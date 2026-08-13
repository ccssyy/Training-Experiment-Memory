# 记忆数据 Schema（冻结 v1）

> 日期：2026-08-13 ｜ 状态：**冻结**（Phase 1 产出依此 schema，后续变更需版本升级）
> 来源：`08-object-model-and-hosting.md` 草案的正式化 + `07-colleague-synthesis.md` 的能力标签体系。

## 0. 对象模型总览

```
具体历史事实（run/checkpoint/badcase/anno）
  └─ ExperienceCase（案例：单次观察，绑证据，不可变）
       多案例聚合 ──► PatternClaim（通用模式：可检索、可迁移，有状态机）
                       通用能力标签（检索键，开放演化）
```

- **检索/推荐用 PatternClaim**（跨单据通用）；**追溯用 ExperienceCase**（回到具体 run）。
- 单次实验结果 ≠ 通用规律：只有多 Case 聚合、且明确失效边界，才升级为可迁移 Claim。

## 1. ExperienceCase（证据侧）

一条 case = 一次实验观察，**不可变**。字段（`*` = 必填）：

```yaml
case_id*: CASE-0001
run_ref: 训练/评估 run 或 checkpoint 引用          # 如 runs/20260711_.../ 或 checkpoint-342
fields: [goods_quantity, item_no, ...]             # 涉及的具体字段（可空，纯数据质量 case 可空）
layout: {document_type, cluster, page_role}        # 具体版式（如 packing_list / dense_table）
problem*: {pattern_id, symptom_metric}             # 观察到的问题（pattern_id 指向 problem pattern 库）
intervention: {strategy_id, changes}               # 施加的干预
outcome: {baseline_ref, delta, protected_regression}  # delta 必须对 prior-best，不对实验内部最佳
evidence_refs*: [artifact refs]                    # 可回溯（报告路径/registry 条目/analysis_outputs）
provenance*: {source_revisions, decision_ref, created_at}
```

约束：
- `evidence_refs` 非空（缺证据不入库）。
- `outcome.delta` 必须对 prior-best 基线；simulation/fake 结果不得产生 validated 结论。
- case 一旦写入不修改；新增观察 → 新 case_id。

## 2. PatternClaim（模式侧）

多条 Case 聚合出的跨单据通用结论。字段（`*` = 必填）：

```yaml
claim_id*: CLAIM-0001
status*: candidate | validated | rejected | unresolved | superseded
capability_tags*:                                 # 通用能力标签（检索键，见 capability-tags.md）
  semantic: [quantity, monetary, weight]
  value_shape: [grouped_value, numeric_unit]
  cardinality: [multi_value, row_aligned, cross_page_group]
  layout: [dense_table, long_table]
problem_pattern*: 行级归组数量字段在密集跨页表格易漏行
intervention_strategy*: 长表分段 + 行级守恒 + 连续重叠 core
applicability:
  preconditions: [...]                             # 适用条件
  contraindications*: [...]                        # 失效边界（必填；validated 必须非空）
  confidence: high | medium | low
  transfer_level: direct | structural | mechanism | context   # 迁移层级定性标签
supported_by*: [CASE-0001, CASE-0007, ...]         # 引用案例（≥1）
outcome_aggregate: {typical_delta, cost_range, stability}
```

约束：
- `status=validated` 需：目标改善 + bbox/基数/归组无未解释退化 + 保护字段无回归 + evaluator 有效 + runtime raw 完整 + ID-OOD 可解释 + 人工验收（7 项）。
- `status=rejected` 用于"验证失败的策略"，作为负经验（contraindication 素材）。
- `status=unresolved` 用于"问题确认但无解决路径"的长期难例，显式建模防止反复试错。
- 迁移层级：`direct`（结构/bbox/版式/评估基本一致）> `structural`（结构一致版式差异）> `mechanism`（字段不同机制相同）> `context`（仅业务上下文相似，**不生成训练动作**）。

## 3. 状态机

```
              ┌─────────────┐
ExperienceCase │ (不可变)    │  一次性写入，无状态转换
              └─────────────┘

PatternClaim:
  candidate ──► validated ──► superseded
     │              │
     ├──► rejected ─┴──► (保留为负经验)
     └──► unresolved（长期难例，阻断重复试错）
```

每个状态转换 = 一条裁判记录（消费方侧记录，如 ATF 的 Decision Ledger）；memory 核心不引入新事实 owner。

## 4. 通用能力标签

标签是开放演化的检索键（见 `capability-tags.md`）。规则：
- 标签 `validated` 后进正式索引；新标签为 `candidate`，人工确认后升级。
- 检索匹配的是**标签**（语义/值形态/基数/版式），不是字段名——字段名千变万化，标签稳定。
