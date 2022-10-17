from fastapi import Depends

from crud.notes_reference import NotesReferenceDAO
from services.notes import NotesService
from store.database import SessionLocal


def get_notes_reference_dao() -> NotesReferenceDAO:
    return NotesReferenceDAO()


def get_notes_service(notes_reference_dao: NotesReferenceDAO = Depends(get_notes_reference_dao)) -> NotesService:
    return NotesService(notes_reference_dao=notes_reference_dao)


# Dependency
def get_db() -> SessionLocal:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
