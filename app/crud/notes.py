from typing import List, Tuple

import numpy as np
from sqlalchemy.orm import Session

from store.schema.noteentity import NoteEntity


def delete_all_notes(db: Session):
    return db.query(NoteEntity).delete()


def get_note_by_uri(db: Session, note_uri: str) -> NoteEntity:
    return db.query(NoteEntity).filter(NoteEntity.uri == note_uri).first()


def delete_note_by_uri(note_uri: str, db: Session):
    note = get_note_by_uri(db, note_uri)
    if note:
        db.delete(note)


def get_all(db: Session, offset: int = 0, count: int = None) -> List[NoteEntity]:
    q = db.query(NoteEntity).offset(offset)
    if count is not None:
        q = q.limit(count)
    return q.all()


def get_notes_valeur(db: Session) -> List[Tuple[int, np.ndarray]]:
    return db.query(NoteEntity).order_by(NoteEntity.id.asc()).value(['id', 'sentence_embeddings'])
