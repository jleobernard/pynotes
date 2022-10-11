from fastapi import APIRouter
from fastapi import Depends
from sqlalchemy.orm import Session

from crud.users import get_user_by_email
from dependencies import get_db
from models.users import User
from models.users import User as UserModel

router = APIRouter(
    tags=['users']
)


@router.get("/user", response_model=UserModel)
async def current_user(db: Session = Depends(get_db)) -> User:
    return get_user_by_email(db, user_email='jleobernard@gmail.com')

@router.get("/authentication:status")
async def authentication_status():
    return [{"username": "Rick"}, {"username": "Morty"}]

@router.get("/token:refresh")
async def token_refresh():
    return [{"username": "Rick"}, {"username": "Morty"}]