from services.notes import NotesService
from subtitles.subs import SubsClient
from store.database import SessionLocal
import os


def get_subs_client() -> SubsClient:
    return SubsClient()


def get_notes_service() -> NotesService:
    return NotesService(strategy=os.getenv('NOTES_SEMANTIC_SEARCH_STRATEGY', default='local'))


# Dependency
def get_db() -> SessionLocal:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
