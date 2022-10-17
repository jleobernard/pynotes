import numpy as np
from sqlalchemy import Column, String, Integer
from sqlalchemy import TypeDecorator, types

from utils.constants import SENTENCE_EMBEDDING_DIMENSION
from ..database import Base


class SentenceEmbedding(TypeDecorator):
    impl = types.LargeBinary
    cache_ok = True

    def process_bind_param(self, value, dialect):
        return None if value is None else value.tobytes()

    def process_result_value(self, value, dialect):
        return None if value is None else np.frombuffer(value, dtype=np.float32)\
            .reshape((-1, SENTENCE_EMBEDDING_DIMENSION))


class NoteEntity(Base):
    __tablename__ = "note"

    id = Column(Integer, primary_key=True, index=True)
    uri = Column(String, unique=True, index=True)
    sentence_embeddings = Column(SentenceEmbedding, unique=False, index=False)
