"""环境变量驱动的配置。部署时通过 run.sh 或 export 覆盖默认值。"""
import os
from dataclasses import dataclass


@dataclass
class Settings:
    model_path: str = os.environ.get("MODEL_PATH", "")
    host: str = os.environ.get("HOST", "0.0.0.0")
    port: int = int(os.environ.get("PORT", "9033"))
    gpu_ids: str = os.environ.get("GPU_IDS", "1")
    # bge-m3 dense 编码的 query 指令前缀（空串 = 裸编码，字段语义匹配用）
    query_instruction: str = os.environ.get("QUERY_INSTRUCTION", "")
    max_length: int = int(os.environ.get("MAX_LENGTH", "512"))
    max_batch_size: int = int(os.environ.get("MAX_BATCH_SIZE", "256"))


settings = Settings()
