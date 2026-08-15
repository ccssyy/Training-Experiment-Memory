import asyncio
import logging
import os

from fastapi import APIRouter, HTTPException

from api.schemas import EmbeddingData, EmbeddingRequest, EmbeddingResponse
from core import model
from core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/v1/embeddings", response_model=EmbeddingResponse)
async def embeddings(request: EmbeddingRequest):
    if model.model is None:
        raise HTTPException(status_code=503, detail="Model not loaded")
    if len(request.inputs) > settings.max_batch_size:
        raise HTTPException(
            status_code=400,
            detail=f"Batch size {len(request.inputs)} exceeds limit {settings.max_batch_size}",
        )
    texts = [inp.text for inp in request.inputs]
    try:
        loop = asyncio.get_event_loop()
        vectors = await loop.run_in_executor(None, model.encode, texts, request.query_mode)
    except Exception as exc:  # noqa: BLE001
        logger.exception("Embedding request failed: count=%s error=%s", len(texts), exc)
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    return EmbeddingResponse(
        data=[EmbeddingData(index=i, embedding=emb) for i, emb in enumerate(vectors)],
        model=os.path.basename(settings.model_path),
        dim=len(vectors[0]) if vectors else 0,
        count=len(vectors),
    )


@router.get("/health")
async def health():
    return model.health_status()
