import logging
import os
import re
import xml
from threading import Lock
from typing import List

import aiohttp
import faiss
import numpy as np
from faiss import Index
from sentence_transformers import SentenceTransformer
from sqlalchemy.orm import Session
from sqlalchemy.sql.expression import func

from crud.notes import get_all, get_note_by_uri
from models.embeddings import EmbeddingComputationRequest, TextReference, EmbeddingComputationResponse
from models.notes import Note as NoteModel
from services.singleton import Singleton
from store.schema.note import Note
from tqdm import tqdm

logger = logging.getLogger(__name__)


class NotesService(metaclass=Singleton):
    model: SentenceTransformer
    lock: Lock = Lock()

    def __init__(self, strategy: str = 'remote'):
        self.index: Index = None
        self.strategy = strategy
        self.embedding_index_to_note_id = []
        models_cache_dir = os.getenv('MODELS_CACHE')
        if self.strategy == 'local':
            self.model = SentenceTransformer('sentence-transformers/LaBSE', cache_folder=models_cache_dir)
        self.cache_loaded = False

    async def search(self, db: Session, q: str = None, offset: int = 0, count: int = 20) -> List[NoteModel]:
        if q:
            q_embeddings: np.ndarray = await self.compute_embeddings(q, strategy=self.strategy, db=db)
            await self.load_index(db=db, force_reload=False)
            similarities_asc, vectors_index = self.index.search(q_embeddings, k=offset + count)
            results_idxs: List[int] = vectors_index[offset:].tolist()[0]
            notes_ids: List[int] = [self.embedding_index_to_note_id[idx] for idx in results_idxs]
            models = db.query(Note).filter(Note.id.in_(notes_ids)) \
                .order_by(func.array_position(notes_ids[::-1], Note.id)) \
                .all()
        else:
            models = get_all(db, 0, 2)
        return models

    def find_note_by_uri(self, note_uri: str, db: Session) -> Note:
        return get_note_by_uri(db, note_uri)

    async def compute_embeddings(self, sentences: str, db: Session, strategy="local") -> np.ndarray:
        if strategy == 'local':
            sentences: List[str] = self._split_sentences(sentences)
            logger.debug("Computing embeddings of %s", sentences)
            embeddings = self.model.encode(sentences).astype(np.float32)
        else:
            embeddings = await self._compute_embeddings_externally(sentences)
        return embeddings

    async def compute_note_embeddings(self, note: NoteModel, db: Session) -> List[float]:
        return self.compute_embeddings(note.valeur, db=db).tolist()

    def _sanitize_line(self, line: str) -> List[str]:
        sanitized: str = ''.join(xml.etree.ElementTree.fromstring(f"<body>{line}</body>").itertext())
        sanitized = re.sub('\.+', '\n', sanitized)
        sanitized = sanitized.replace('#', ' ')
        sanitized = sanitized.strip()
        sanitized = re.sub('#+', '\n', sanitized)
        return sanitized.splitlines()

    def _split_sentences(self, txt: str) -> List[str]:
        sentences: List[str] = txt.splitlines()
        sanitized_sentences = []
        for raw_line in sentences:
            lines = self._sanitize_line(raw_line)
            for line in lines:
                line = line.strip()
                if line:
                    sanitized_sentences.append(line)
        return sanitized_sentences

    async def load_index(self, db: Session, force_reload: bool = False) -> None:
        with self.lock:
            if force_reload or not self.cache_loaded:
                logger.info("Building notes index...")
                logger.info("Loading all text from database")
                notes: List[Note] = get_all(db)
                logger.info("...all texts loaded from database")
                embeddings = []
                embedding_index_to_note_id = []
                commit = False
                nb_notes = 0
                for note in tqdm(notes):
                    try:
                        if note.sentence_embeddings is None:
                            embd = await self.compute_embeddings(note.valeur, db=db, strategy=self.strategy)
                            note.sentence_embeddings = embd
                            db.add(note)
                            commit = True
                        else:
                            embd = note.sentence_embeddings
                        embeddings.extend(embd)
                        embedding_index_to_note_id.extend([note.id] * embd.shape[0])
                        nb_notes += 1
                        if nb_notes % 10 == 0:
                            db.flush()
                    except BaseException as err:
                        logger.error(
                            f"Error while trying to compute embeddings of note {note.id} :\n{note.valeur}\n{err}")
                if commit:
                    db.commit()
                np_embeddings = np.stack(embeddings).astype(np.float32)
                index = faiss.IndexFlatL2(np_embeddings.shape[1])
                index.add(np_embeddings)
                self.index = index
                self.embedding_index_to_note_id = embedding_index_to_note_id
                logger.info(".... index built")
                self.cache_loaded = True

    async def _compute_embeddings_externally(self, text: str) -> np.ndarray:
        async with aiohttp.ClientSession() as session:
            texts = [TextReference(id=0, text=text)]
            request = EmbeddingComputationRequest(texts=texts)
            params = {'strategy': 'local'}
            async with session.post('https://pynotes.jleo.tech/api/embeddings',
                                    params=params,
                                    json=request.dict()) as response:
                answer: EmbeddingComputationResponse = await response.json()
                return np.array(answer['texts'][0]['embeddings']).astype(np.float32)
