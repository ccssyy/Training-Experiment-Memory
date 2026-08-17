# 向量索引目录

存放从源数据派生的向量索引（大文件，**不进 git**，用 `.gitignore` 排除）。

| 文件 | 大小 | 内容 | 构建脚本 |
|---|---|---|---|
| `layout_index.json` | ~170MB | 版式向量：14 单据 3879 图（dim 2048，qwen3-vl-embedding；8 类 2145 + 2026-08-17 增 ci/bl/air/po/pi/sc 1734） | `layout_library/build_index.py` + `layout_library/build_index_extra.py` |
| `concept_index.json` | ~9.8MB | 字段语义概念向量：85 概念 431 片段（dim 1024，bge-m3） | `phase2/build_concept_index.py` |

## 为什么不进 git

这两个是**派生数据**（从源单据图片 + embedding 模型算出来的），体积大（合计 ~180MB），且可随时用构建脚本 + embedding 服务重建。进 git 会让仓库膨胀，对公开阅读者无意义。

## 怎么获取/重建

- **A800 共享目录**：`/data/collab/training-experience-memory/indexes/`（同事体验版已预置）。
- **重建**：
  ```bash
  # 版式索引 - round2 normalized cluster 结构（8 类，需 qwen3-vl-embedding 公网 9030）
  cd layout_library && SOURCE_ROOT=/path/to/normalized \
    EMBED_URL=http://124.220.53.207:9030/v1/embeddings \
    OUT=../indexes/layout_index.json python3 build_index.py

  # 版式索引 - 新增单据（ci/bl/air/po/pi/sc，goods/mixed/non_goods 早期数据 + round2 pi/sc，抽样 300/类）
  cd layout_library && MAX_PER_DOC=300 OUT=layout_extra.json \
    python3 build_index_extra.py   # 在 A800 跑（硬编码了 A800 源路径），产物再合并进主索引

  # 概念索引（需 bge-m3 服务 9033）
  cd phase2 && EMBED_URL=http://127.0.0.1:9033/v1/embeddings \
    OUT=../indexes/concept_index.json python3 build_concept_index.py
  ```

## 同步到 A800

索引更新后需手动同步（rsync 排除了 .workbuddy，索引也不在 git 流里）：

```bash
scp indexes/layout_index.json A800_5005:/data/collab/training-experience-memory/indexes/
scp indexes/concept_index.json A800_5005:/data/collab/training-experience-memory/indexes/
```
