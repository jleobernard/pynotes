from typing import List

from sqlalchemy.orm import Session

from services.singleton import Singleton
from models.notes import Note as NoteModel
from crud.notes import get_all, get_note_by_uri
from sentence_transformers import SentenceTransformer

from store.schema.note import Note


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
        embeddings = self.model(sentences)
        print(embeddings)
        return embeddings

    def _split_sentences(self, note: NoteModel) -> List[str]:
        # Todo change
        return note.valeur.splitlines()
