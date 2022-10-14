import logging
from typing import List

from fastapi import APIRouter, Request
from fastapi import Depends
from sqlalchemy.orm import Session
from starlette.background import BackgroundTasks

from dependencies import get_db, get_notes_service
from models.embeddings import EmbeddingComputationRequest, EmbeddingComputationResponse, TextWithEmbeddings
from models.notes import Note as NoteModel, NoteBase
from services.notes import NotesService
from store.schema.note import Note

router = APIRouter(
    tags=['notes']
)

logger = logging.getLogger(__name__)

@router.get("/notes:reload-index")
async def reload_index(background_tasks: BackgroundTasks,
                       notes_service: NotesService = Depends(get_notes_service),
                       db: Session = Depends(get_db)):
    background_tasks.add_task(notes_service.load_index, force_reload=True, db=db)
    return {"ok": True, "message": "Task running"}


@router.get("/notes/{note_uri}", response_model=NoteBase)
async def find_note_by_uri(note_uri: str,
                           notes_service: NotesService = Depends(get_notes_service),
                           db: Session = Depends(get_db)) -> List[NoteModel]:
    return notes_service.find_note_by_uri(note_uri, db)


@router.get("/notes", response_model=List[NoteBase])
async def search_notes(q: str | None,
                       offset: int = 0, count: int = 20,
                       notes_service: NotesService = Depends(get_notes_service),
                       db: Session = Depends(get_db)):
    return await notes_service.search(db=db, q=q, offset=offset, count=count)


@router.get("/notes/{note_uri}/embeddings")
async def get_note_embedding(note_uri: str,
                             strategy: str = 'local',
                             notes_service: NotesService = Depends(get_notes_service),
                             db: Session = Depends(get_db)) -> List[NoteModel]:
    note: Note = notes_service.find_note_by_uri(note_uri, db)
    return notes_service.compute_note_embeddings(note, db=db)


@router.post("/embeddings", response_model=EmbeddingComputationResponse)
async def get_note_embedding(request: EmbeddingComputationRequest,
                             strategy: str = 'local',
                             db: Session = Depends(get_db),
                             notes_service: NotesService = Depends(get_notes_service)) -> EmbeddingComputationResponse:
    embeddings: List[TextWithEmbeddings] = []
    for text in request.texts:
        embedding = await notes_service.compute_embeddings(text.text, strategy=strategy, db=db)
        embeddings.append(TextWithEmbeddings(id=text.id, embeddings=embedding.tolist()))
    return EmbeddingComputationResponse(texts=embeddings)


@router.post('/notes/notifications')
def receive_messages_handler(request: Request):
    # Verify that the request originates from the application.
    body = request.json()
    print(f"Received from GCP PUB/SUB : {body}")
    return {"success": True, "message": "OK"}
