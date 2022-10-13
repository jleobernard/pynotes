from sqlalchemy import Column, Integer, String
from sqlalchemy import TypeDecorator, types

from utils.constants import SENTENCE_EMBEDDING_DIMENSION
from ..database import Base

import numpy as np


class SentenceEmbedding(TypeDecorator):
    impl = types.LargeBinary
    cache_ok = True

    def process_bind_param(self, value, dialect):
        return None if value is None else value.tobytes()

    def process_result_value(self, value, dialect):
        return None if value is None else np.frombuffer(value, dtype=np.float).reshape((-1, SENTENCE_EMBEDDING_DIMENSION))


class Note(Base):
    __tablename__ = "note"

    id = Column(Integer, primary_key=True, index=True)
    uri = Column(String, unique=True, index=True)
    valeur = Column(String, unique=False, index=False)
    sentence_embeddings = Column(SentenceEmbedding, unique=False, index=False)
