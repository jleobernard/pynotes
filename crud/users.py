from typing import List
from sqlalchemy.orm import Session
from store.schema.user import User


def get_user_by_uri(db: Session, user_uri: int) -> User:
    return db.query(User).filter(User.uri == user_uri).first()

def get_user_by_email(db: Session, user_email: int) -> User:
    return db.query(User).filter(User.email == user_email).first()

def get_users(db: Session, skip: int = 0, limit: int = 100) -> List[User]:
    return db.query(User).offset(skip).limit(limit).all()