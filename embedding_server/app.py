import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from api.routes import router
from core.model import load_model

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    load_model()
    logger.info("Service ready.")
    yield


app = FastAPI(title="Qwen3-VL-Embedding Service", lifespan=lifespan)
app.include_router(router)


if __name__ == "__main__":
    import uvicorn

    from core.config import settings

    uvicorn.run(app, host=settings.host, port=settings.port)
