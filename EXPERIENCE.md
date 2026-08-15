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

## 视觉版（可选，需 embedding 服务）

模型在公共目录 `/data/LLM_model/`（Qwen3-VL-Embedding-2B、bge-m3）。当前开发者版本已起服务：

| 服务 | 端口 | 模型 | 用途 |
|---|---|---|---|
| 版式向量 | 9031 | Qwen3-VL-Embedding-2B | 样例图 → 版式结构向量（跨单据视觉确认） |
| 字段语义向量 | 9033 | bge-m3 | 字段名 → 语义向量（别名表未命中兜底） |

给 profiler 传 `image_path` + `embedding_server` + `index_path` 即走视觉路；不传则纯字段版（零依赖）。

## 文档

- `README.md` / `HANDOFF.md` — 项目总览 + 交接
- `docs/architecture-overview.md` — 架构设计总览
- `docs/diagrams/*.html`（+ 同名 `.png`）— 4 张架构图
- `docs/demo-walkthrough.md` — 端到端演示
