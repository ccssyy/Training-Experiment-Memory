# 训练经验 Memory — 体验指南（A800 共享目录）

> 位置：`/data/collab/training-experience-memory/`
> 这是「当前整理版 memory 库」的**独立体验副本**，与开发版本物理隔离——**随便改、随便跑，不影响开发版**。

## 这是什么

训练经验 Memory 系统：给一个新单据/字段抽取任务，从历史训练经验里推荐匹配的策略（含失效边界 + 证据 + 机制层归属）。记忆数据是 32 Case + 26 Claim + 5 Mechanism + 85 字段语义概念。

## 一分钟上手（纯字段版，零依赖）

```bash
cd /data/collab/training-experience-memory/phase2
python3 demo.py        # 任何 python3 都可（只用标准库），4 个场景
```

demo 走完整链路：字段定义 → 画像引擎 → 检索（机制→实例两级）→ 建议卡。

**自己造一个字段定义试**（画像→检索→建议卡）：

```bash
echo '{"doc_type":"packing_list","fields":[{"name":"goods_quantity","sample":"1,392 BAGS"},{"name":"goods_gross_weight","sample":"24,897 KGS"}]}' \
  | python3 skill-dev/training-preflight/scripts/advise.py
```

## 用自然语言体验（skill，workbuddy / Claude Code / Codex 通用）

Agent Skills 标准（agentskills.io）三款工具通用，SKILL.md 只需 `name`+`description`，本 skill 直接兼容。装到对应工具的用户级 skills 目录：

```bash
# workbuddy
cp -r /data/collab/training-experience-memory/skill-dev/training-preflight ~/.workbuddy/skills/
# Claude Code
cp -r /data/collab/training-experience-memory/skill-dev/training-preflight ~/.claude/skills/
# Codex CLI（触发：/skills 选，或提示词写 $training-preflight）
cp -r /data/collab/training-experience-memory/skill-dev/training-preflight ~/.codex/skills/
```

然后自然语言描述任务（如「我要训练海运单抽取，字段有提单号、船名、毛重、净重」），agent 自动触发 skill 走画像→检索→建议卡。

## 在自己 mac 上体验（无需 A800）

两种拿代码的方式：

**方式一：从 A800 共享目录下载（推荐，含索引，约 108MB）**

```bash
scp -r [开发机]:/data/collab/training-experience-memory ./training-experience-memory
# 或 rsync（支持断点续传）
rsync -av [开发机]:/data/collab/training-experience-memory/ ./training-experience-memory/
cd training-experience-memory/phase2 && python3 demo.py
```

这样连 `indexes/` 下的两个向量索引一起拿到，视觉版也能用。

**方式二：git clone（纯代码，无索引）**

```bash
git clone https://github.com/ccssyy/Training-Experiment-Memory.git
cd Training-Experiment-Memory/phase2 && python3 demo.py
```

git 里没有 `indexes/` 大索引，视觉版需自行重建（见文末索引说明）。

- **纯字段版**（画像→检索→建议卡）只用标准库，任何 mac 的 python3 都能跑，这是核心体验，够用。
- **视觉版**（可选，需 embedding）：
  - bge-m3（字段语义向量，568M）mac CPU 就能跑，或 HTTP 调远程 `9033`；
  - qwen3-vl-embedding（版式视觉，2B）走 HTTP 调公网 `http://124.220.53.207:9030`（公共部署，无需自起）。
  - 即：本地跑规则 + 远程调 embedding 服务。

## memory 数据在哪

```
phase2/data/
├── cases.json        # 32 条 ExperienceCase（证据）
├── claims.json       # 26 条 PatternClaim（含 mechanism_id）
├── mechanisms.json   # 5 条 Mechanism（跨字段类型稳定方案）
├── concepts.json     # 85 字段语义概念 + 别名
└── tags.json         # 能力标签
```

`memory/*.md` 是人读版本（experience-cases.md / pattern-claims.md / field-semantics.md / schema.md）。

## 视觉版（需 embedding 服务）

模型在公共目录 `/data/LLM_model/`（Qwen3-VL-Embedding-2B、bge-m3）。

**版式服务（qwen3-vl-embedding）：统一共用公网服务**

