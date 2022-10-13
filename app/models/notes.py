from pydantic import BaseModel


class NoteBase(BaseModel):
    uri: str
    valeur: str

    class Config:
        orm_mode = True


class Note(NoteBase):
    id: int

    class Config:
        orm_mode = True
