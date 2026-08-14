# Qwen3-VL-Embedding 版式向量服务（独立部署）

基于 vLLM `runner="pooling"` 加载 `Qwen3-VL-Embedding-2B`，对文档图片编码**版式结构向量**（只传图不传文本），供画像引擎 / 检索器做版式相似度判别。

代码提炼自同事标注系统的 `services/embedding_server`，去掉了业务配置系统依赖，改为纯环境变量配置，可独立部署。

## 启动

```bash
MODEL_PATH=<模型目录> bash run.sh
```

关键环境变量（默认值）：

| 变量 | 默认 | 说明 |
|---|---|---|
| MODEL_PATH | 必填 | 模型目录 |
| PORT | 9031 | 服务端口 |
| GPU_IDS | 0 | 使用的 GPU |
| DTYPE | bfloat16 | 推理精度 |
| GPU_MEM_UTIL | 0.1 | 显存利用率（2B 模型很小） |
| MAX_MODEL_LEN | 4096 | 最大序列长度 |
| MAX_BATCH_SIZE | 500 | 单请求最大批量 |
| INFERENCE_CHUNK_SIZE | 10 | 推理分块 |

依赖 vLLM 0.16+（`runner="pooling"`）+ FastAPI + uvicorn + Pillow。

## 接口

- `GET /health` → `{"status": "ok"}`
- `POST /v1/embeddings`，body：

```json
{"inputs": [{"image_base64": "<base64>", "text": null}]}
```

返回：`{"object":"list","data":[{"index":0,"embedding":[...]}],"model":"...","dim":N,"count":1}`

## 聚类用法

拿到向量后，用 `L2 归一化 → 余弦相似度矩阵 → 并查集连通分量` 做版式聚类（见同事的 `cluster_embeddings.py`，阈值默认 0.9）。

## 脱敏说明

本目录代码不硬编码任何服务器路径；`MODEL_PATH` 通过环境变量传入，默认值在部署时 export，不写进提交的 run.sh。