`http://124.220.53.207:9030`（公共 Qwen3-VL-Embedding-2B，dim=2048），**无需自起**，直接调。

**bge 服务（字段语义向量）：各容器自起**

前提：容器已挂载 `/data`（能访问 `/data/LLM_model/bge-m3` 模型）+ GPU 权限（`--gpus all`）。

```bash
# 0. 准备 python 环境（一次即可，依赖已列在 requirements.txt）
python3 -m venv bge_env
bge_env/bin/pip install -r /data/collab/training-experience-memory/bge_embedding_server/requirements.txt

# 1. 起 bge 服务
cd /data/collab/training-experience-memory/bge_embedding_server
MODEL_PATH=/data/LLM_model/bge-m3 PORT=9033 GPU_IDS=<空闲卡号> nohup ../bge_env/bin/python app.py > server.log 2>&1 &
curl -s http://127.0.0.1:9033/health    # 期望 {"status":"ok","device":"cuda"}
```

> 若容器里已有含 transformers+torch+fastapi 的现成环境，可跳过第 0 步，直接 `PY=<现成环境>/bin/python` 起服务。

访问地址：版式 `http://124.220.53.207:9030`，bge `http://127.0.0.1:9033`。

**完全隔离自起版式（可选，不想依赖公网时）**

前提：你的容器已挂载 `/data`（`-v /data:/data`）+ GPU 权限（`--gpus all`）。

```bash
# 环境依赖见 embedding_server/requirements.txt（vllm + fastapi + pillow）
PY=<含 vllm+fastapi 的 python 环境>/bin/python
cd /data/collab/training-experience-memory/embedding_server
MODEL_PATH=/data/LLM_model/Qwen3-VL-Embedding-2B PORT=9031 GPU_IDS=<空闲卡号> nohup $PY app.py > server.log 2>&1 &
curl -s http://127.0.0.1:9031/health    # 期望 {"status":"ok"}
```

> 卡号提示：8 卡 A800，当前 GPU 7（bge）已占用，其余空闲。自起 bge/版式时 `<空闲卡号>` 选空闲卡即可；同一张卡跑两个进程需各自设 `GPU_MEM_UTIL` 分摊显存（如各 0.4）。

给 profiler 传 `image_path` + `embedding_server`（版式地址）+ `concept_embedding_server`（bge 地址）+ `index_path` 即走完整视觉路；不传则纯字段版（零依赖）。

**索引文件路径**（体验目录里已预置，在 `indexes/` 下，不进 git，是单独同步的大文件）：

| 索引 | 路径 | 内容 |
|---|---|---|
| 版式索引 | `indexes/layout_index.json` | 14 单据 3879 版式向量（dim 2048，2026-08-17 增 ci/bl/air/po/pi/sc） |
| 概念索引 | `indexes/concept_index.json` | 85 概念 431 片段（dim 1024） |

完整视觉版调用示例（skill advise.py 走视觉路）：

```bash
cd /data/collab/training-experience-memory
echo '{"doc_type":"aco","image_path":"/path/to/sample.png","fields":[{"name":"beneficiary_account","sample":"IT13..."}]}' \
  | EMBEDDING_SERVER=http://124.220.53.207:9030 \
    CONCEPT_EMBEDDING_SERVER=http://127.0.0.1:9033 \
    LAYOUT_INDEX=/data/collab/training-experience-memory/indexes/layout_index.json \
    CONCEPT_INDEX=/data/collab/training-experience-memory/indexes/concept_index.json \
    python3 skill-dev/training-preflight/scripts/advise.py
```

> 索引若缺失（比如 git clone 拿到的代码没有索引），可用 `layout_library/build_index.py`（版式 8 类，需公网 9030）+ `layout_library/build_index_extra.py`（版式新增 6 类，A800 跑）+ `phase2/build_concept_index.py`（概念，需 bge 9033）重新构建。

## 文档

- `README.md` / `HANDOFF.md` — 项目总览 + 交接
- `docs/architecture-overview.md` — 架构设计总览
- `docs/diagrams/*.html`（+ 同名 `.png`）— 4 张架构图
- `docs/demo-walkthrough.md` — 端到端演示
