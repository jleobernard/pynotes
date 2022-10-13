from typing import List, Tuple

import numpy as np
from sqlalchemy.orm import Session

from store.schema.note import Note


def get_note_by_uri(db: Session, note_uri: str) -> Note:
    return db.query(Note).filter(Note.uri == note_uri).first()


def get_all(db: Session, offset: int = 0, count: int = None) -> List[Note]:
    q = db.query(Note).offset(offset)
    if count is not None:
        q = q.limit(count)
    return q.all()


def get_notes_valeur(db: Session) -> List[Tuple[int, np.ndarray]]:
    return db.query(Note).order_by(Note.id.asc()).value(['id', 'sentence_embeddings'])
