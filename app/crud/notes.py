from typing import List, Tuple

from sqlalchemy.orm import Session

from store.schema.note import Note


def get_note_by_uri(db: Session, note_uri: str) -> Note:
    return db.query(Note).filter(Note.uri == note_uri).first()


def get_all(db: Session, offset: int = 0, count: int = 0) -> List[Note]:
    return db.query(Note).offset(offset).limit(count).all()


def get_notes_valeur(db: Session) -> List[Tuple[int, str]]:
    return db.query(Note).order_by(Note.id.asc()).value(['id', 'valeur'])
