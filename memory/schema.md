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

**字段类型图例**（每个字段注释尾标注）：

| 类型 | 标记 | 含义 |
|---|---|---|
| 单值 | `单值` | 一个标量（字符串/枚举/数字/时间戳） |
| 列表 | `列表` | 零个或多个标量的数组（`[a, b, ...]`） |
| 对象 | `对象` | 嵌套键值对（`{k1, k2, ...}`），子键类型在括号内再标 |

## 1. ExperienceCase（证据侧）

一条 case = 一次实验观察，**不可变**。字段（`*` = 必填）：

```yaml
case_id*: CASE-0001                                  # 单值
run_ref: 训练/评估 run 或 checkpoint 引用              # 单值（如 runs/20260711_.../ 或 checkpoint-342）
fields: [goods_quantity, item_no, ...]                # 列表（可空；纯数据质量 case 可空）
layout: {document_type, cluster, page_role}           # 对象（document_type/cluster/page_role 均单值）
problem*: {pattern_id, symptom_metric}                # 对象（pattern_id 单值；symptom_metric 单值/对象）
intervention: {strategy_id, changes}                  # 对象（strategy_id 单值；changes 列表）
outcome: {baseline_ref, delta, protected_regression}  # 对象（baseline_ref 单值；delta 单值/对象；protected_regression 单值）
evidence_refs*: [artifact refs]                       # 列表（可回溯：报告路径/registry 条目/analysis_outputs）
provenance*: {source_revisions, decision_ref, created_at}  # 对象（source_revisions 列表；decision_ref/created_at 单值）
```

约束：
- `evidence_refs` 非空（缺证据不入库）；允许多引用（多证据互证），不限制数量。
- `outcome.delta` 必须对 prior-best 基线；simulation/fake 结果不得产生 validated 结论。
- case 一旦写入不修改；新增观察 → 新 case_id。

## 2. PatternClaim（模式侧）

多条 Case 聚合出的跨单据通用结论。字段（`*` = 必填）：

```yaml
claim_id*: CLAIM-0001                                # 单值
status*: candidate | validated | rejected | unresolved | superseded  # 单值（枚举）
capability_tags*:                                   # 对象（4 个子键，均列表）
  semantic: [quantity, monetary, weight]
  value_shape: [grouped_value, numeric_unit]
  cardinality: [multi_value, row_aligned, cross_page_group]
  layout: [dense_table, long_table]
problem_pattern*: 行级归组数量字段在密集跨页表格易漏行   # 单值
intervention_strategy*: 长表分段 + 行级守恒 + 连续重叠 core  # 单值
applicability:                                      # 对象
  preconditions: [...]                              # 列表（适用条件）
  contraindications*: [...]                         # 列表（失效边界；必填；validated 必须非空）
  confidence: high | medium | low                   # 单值（枚举）
  transfer_level: direct | structural | mechanism | context  # 单值（枚举）
supported_by*: [CASE-0001, CASE-0007, ...]          # 列表（引用案例，≥1）
outcome_aggregate: {typical_delta, cost_range, stability}  # 对象（typical_delta/cost_range/stability 均单值）
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
