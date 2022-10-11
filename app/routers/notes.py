from typing import List

from fastapi import APIRouter
from fastapi import Depends
from sqlalchemy.orm import Session

from app.crud.users import get_user_by_email
from app.dependencies import get_db, get_notes_service
from app.models.notes import Note as NoteModel
from app.services.notes import NotesService
from app.store.schema.note import Note

router = APIRouter(
    tags=['notes']
)


@router.get("/notes", response_model=List[NoteModel])
async def search_notes(q: str | None,
                       offset: int = 0, count: int = 20, db: Session = Depends(get_db)) -> List[NoteModel]:
    return get_user_by_email(db, user_email='jleobernard@gmail.com')


@router.get("/notes/{note_uri}/embeddings")
async def get_note_embedding(note_uri: str,
                             notes_service: NotesService = Depends(get_notes_service),
                             db: Session = Depends(get_db)) -> List[NoteModel]:
    note: Note = notes_service.find_note_by_uri(note_uri, db)
    return notes_service.compute_embeddings(note)
