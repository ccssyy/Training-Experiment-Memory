from typing import List, Optional

from pydantic import BaseModel, Field


class EmbeddingInput(BaseModel):
    text: Optional[str] = None


class EmbeddingRequest(BaseModel):
    inputs: List[EmbeddingInput] = Field(..., min_length=1, description="List of text inputs")
    query_mode: bool = Field(False, description="是否作为 query（加指令前缀）")


class EmbeddingData(BaseModel):
    index: int
    embedding: List[float]


class EmbeddingResponse(BaseModel):
    object: str = "list"
    data: List[EmbeddingData]
    model: str
    dim: int
    count: int
