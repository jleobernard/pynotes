from typing import List

from sqlalchemy.orm import Session

from app.store.schema.note import Note


def get_note_by_uri(db: Session, note_uri: str) -> Note:
    return db.query(Note).filter(Note.uri == note_uri).first()


def get_all(db: Session, offset: int = 0, count: int = 0) -> List[Note]:
    return db.query(Note).offset(offset).limit(count).all()
