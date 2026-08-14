import base64
import logging
import os
from io import BytesIO
from typing import Any, Dict, List

from PIL import Image
from vllm import EngineArgs, LLM
from vllm.multimodal.utils import fetch_image

from core.config import settings

logger = logging.getLogger(__name__)

llm: LLM | None = None


def load_model() -> LLM:
    global llm
    if not settings.model_path:
        raise RuntimeError("MODEL_PATH 未设置，请通过环境变量或 run.sh 指定模型目录")
    logger.info("Loading model from %s ...", settings.model_path)
    os.environ["CUDA_VISIBLE_DEVICES"] = settings.gpu_ids
    logger.info("Using GPUs: %s", settings.gpu_ids)

    engine_args = EngineArgs(
        model=settings.model_path,
        runner="pooling",
        dtype=settings.dtype,
        trust_remote_code=True,
        gpu_memory_utilization=settings.gpu_memory_utilization,
        max_model_len=settings.max_model_len,
    )
    llm = LLM(**vars(engine_args))
    logger.info("Model loaded.")
    return llm


def health_status() -> dict:
    if llm is None:
        return {"status": "loading"}
    try:
        engine_core = getattr(getattr(llm, "llm_engine", None), "engine_core", None)
        if engine_core is not None and hasattr(engine_core, "ensure_alive"):
            engine_core.ensure_alive()
        return {"status": "ok"}
    except Exception as exc:  # noqa: BLE001
        return {"status": "failed", "error": str(exc) or exc.__class__.__name__}


def _build_conversation(text: str | None, image: str | None, has_image_base64: bool = False) -> List[Dict]:
    content: List[Dict] = []
    if image or has_image_base64:
        if image and image.startswith(("http", "https", "oss")):
            image_ref = image
        elif image:
            image_ref = "file://" + os.path.abspath(image)
        else:
            image_ref = "base64://image"
        content.append({"type": "image", "image": image_ref})
    if text:
        content.append({"type": "text", "text": text})
    if not content:
        content.append({"type": "text", "text": ""})
    return [
        {"role": "system", "content": [{"type": "text", "text": settings.instruction}]},
        {"role": "user", "content": content},
    ]


def _load_image(image: str | None, image_base64: str | None = None):
    if image_base64:
        data = image_base64.split(",", 1)[1] if image_base64.startswith("data:") and "," in image_base64 else image_base64
        img = Image.open(BytesIO(base64.b64decode(data)))
    elif image and image.startswith(("http", "https", "oss")):
        img = fetch_image(image)
    elif image:
        img = Image.open(os.path.abspath(image))
    else:
        raise ValueError("image or image_base64 is required")
    return img.convert("RGB")


def build_vllm_input(text: str | None, image: str | None, image_base64: str | None = None) -> Dict[str, Any]:
    conversation = _build_conversation(text, image, bool(image_base64))
    prompt_text = llm.llm_engine.tokenizer.apply_chat_template(
        conversation, tokenize=False, add_generation_prompt=True
    )
    multi_modal_data = None
    if image or image_base64:
        multi_modal_data = {"image": _load_image(image, image_base64)}
    return {"prompt": prompt_text, "multi_modal_data": multi_modal_data}


def embed(inputs: List[Dict[str, Any]]) -> List[List[float]]:
    if llm is None:
        raise RuntimeError("Model not loaded")
    chunk_size = max(1, settings.inference_chunk_size)
    vectors: List[List[float]] = []
    for start in range(0, len(inputs), chunk_size):
        chunk = inputs[start : start + chunk_size]
        logger.info("Embedding inference chunk: %s-%s / %s", start + 1, start + len(chunk), len(inputs))
        outputs = llm.embed(chunk, use_tqdm=False)
        vectors.extend(out.outputs.embedding for out in outputs)
    return vectors
