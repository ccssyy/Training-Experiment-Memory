import asyncio
import logging

from fastapi import APIRouter, HTTPException

from api.schemas import EmbeddingData, EmbeddingRequest, EmbeddingResponse
from core import model
from core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/v1/embeddings", response_model=EmbeddingResponse)
async def embeddings(request: EmbeddingRequest):
    if model.llm is None:
        raise HTTPException(status_code=503, detail="Model not loaded")
    health = model.health_status()
    if health.get("status") != "ok":
        raise HTTPException(status_code=503, detail=health)

    if len(request.inputs) > settings.max_batch_size:
        raise HTTPException(
            status_code=400,
            detail=f"Batch size {len(request.inputs)} exceeds limit {settings.max_batch_size}",
        )

    try:
        vllm_inputs = [model.build_vllm_input(inp.text, inp.image, inp.image_base64) for inp in request.inputs]
        loop = asyncio.get_event_loop()
        vectors = await loop.run_in_executor(None, model.embed, vllm_inputs)
    except Exception as exc:  # noqa: BLE001
        logger.exception("Embedding request failed: count=%s error=%s", len(request.inputs), exc)
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    if len(vectors) != len(request.inputs):
        raise HTTPException(
            status_code=500,
            detail=f"Embedding vector count mismatch: requested {len(request.inputs)}, got {len(vectors)}",
        )

    return EmbeddingResponse(
        data=[EmbeddingData(index=i, embedding=emb) for i, emb in enumerate(vectors)],
        model=settings.model_path.split("/")[-1],
        dim=len(vectors[0]) if vectors else 0,
        count=len(vectors),
    )


@router.get("/health")
async def health():
    return model.health_status()
