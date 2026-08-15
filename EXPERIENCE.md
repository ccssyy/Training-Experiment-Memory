# 训练经验 Memory — 同事体验指南（A800 共享目录）

> 位置：`/data/collab/training-experience-memory/`
> 这是「当前整理版 memory 库」的**独立体验副本**，与开发者版本（`/data/sam`）物理隔离——**随便改、随便跑，不影响开发版**。

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

```bash
git clone https://github.com/[GitHub账号]/Training-Experiment-Memory.git
cd Training-Experiment-Memory/phase2 && python3 demo.py        # 纯字段版，零 GPU 零依赖
```

- **纯字段版**（画像→检索→建议卡）只用标准库，任何 mac 的 python3 都能跑，这是核心体验，够用。
- **视觉版**（可选，需 embedding）：
  - bge-m3（字段语义向量，568M）mac CPU 就能跑，或 HTTP 调 A800 `9033`；
  - qwen3-vl-embedding（版式视觉，2B）mac CPU 跑不现实，走 HTTP 调 A800 `9031`（需能连 A800 内网/VPN）。
  - 即：本地跑规则 + 远程调 A800 的 embedding 服务。

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

**方案一（推荐，最省事）：版式共享 + bge 自起**

版式服务已由开发者起好并共享（容器 IP `172.18.0.8`，同 docker 网络可直接访问），你只需自起 bge：

```bash
# 起 bge-m3（字段语义向量，568M，加载快）
PY=/data/sam/env/torch210_vllm0181_bnb_qwen3vl/bin/python   # 复用共享 env（含 transformers+fastapi）
cd /data/collab/training-experience-memory/bge_embedding_server
MODEL_PATH=/data/LLM_model/bge-m3 PORT=9033 GPU_IDS=<空闲卡号> nohup $PY app.py > server.log 2>&1 &
curl -s http://127.0.0.1:9033/health    # 期望 {"status":"ok","device":"cuda"}
```

访问地址：版式 `172.18.0.8:9031`，bge `127.0.0.1:9033`。

**方案二（完全隔离，自起全部服务）**

前提：你的容器已挂载 `/data`（`-v /data:/data`）+ GPU 权限（`--gpus all`）。

```bash
PY=/data/sam/env/torch210_vllm0181_bnb_qwen3vl/bin/python

# 1. 起版式服务（qwen3-vl-embedding-2b，占一张卡，加载约 75s）
cd /data/collab/training-experience-memory/embedding_server
MODEL_PATH=/data/LLM_model/Qwen3-VL-Embedding-2B PORT=9031 GPU_IDS=<卡号A> nohup $PY app.py > server.log 2>&1 &

# 2. 起字段语义服务（bge-m3，568M，占显存小）
cd /data/collab/training-experience-memory/bge_embedding_server
MODEL_PATH=/data/LLM_model/bge-m3 PORT=9033 GPU_IDS=<卡号B> nohup $PY app.py > server.log 2>&1 &

# 3. 验证
curl -s http://127.0.0.1:9031/health    # 期望 {"status":"ok"}
curl -s http://127.0.0.1:9033/health    # 期望 {"status":"ok","device":"cuda"}
```

> 卡号提示：8 卡 A800，当前 GPU 0（开发者版式）、GPU 7（开发者 bge）已占用，GPU 1~6 空闲。同事自起服务时 `<卡号>` 选空闲卡即可；同一张卡跑两个进程需各自设 `GPU_MEM_UTIL` 分摊显存（如各 0.4）。

给 profiler 传 `image_path` + `embedding_server`（版式地址）+ `concept_embedding_server`（bge 地址）+ `index_path` 即走完整视觉路；不传则纯字段版（零依赖）。

## 文档

- `README.md` / `HANDOFF.md` — 项目总览 + 交接
- `docs/architecture-overview.md` — 架构设计总览
- `docs/diagrams/*.html`（+ 同名 `.png`）— 4 张架构图
- `docs/demo-walkthrough.md` — 端到端演示
