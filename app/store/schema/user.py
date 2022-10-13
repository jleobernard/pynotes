from sqlalchemy import Column, Integer, String

from ..database import Base


class User(Base):
    __tablename__ = "user_account"

    id = Column(Integer, primary_key=True, index=True)
    uri = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    password = Column(String)
