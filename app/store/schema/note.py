from sqlalchemy import Boolean, Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from ..database import Base


class Note(Base):
    __tablename__ = "note"

    id = Column(Integer, primary_key=True, index=True)
    uri = Column(String, unique=True, index=True)
    valeur = Column(String, unique=False, index=False)
