from typing import List

from fastapi import APIRouter
from fastapi import Depends
from sqlalchemy.orm import Session
from starlette.background import BackgroundTasks

from crud.users import get_user_by_email
from dependencies import get_db, get_notes_service
from models.embeddings import EmbeddingComputationRequest, EmbeddingComputationResponse, TextWithEmbeddings
from models.notes import Note as NoteModel, NoteBase
from services.notes import NotesService
from store.schema.note import Note

router = APIRouter(
    tags=['notes']
)


@router.get("/notes:reload-index", response_model=NoteBase)
async def reload_index(background_tasks: BackgroundTasks,
                       notes_service: NotesService = Depends(get_notes_service),
                       strategy: str = "local",
                       db: Session = Depends(get_db)):
    background_tasks.add_task(notes_service.load_index, db=db, strategy=strategy)
    return {"ok": True, "message": "Task running"}


@router.get("/notes/{note_uri}", response_model=NoteBase)
async def find_note_by_uri(note_uri: str,
                           notes_service: NotesService = Depends(get_notes_service),
                           db: Session = Depends(get_db)) -> List[NoteModel]:
    return notes_service.find_note_by_uri(note_uri, db)


@router.get("/notes", response_model=List[NoteModel])
async def search_notes(q: str | None,
                       offset: int = 0, count: int = 20,
                       notes_service: NotesService = Depends(get_notes_service),
                       db: Session = Depends(get_db)) -> List[NoteModel]:
    return get_user_by_email(db, user_email='jleobernard@gmail.com')


@router.get("/notes/{note_uri}/embeddings")
async def get_note_embedding(note_uri: str,
                             notes_service: NotesService = Depends(get_notes_service),
                             db: Session = Depends(get_db)) -> List[NoteModel]:
    note: Note = notes_service.find_note_by_uri(note_uri, db)
    return notes_service.compute_note_embeddings(note)


@router.post("/embeddings", response_model=EmbeddingComputationResponse)
async def get_note_embedding(request: EmbeddingComputationRequest,
                             strategy: str = 'local',
                             notes_service: NotesService = Depends(get_notes_service)) -> EmbeddingComputationResponse:
    embeddings: List[TextWithEmbeddings] = []
    for text in request.texts:
        embedding = await notes_service.compute_embeddings(text.text, strategy=strategy)
        embeddings.append(TextWithEmbeddings(id=text.id, embeddings=embedding.tolist()))
    return EmbeddingComputationResponse(texts=embeddings)
