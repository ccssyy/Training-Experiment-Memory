# 对象模型映射与承载位置（v8：合并决策 2、3 的澄清）

> 日期：2026-08-13 ｜ 状态：讨论稿
> 承接 v7 综合分析的"待定夺决策 2、3"

## 决策 2：对象模型怎么映射（experience-card 一层 → Case + Claim 两层）

### 2.1 问题本质

我们 v1-v6 只设计了**一层** `experience-card/v1`（把"证据"和"通用结论"混在一个对象里）。同事拆成**两层**：

- **ExperienceCase（案例）**：具体的一次实验观察，绑定证据（哪次 run/checkpoint/badcase/指标）。
- **PatternClaim（能力模式声明）**：多案例聚合出的**跨单据通用**结论（如"行级归组数量字段在密集跨页表格易漏行"），引用多条 Case 作支撑。

拆两层的价值：**"证据"和"通用规律"分离**。单次实验可能只是特例，不能直接当规律用；只有多条 Case 聚合、且明确失效边界，才升级为可跨单据迁移的 Claim。我们之前一层 schema 会诱导"把一次结果当普适经验"。

### 2.2 映射方案

我们原来的 experience-card 字段，按"证据侧/模式侧"拆到两个对象：

| 原 experience-card 字段 | 归入 |
|---|---|
| problem.pattern_id / symptom_metric / affected_fields | → PatternClaim（模式侧） |
| intervention.strategy_id / changes / frozen_variables | → PatternClaim |
| applicability.preconditions / contraindications / confidence | → PatternClaim |
| outcome.baseline_ref / delta / cost / stability | → 两者都留（Claim 存聚合 delta，Case 存单次 delta） |
| evidence_refs / provenance.source_revisions / decision_ref | → ExperienceCase（证据侧） |

### 2.3 两个对象的 schema（草案）

```yaml
# ExperienceCase：具体证据（一 case 一次实验观察，不可变）
case_id: CASE-0001
run_ref: run/checkpoint 引用
fields: [goods_quantity, item_no, ...]          # 具体字段
layout: {document_type, cluster, page_role}      # 具体版式
problem: {pattern_id, symptom_metric}            # 观察到的问题
intervention: {strategy_id, changes}             # 施加的干预
outcome: {baseline_ref, delta, protected_regression}
evidence_refs: [artifact refs]                   # 可回溯
provenance: {source_revisions, decision_ref, created_at}

# PatternClaim：通用能力模式（多条 Case 聚合，可检索、可迁移）
claim_id: CLAIM-0001
status: candidate | validated | rejected | unresolved | superseded
capability_tags:                                 # 通用能力标签（检索键）
  semantic: [quantity, monetary]
  value_shape: [grouped_value, numeric_unit]
  cardinality: [multi_value, row_aligned]
  layout: [dense_table, long_table, cross_page]
problem_pattern: 行级归组数量字段在密集跨页表格易漏行
intervention_strategy: 长表分段 + 行级守恒 + 连续重叠 core
applicability:
  preconditions: [...]
  contraindications: [...]                       # 失效边界（必填）
  confidence: high | medium | low
supported_by: [CASE-0001, CASE-0007, ...]       # 引用案例
outcome_aggregate: {typical_delta, cost_range, stability}
```

**检索与推荐用 PatternClaim（跨单据通用）；证据追溯用 ExperienceCase（回到具体 run）。** 这样"新单据 → 能力标签 → Claim 迁移"走得通，且每条结论都能落回具体证据。

## 决策 3：承载位置（[同事项目] 不是 git 仓库）

### 3.1 事实澄清

`[同事设计仓库]/` **不是 git 仓库**（无 `.git`、无 remote、无 commit），是同事 [同事] 的**个人工作目录**，里面只有：
- `docs/`：两份 Preflight 设计文档
- `tmp/non_goods_round3_analysis/`：同事正在做的 non-goods round3 真实数据分析包（2878 张图、checkpoint-342、provenance、SPLITS.md）
- `.codex/session-digests/`：会话摘要

所以"memory 直接落在 [同事项目] 演进"这个选项**不成立**——那只是同事的草稿目录，不是可协作的正式仓库。

### 3.2 承载选项

| 选项 | 说明 | 判断 |
|---|---|---|
| A. 独立新 git 仓库 | 新建 `training-experience-memory` 仓库，托管到 GitHub/公司 git | 最干净，符合"独立于 ATF"，但需新建+定托管 |
| B. ATF 仓库独立子目录/worktree | 我们现在做的：ATF 分支下独立 worktree + 独立研究集目录 | 短期可行，但 memory 仍是 ATF 仓库的一部分 |
| C. [同事项目] 目录 | 同事个人目录 | ❌ 非 git，不可协作 |

### 3.3 建议

**短期（Phase 1 阶段）**：继续用现在的独立 worktree + 本地 `TrainingExperienceMemory/` 目录演进，因为 Phase 1 是"整理历史经验成 Case/Claim"，产出的主要是**文档 + 数据**，还没到必须独立仓库的程度。

**中期（Phase 2 实现分析器前）**：升级为**独立 git 仓库**，ATF 和同事的 [同事项目] 都作为消费方接入。理由：memory 的代码（画像引擎/标签提炼/检索/回灌）要独立测试、独立发布，不能再寄生在 ATF 仓库。

**同事工作的复用**：同事的 `tmp/non_goods_round3_analysis/`（真实 non-goods 数据 + provenance + checkpoint-342）是 Phase 1 整理 ExperienceCase 的**现成素材**——它已经把 round3 non-goods 的字段合同、split、badcase、指标都结构化好了，可以直接转成首批 ExperienceCase。

## 4. 结论

- **决策 2**：experience-card 拆为 `ExperienceCase`（证据）+ `PatternClaim`（通用模式）两层，检索用 Claim、追溯用 Case。
- **决策 3**：[同事项目] 非 git 仓库，不可作为承载；Phase 1 先在独立 worktree 演进，Phase 2 前升级独立 git 仓库；同事的 non_goods round3 分析包是 Phase 1 首批 Case 的现成素材。

这两点确认后，即可正式进入 Phase 1：以同事 Preflight 框架（Case/Claim/标签/矩阵）+ 我们的向量/独立化为骨架，把 Qwen 历史归档 + 同事 non_goods 分析包整理成首批 ExperienceCase + PatternClaim。
