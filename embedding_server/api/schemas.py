from typing import List, Optional

from pydantic import BaseModel, Field


class EmbeddingInput(BaseModel):
    text: Optional[str] = None
    image: Optional[str] = None
    image_base64: Optional[str] = None


class EmbeddingRequest(BaseModel):
    inputs: List[EmbeddingInput] = Field(..., min_length=1, description="List of text/image inputs")


class EmbeddingData(BaseModel):
    index: int
    embedding: List[float]


class EmbeddingResponse(BaseModel):
    object: str = "list"
    data: List[EmbeddingData]
    model: str
    dim: int
    count: int
