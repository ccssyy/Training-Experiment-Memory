#!/usr/bin/env bash
# 启动独立的 Qwen3-VL-Embedding 版式向量服务（不依赖任何业务配置系统）。
# 用法：MODEL_PATH=/path/to/model bash run.sh   （其余参数见下方默认值，可用环境变量覆盖）
set -euo pipefail

DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$DIR"

: "${MODEL_PATH:?请设置 MODEL_PATH（模型目录，部署时 export 真实路径）}"
export DTYPE="${DTYPE:-bfloat16}"
export HOST="${HOST:-0.0.0.0}"
export PORT="${PORT:-9031}"
export GPU_IDS="${GPU_IDS:-0}"
export GPU_MEM_UTIL="${GPU_MEM_UTIL:-0.1}"
export MAX_MODEL_LEN="${MAX_MODEL_LEN:-4096}"
export MAX_BATCH_SIZE="${MAX_BATCH_SIZE:-500}"
export INFERENCE_CHUNK_SIZE="${INFERENCE_CHUNK_SIZE:-10}"

echo "启动 embedding 服务：model=$MODEL_PATH port=$PORT gpu=$GPU_IDS"
exec python3 app.py
