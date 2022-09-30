from fastapi import APIRouter
from models.users import User

from subtitles.subs import SubsClient
from fastapi import Depends
from dependencies import get_db, get_subs_client
from sqlalchemy.orm import Session
from crud.users import get_user_by_email
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