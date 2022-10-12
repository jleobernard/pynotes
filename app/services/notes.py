from typing import List

from sqlalchemy.orm import Session

from services.singleton import Singleton
from models.notes import Note as NoteModel
from crud.notes import get_all, get_note_by_uri
from sentence_transformers import SentenceTransformer

from store.schema.note import Note
import xml
import re


class NotesService(metaclass=Singleton):
    model: SentenceTransformer

    def __init__(self):
        self.model = SentenceTransformer('sentence-transformers/LaBSE')

    def search(self, db: Session) -> List[NoteModel]:
        return get_all(db, 0, 2)

    def find_note_by_uri(self, note_uri: str, db: Session) -> Note:
        return get_note_by_uri(db, note_uri)

    def compute_embeddings(self, note: NoteModel):
        sentences: List[str] = self._split_sentences(note)
        print(sentences)
        embeddings = self.model.encode(sentences)
        print(embeddings.shape)
        return embeddings.tolist()

    def _sanitize_line(self, line: str) -> List[str]:
        sanitized: str = ''.join(xml.etree.ElementTree.fromstring(f"<body>{line}</body>").itertext())
        sanitized = re.sub('\.+', '\n', sanitized)
        sanitized = sanitized.replace('#', ' ')
        sanitized = sanitized.strip()
        sanitized = re.sub('#+', '\n', sanitized)
        return sanitized.splitlines()

    def _split_sentences(self, note: NoteModel) -> List[str]:
        sentences: List[str] = note.valeur.splitlines()
        sanitized_sentences = []
        for raw_line in sentences:
            lines = self._sanitize_line(raw_line)
            for line in lines:
                line = line.strip()
                if line:
                    sanitized_sentences.append(line)
        return sanitized_sentences

