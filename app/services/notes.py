from typing import List, Tuple

from faiss import Index
from sqlalchemy.orm import Session

from models.embeddings import EmbeddingComputationRequest, TextReference, EmbeddingComputationResponse
from services.singleton import Singleton
from models.notes import Note as NoteModel
from crud.notes import get_all, get_note_by_uri, get_notes_valeur
from sentence_transformers import SentenceTransformer

from store.schema.note import Note
import xml
import re
import os
import logging
import numpy as np
import faiss
import aiohttp

logger = logging.getLogger(__name__)

SENTENCE_EMBEDDING_DIMENSION = 768


class NotesService(metaclass=Singleton):
    model: SentenceTransformer

    def __init__(self):
        self.index: Index = None
        models_cache_dir = os.getenv('MODELS_CACHE')
        self.model = SentenceTransformer('sentence-transformers/LaBSE', cache_folder=models_cache_dir)

    def search(self, db: Session) -> List[NoteModel]:
        return get_all(db, 0, 2)

    def find_note_by_uri(self, note_uri: str, db: Session) -> Note:
        return get_note_by_uri(db, note_uri)

    async def compute_embeddings(self, sentences: str, strategy="local") -> np.ndarray:
        if strategy == 'local':
            sentences: List[str] = self._split_sentences(sentences)
            logger.debug("Computing embeddings of %s", sentences)
            embeddings = self.model.encode(sentences)
        else:
            embeddings = self._compute_embeddings_externally(sentences)
        return embeddings

    async def compute_note_embeddings(self, note: NoteModel) -> List[float]:
        return self.compute_embeddings(note.valeur).tolist()

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

    async def load_index(self, db: Session, strategy="remote") -> None:
        logger.info("Building notes index")
        logger.info("Loading all text from database")
        values: List[Tuple[int, str]] = get_notes_valeur(db)
        embeddings = [self.compute_embeddings(valeur, strategy) for (_, valeur) in values]
        index = faiss.IndexFlatL2(SENTENCE_EMBEDDING_DIMENSION)
        index.add(embeddings)
        self.index = index

    async def _compute_embeddings_externally(self, text: str) -> np.ndarray:
        async with aiohttp.ClientSession() as session:
            texts = [TextReference(id=0, text=text)]
            request = EmbeddingComputationRequest(texts=texts)
            params = {'strategy': 'local'}
            async with session.post('https://pynotes.jleo.tech/api/embeddings',
                                    params=params,
                                    json=request) as response:
                answer: EmbeddingComputationResponse = await response.json()
                return np.array(answer.texts[0].embeddings)
