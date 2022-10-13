from typing import List

from pydantic import BaseModel


class TextReference(BaseModel):
    id: int
    text: str


class TextWithEmbeddings(BaseModel):
    id: int
    embeddings: List[List[float]]


class EmbeddingComputationRequest(BaseModel):
    texts: List[TextReference]


class EmbeddingComputationResponse(BaseModel):
    texts: List[TextWithEmbeddings]
