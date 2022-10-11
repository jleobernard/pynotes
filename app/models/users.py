from pydantic import BaseModel

class UserBase(BaseModel):
    uri: str
    email: str

class User(UserBase):
    id: int

    class Config:
        orm_mode = True