"""bge-m3 dense embedding：transformers 加载 + [CLS] pooling + L2 归一化。"""
import logging
import os

import torch
from transformers import AutoModel, AutoTokenizer

from core.config import settings

logger = logging.getLogger(__name__)

model = None
tokenizer = None
_device = "cpu"


def load_model():
    global model, tokenizer, _device
    if not settings.model_path:
        raise RuntimeError("MODEL_PATH 未设置，请通过环境变量或 run.sh 指定模型目录")
    logger.info("Loading bge-m3 from %s ...", settings.model_path)
    tokenizer = AutoTokenizer.from_pretrained(settings.model_path)
    model = AutoModel.from_pretrained(settings.model_path)
    model.eval()
    os.environ["CUDA_VISIBLE_DEVICES"] = settings.gpu_ids
    if torch.cuda.is_available():
        model = model.cuda()
        _device = "cuda"
        logger.info("Using GPU: %s", settings.gpu_ids)
    else:
        _device = "cpu"
        logger.info("Using CPU")
    logger.info("Model loaded.")


def health_status() -> dict:
    if model is None:
        return {"status": "loading"}
    return {"status": "ok", "device": _device}


def _to_device(batch):
    if _device == "cuda":
        return {k: v.cuda() for k, v in batch.items()}
    return batch


def encode(texts: list[str], query_mode: bool = False) -> list[list[float]]:
    """文本 → 1024 维 dense 向量（[CLS] pooling + L2 归一化）。

    query_mode=True 时给 query 加指令前缀（settings.query_instruction，空则不加）。
    """
    if model is None:
        raise RuntimeError("Model not loaded")
    prepared = []
    for t in texts:
        t = t or ""
        if query_mode and settings.query_instruction:
            t = settings.query_instruction + t
        prepared.append(t)
    batch = tokenizer(
        prepared, return_tensors="pt", padding=True, truncation=True, max_length=settings.max_length
    )
    batch = _to_device(batch)
    with torch.no_grad():
        outputs = model(**batch)
    cls = outputs.last_hidden_state[:, 0, :]  # [CLS]
    cls = torch.nn.functional.normalize(cls, p=2, dim=1)
    return cls.cpu().tolist()
