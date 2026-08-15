"""环境变量驱动的配置。部署时通过 run.sh 或 export 覆盖默认值。"""
import os
from dataclasses import dataclass


@dataclass
class Settings:
    model_path: str = os.environ.get("MODEL_PATH", "")
    dtype: str = os.environ.get("DTYPE", "bfloat16")
    host: str = os.environ.get("HOST", "0.0.0.0")
    port: int = int(os.environ.get("PORT", "9031"))
    gpu_ids: str = os.environ.get("GPU_IDS", "0")
    instruction: str = os.environ.get(
        "INSTRUCTION",
        "Represent the document layout structure only, ignoring text content and specific details.",
    )
    gpu_memory_utilization: float = float(os.environ.get("GPU_MEM_UTIL", "0.1"))
    max_model_len: int = int(os.environ.get("MAX_MODEL_LEN", "4096"))
    max_batch_size: int = int(os.environ.get("MAX_BATCH_SIZE", "500"))
    inference_chunk_size: int = int(os.environ.get("INFERENCE_CHUNK_SIZE", "10"))


settings = Settings()
