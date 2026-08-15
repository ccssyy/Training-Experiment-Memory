#!/usr/bin/env bash
# bge-m3 文本 embedding 服务启动脚本（纯环境变量配置）
set -e

: "${MODEL_PATH:?请设置 MODEL_PATH，例如 MODEL_PATH=/data/LLM_model/bge-m3}"
export PORT="${PORT:-9033}"
export GPU_IDS="${GPU_IDS:-1}"
export QUERY_INSTRUCTION="${QUERY_INSTRUCTION:-}"
export MAX_LENGTH="${MAX_LENGTH:-512}"
export MAX_BATCH_SIZE="${MAX_BATCH_SIZE:-256}"

exec python app.py
