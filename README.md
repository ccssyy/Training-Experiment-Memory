# 训练经验 Memory

> 独立于 ATF 的通用训练经验系统：训练前用历史经验分析新任务（画像 → 检索 → 建议卡），训练后把验证有效的修复沉淀回记忆库（回灌闭环）。
> 仓库：[GitHub账号]/Training-Experiment-Memory（public，唯一 origin）。
> 详细交接见 [HANDOFF.md](./HANDOFF.md)。

## 一句话

新单据字段定义 → 记忆库历史经验 → 推荐匹配的策略（含失效边界 + 证据 + 机制层归属）。三条匹配通路：别名表 + 值形态启发 + 语义向量（bge-m3）。

## 当前状态（2026-08-15）

| 阶段 | 内容 | 状态 |
|---|---|---|
| Phase 1 记忆数据 | 32 Case + 26 Claim（validated 9/confirmed 8/candidate 9）+ 5 Mechanism + 85 概念 + 标签 | ✅ |
| Phase 2 训练前推荐 | 画像引擎 + 两级检索（机制→实例）+ 建议卡 + 版式视觉确认（qwen3-vl-embedding） | ✅ MVP |
| Phase 3 训练后回灌 | EvidenceEvent + 验证门槛（validated 7 项 / rejected 8 类）+ curator | ✅ 框架 + dry-run |
| 向量检索 P4 | 字段语义向量 bge-m3 + 概念索引 + 别名未命中兜底 | ✅ 已闭环 |
| F1~F4 结构反馈 | 版式标签 / 值形态过滤 / 上下文类检索 / CTN 单位 | ✅ 全部闭环 |

文档（4 张架构图自包含 HTML + PNG 导出）：系统架构 / 完整闭环 / 对象模型（含 Mechanism）/ 状态机。

## 体验入口

### 1. 在 A800 共享目录体验（推荐）

模型在公共目录 `/data/LLM_model/`（qwen3-vl-embedding-2b、bge-m3），项目代码+memory 数据+服务都部署在 A800 共享位置（详见 [HANDOFF-secrets.md](./.workbuddy/HANDOFF-secrets.md)）。任何登录 A800 的同事都能直接体验同一份 memory 库。

```bash
# 跑画像→检索→建议卡（零 GPU，纯字段版）
echo '{"doc_type":"packing_list","fields":[{"name":"goods_quantity","sample":"1,392 BAGS"}]}' \
  | python3 phase2/advise.py    # 详见 skill-dev/ 完整 skill 入口
```

可选视觉路（用版式向量服务确认单据 + 视觉标签）：版式向量走公网 `http://124.220.53.207:9030`（同事的 Qwen3-VL-Embedding-2B），bge-m3 字段语义向量走 9033（各容器自起或 A800），调 profiler 时传 `image_path` + `embedding_server` + `index_path`。

### 2. 纯 Python 体验（任何机器，无需 GPU）

```bash
git clone https://github.com/[GitHub账号]/Training-Experiment-Memory.git
cd Training-Experiment-Memory/phase2
python3 demo.py                 # 4 个场景：装箱单 / 出口托收 / 未知字段 / bbox 任务
python3 ../phase3/dry_run.py    # 回灌状态判定：validated / rejected / confirmed / blocked
```

### 3. Skill 体验（workbuddy / Claude Code 自然语言触发）

```bash
cp -r skill-dev/training-preflight ~/.workbuddy/skills/   # 或 ~/.claude/skills/
```

然后自然语言描述任务即可，agent 自动触发 skill 走画像→检索→建议卡。

## 文档地图

| 文档 | 内容 |
|---|---|
| [HANDOFF.md](./HANDOFF.md) | 项目交接：进度、已定决策、Phase 1/2/3 详情、关键路径 |
| [docs/architecture-overview.md](./docs/architecture-overview.md) | 架构设计总览（分层/对象模型四层/状态机/检索链/回灌验证门槛） |
| [docs/applicability-dimensions.md](./docs/applicability-dimensions.md) | 结构化适用性判别维度（10 维 + when/contraindications） |
| [docs/mechanism-layer-design.md](./docs/mechanism-layer-design.md) | 机制层 Mechanism schema 设计（三层对象模型 + 稳定结构前提） |
| [docs/layout-vector-library.md](./docs/layout-vector-library.md) | 版式向量库方案（向量索引 + k-NN 软匹配，含实测诊断） |
| [docs/demo-walkthrough.md](./docs/demo-walkthrough.md) | 端到端演示：画像 → 检索 → 建议卡 |
| [docs/diagrams/](./docs/diagrams/) | 4 张架构图（HTML + PNG，自包含浏览器可直接打开） |
| [memory/schema.md](./memory/schema.md) | 冻结 v1 schema（EvidenceEvent/Case/Claim/Mechanism + 状态机） |
| [memory/field-semantics.md](./memory/field-semantics.md) | 字段语义词典 v2（85 概念 × 16 单据 × 298 字段名归并） |
| [memory/pattern-claims.md](./memory/pattern-claims.md) | 首批 PatternClaim（26 条，5 机制挂载 + 失效边界） |
| [memory/experience-cases.md](./memory/experience-cases.md) | 首批 ExperienceCase（32 条，绑证据） |
| [memory/capability-tags.md](./memory/capability-tags.md) | 通用能力标签（4 类约 40 标签） |
| [phase2/FINDINGS.md](./phase2/FINDINGS.md) | Phase 2 结构反馈（4 项已全部闭环） |
| [phase3/FINDINGS.md](./phase3/FINDINGS.md) | Phase 3 结构反馈（3 项已全部闭环） |
| [01-09*.md](./01-vision-and-scope.md) 等 | 早期研究讨论稿（构想/先例/任务画像/架构/同事综合/对象模型） |

## 设计原则

- **推荐是建议不是自动执行**：永不自动改参数；人工接受后生效。
- **回灌永远停在人工验收闸前**：系统不自动写库。
- **能力标签与字段名解耦**：装箱单经验通过 `grouped_value + dense_table` 标签迁移到任何同类表格单据，而非靠"装箱单"字段名。
- **机制层跨字段类型稳定**：Mechanism 只基于结构属性（语义/基数/值形态/版式/跨页），字段类型划分变更只动 Claim 引用。
- **独立化原则**：核心层不 import 任何消费方代码（ATF 通过适配接口单向依赖）。