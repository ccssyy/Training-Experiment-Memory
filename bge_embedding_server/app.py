"""bge-m3 文本 embedding 服务（字段语义向量）。

FastAPI + transformers，提供纯文本 dense embedding（[CLS] pooling + L2 归一化）。
用法：
    MODEL_PATH=/path/to/bge-m3 PORT=9033 GPU_IDS=1 python app.py
"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from api.routes import router
from core import model
from core.config import settings

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    model.load_model()
    yield


app = FastAPI(title="bge-m3 embedding", lifespan=lifespan)
app.include_router(router)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host=settings.host, port=settings.port)
