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
from sqlalchemy.orm import Session, load_only
from sqlalchemy.sql.expression import func
from tqdm import tqdm

from crud.notes import get_all, get_note_by_uri, delete_note_by_uri, delete_all_notes
from crud.notes_reference import NotesReferenceDAO
from models.embeddings import EmbeddingComputationRequest, TextReference, EmbeddingComputationResponse
from models.notes import Note as NoteModel, NoteReferential
from services.singleton import Singleton
from store.schema.noteentity import NoteEntity

logger = logging.getLogger(__name__)


class NotesService(metaclass=Singleton):
    model: SentenceTransformer
    lock: Lock = Lock()

    def __init__(self, notes_reference_dao: NotesReferenceDAO):
        self.index: Index = None
        self.embedding_index_to_note_id = []
        models_cache_dir = os.getenv('MODELS_CACHE')
        self.model = SentenceTransformer('sentence-transformers/LaBSE', cache_folder=models_cache_dir)
        self.cache_loaded = False
        self.notes_reference_dao = notes_reference_dao

    async def search(self, db: Session, q: str = None, offset: int = 0, count: int = 20) -> List[NoteModel]:
        if q:
            q_embeddings: np.ndarray = await self.compute_embeddings(q)
            await self.load_index(db=db, force_reload=False)
            similarities_asc, vectors_index = self.index.search(q_embeddings, k=offset + count)
            results_idxs: List[int] = vectors_index[offset:].tolist()[0]
            notes_ids: List[int] = [self.embedding_index_to_note_id[idx] for idx in results_idxs]
            models = db.query(NoteEntity)\
                .options(load_only(NoteEntity.uri))\
                .filter(NoteEntity.id.in_(notes_ids)) \
                .order_by(func.array_position(notes_ids, NoteEntity.id)) \
                .all()
        else:
            models = get_all(db, 0, 2)
        return models

    def find_note_by_uri(self, note_uri: str, db: Session) -> NoteEntity:
        return get_note_by_uri(db, note_uri)

    async def compute_embeddings(self, sentences: str) -> np.ndarray:
        sentences: List[str] = self._split_sentences(sentences)
        logger.debug("Computing embeddings of %s", sentences)
        embeddings = self.model.encode(sentences).astype(np.float32)
        return embeddings

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
        force_rerun: bool = False
        with self.lock:
            logger.info("Building notes index...")
            if force_reload:
                await self._populate_db_from_remote_service(db)
            if force_reload or not self.cache_loaded:
                logger.info("Loading all text from database")
                notes: List[NoteEntity] = get_all(db)
                logger.info("...all texts loaded from database")
                if not force_reload and len(notes) == 0:
                    logger.info("Seems like it is the first run so we will load all notes")
                    force_rerun = True
                else:
                    embeddings = []
                    embedding_index_to_note_id = []
                    nb_notes = 0
                    for note in tqdm(notes):
                        embd = note.sentence_embeddings
                        embeddings.extend(embd)
                        embedding_index_to_note_id.extend([note.id] * embd.shape[0])
                        nb_notes += 1
                        if nb_notes % 10 == 0:
                            db.flush()
                    np_embeddings = np.stack(embeddings).astype(np.float32)
                    index = faiss.IndexFlatL2(np_embeddings.shape[1])
                    index.add(np_embeddings)
                    self.index = index
                    self.embedding_index_to_note_id = embedding_index_to_note_id
                    logger.info(".... index built")
                    self.cache_loaded = True
        if force_rerun:
            await self.load_index(db=db, force_reload=True)

    async def _compute_embeddings_externally(self, text: str) -> np.ndarray:
        async with aiohttp.ClientSession() as session:
            texts = [TextReference(id=0, text=text)]
            request = EmbeddingComputationRequest(texts=texts)
            async with session.post('https://pynotes.jleo.tech/api/embeddings',
                                    json=request.dict()) as response:
                answer: dict = await response.json()
                return np.array(answer['texts'][0]['embeddings']).astype(np.float32)

    async def handle_pubsub_message(self, payload: dict, db: Session):
        message_type: str = payload.get('type', '').lower()
        note_uri: str = payload.get('uri', '')
        match message_type:
            case 'upsert':
                await self.upsert_note_embedding(note_uri, db=db)
            case 'deletion':
                await self.delete_note_embedding(note_uri, db=db)
            case _:
                logger.warning(f"Could not handle pubsub message {payload}")

    async def delete_note_embedding(self, note_uri: str, db: Session):
        await self.remove_note_embeddings(note_uri, db)
        delete_note_by_uri(note_uri, db)
        db.commit()

    async def upsert_note_embedding(self, note_uri: str, db: Session):
        ref_note: NoteReferential = await self.notes_reference_dao.fetch_note_by_uri(note_uri=note_uri)
        note: NoteEntity = self.find_note_by_uri(note_uri=note_uri, db=db)
        if note:
            note.sentence_embeddings = None
        else:
            note = NoteEntity()
            note.uri = note_uri
            db.add(note)
        embeddings: np.ndarray = await self.compute_embeddings(sentences=ref_note.valeur)
        note.sentence_embeddings = embeddings
        db.commit()
        await self.load_index(db=db, force_reload=False)
        with self.lock:
            self.index.add(embeddings)
            self.embedding_index_to_note_id.extend([note.id] * embeddings.shape[0])

    async def remove_note_embeddings(self, note_uri: str, db: Session):
        await self.load_index(db=db, force_reload=False)
        with self.lock:
            note = get_note_by_uri(db=db, note_uri=note_uri)
            note_id = note.id
            if note:
                embedding_index_to_note_id = []
                indices_to_delete: List[int] = []
                for idx, rel in enumerate(self.embedding_index_to_note_id):
                    if rel == note_id:
                        indices_to_delete.append(idx)
                    else:
                        embedding_index_to_note_id.append(rel)
                self.index.remove_ids(indices_to_delete)
                self.embedding_index_to_note_id = embedding_index_to_note_id

    async def _populate_db_from_remote_service(self, db: Session):
        delete_all_notes(db)
        count, offset = 20, 0
        while True:
            try:
                notes = await self.notes_reference_dao.fetch_notes(count=count, offset=offset)
                if len(notes) > 0:
                    for note in notes:
                        try:
                            embd = await self.compute_embeddings(note.valeur)
                            note_entity = NoteEntity(uri=note.uri, sentence_embeddings=embd)
                            db.add(note_entity)
                        except BaseException as err:
                            logger.error(f"Error while computing embeddings of :\n"
                                         f"---\n"
                                         f"{note.uri} = {note.valeur}"
                                         f"---\n"
                                         f"{err}")
                    offset += len(notes)
                else:
                    break
            except BaseException as err:
                logger.error(f"Error while fetching notes at offset {offset}\n{err}")
                break
        db.commit()
