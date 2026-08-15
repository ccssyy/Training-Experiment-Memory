# 记忆数据 Schema（冻结 v1）

> 日期：2026-08-13 ｜ 状态：**冻结**（Phase 1 产出依此 schema，后续变更需版本升级）
> 来源：`08-object-model-and-hosting.md` 草案的正式化 + `07-colleague-synthesis.md` 的能力标签体系。

## 0. 对象模型总览

```
EvidenceEvent（训练事实：badcase 结论 + 指标 + 评估，追加式不可变）
  └─ ExperienceCase（案例：单次观察，绑证据，不可变）
       多案例聚合 ──► PatternClaim（实例：机制在某字段类型下的适用，有状态机）
                       多实例归纳 ──► Mechanism（机制：跨字段类型稳定，有结构前提）
                       通用能力标签（检索键，开放演化）
```

- **检索/推荐用 PatternClaim**（实例，跨单据通用）+ **Mechanism**（机制，跨字段类型统一）；**追溯用 ExperienceCase**（回到具体 run）；**回灌用 EvidenceEvent**（训练后追加事实）。
- 单次实验结果 ≠ 通用规律：只有多 Case 聚合、且明确失效边界，才升级为可迁移 Claim。
- 多 Claim 归纳为 Mechanism（跨字段类型的稳定方案）；机制层只基于稳定结构属性（基数/值形态/版式/跨页），**不碰易变的字段类型划分**（lane/标注范围）。
- EvidenceEvent 是回灌闭环的入口：训练后先追加 EvidenceEvent，再关联/创建 Case、生成 candidate Claim。

**字段类型图例**（每个字段注释尾标注）：

| 类型 | 标记 | 含义 |
|---|---|---|
| 单值 | `单值` | 一个标量（字符串/枚举/数字/时间戳） |
| 列表 | `列表` | 零个或多个标量的数组（`[a, b, ...]`） |
| 对象 | `对象` | 嵌套键值对（`{k1, k2, ...}`），子键类型在括号内再标 |

## 1. EvidenceEvent（训练事实，回灌入口）

训练后追加的事实事件，**不可变**。字段（`*` = 必填）：

```yaml
event_id*: EVT-0001                                    # 单值
run_ref*: 训练/评估 run 或 checkpoint 引用               # 单值
kind: intervention | diagnostic                        # 单值（枚举）——干预验证 vs 归因/诊断
badcase_analysis: {problem_pattern, suggested_fix}      # 对象（problem_pattern/suggested_fix 均单值）
metrics:                                               # 对象
  baseline: prior-best                                 # 单值（基线 ref）
  delta: {amount_F1: "0.4211 → 1.0000"}                # 单值/对象（必须对 prior-best）
  improved: true | false                               # 单值（目标是否改善）
  degradation:                                         # 对象（退化矩阵，验证门槛用）
    core: false                                        # 核心指标退化
    protected: false                                   # 保护字段回归
    empty_output: false                                # 空输出/截断增加
    repeated_group: false                              # 重复 group 增加
    bbox_card_group: false                             # bbox/基数/归组退化
evaluator:                                             # 对象
  valid: true                                          # 单值（evaluator 有效）
  runtime_raw: true                                    # 单值（runtime raw 完整）
  id_ood: ID/OOD 同合同复测                             # 单值（ID-OOD 可解释）
  leakage: false                                       # 单值（污染评估提升）
  adapter_missing: false                               # 单值（runtime 未加载 adapter）
  fake: false                                          # 单值（simulation/fake 结果）
provenance: {source_revisions, created_at}              # 对象（source_revisions 列表；created_at 单值）
```

约束：
- EvidenceEvent 只追加、不修改；新训练事实 → 新 event_id。
- `metrics.delta` 必须对 prior-best 基线（不对实验内部最佳 checkpoint）。
- `kind=diagnostic` 的 event 只能产 confirmed（归因确认），不能产 validated。
- 一个 EvidenceEvent 可关联/创建一个 ExperienceCase，并生成 candidate Claim。

## 2. ExperienceCase（证据侧）

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

## 3. PatternClaim（模式侧）

多条 Case 聚合出的跨单据通用结论。字段（`*` = 必填）：

```yaml
claim_id*: CLAIM-0001                                # 单值
mechanism_id: MECH-0001                              # 单值（可选；归属机制，未归纳时 null）
status*: candidate | confirmed | validated | rejected | unresolved | superseded  # 单值（枚举）
capability_tags*:                                   # 对象（4 个子键，均列表）——字段语义维度
  semantic: [quantity, monetary, weight]
  value_shape: [grouped_value, numeric_unit]
  cardinality: [multi_value, row_aligned, cross_page_group]
  layout: [dense_table, long_table]
task_shape:                                         # 对象（可选）——任务形态维度，上下文类经验用
  lane: goods | non_goods | both                    # 单值
  bbox_required: true | false                       # 单值
  cross_page: true | false                          # 单值
  triggers: [gb_large_batch, vllm_runtime, cluster_split, field_align]  # 列表（训练配置/运行时/评估口径触发词）
problem_pattern*: 行级归组数量字段在密集跨页表格易漏行   # 单值
intervention_strategy*: 长表分段 + 行级守恒 + 连续重叠 core  # 单值
applicability:                                      # 对象（结构化适用性判定，见 docs/applicability-dimensions.md）
  when:                                             # 对象（可采纳条件，AND 全满足才推荐）
    lane: [goods]                                   # 列表（lane 一级判别：goods/non_goods）
    languages: [zh, en, zh_en]                      # 列表（语言）
    doc_types: [packing_list]                       # 列表（单据类型）
    cardinality: [grouped_value]                    # 列表（字段基数，从 capability_tags 派生）
    value_shape: [numeric_value]                    # 列表（值形态，从 capability_tags 派生）
    layout: [dense_table, long_table]               # 列表（版式标签）
    distribution: {support_min: 20}                 # 对象（字段分布门槛，可选）
    data_scale: {min_samples: 2000}                 # 对象（数据规模，可选）
  contraindications:                                # 列表（不适用条件，OR 命中任一即降权/过滤）
    - when: {lane: non_goods}                       # 对象（结构化触发条件）
      reason: 非货描迁移能力弱，本经验仅货描验证过  # 单值（不适用原因）
  confidence: high | medium | low                   # 单值（枚举）
  transfer_level: direct | structural | mechanism | context  # 单值（枚举）
  expires_at: 2026-12-31                            # 单值（可选；过期降级为 observed）
supported_by*: [CASE-0001, CASE-0007, ...]          # 列表（引用案例，≥1）
outcome_aggregate: {typical_delta, cost_range, stability}  # 对象（typical_delta/cost_range/stability 均单值）
```

**检索维度**：Claim 有两个并列检索键——
- `capability_tags`（字段语义）：字段语义类经验（漏行/串位/币种/同值冒充…）靠它命中。
- `task_shape`（任务形态）：上下文类经验（训练配置/运行时/评估口径，如 GB256 主线、vLLM bbox、cluster split、字段面对齐）靠它命中。这类经验的 `capability_tags` 可为空，但 `task_shape` 必须非空，否则检索永远命中不了（成为"死数据"）。

约束：
- `status=confirmed` 用于"归因/诊断/方法论确认"类结论——问题归因正确、或工程决策合理，但**未经过"干预→训练改善"的验证**（如"空输出二分""指标下降先查口径"）。证据强度低于 validated，检索时权重相应降低。
- `status=validated` 需：目标改善 + bbox/基数/归组无未解释退化 + 保护字段无回归 + evaluator 有效 + runtime raw 完整 + ID-OOD 可解释 + 人工验收（7 项）。**validated 是"干预验证通过"，不是"结论可信"。**
- `status=rejected` 用于"验证失败的策略"，作为负经验（contraindication 素材）。
- `status=unresolved` 用于"问题确认但无解决路径"的长期难例，显式建模防止反复试错。
- `applicability.when` 判定为 AND（全满足才推荐）；`contraindications[].when` 判定为 OR（命中任一即降权/过滤）。画像缺失某维度时该维度不参与判定（宽松通过），不因缺数据误拒。
- 迁移层级：`direct`（结构/bbox/版式/评估基本一致）> `structural`（结构一致版式差异）> `mechanism`（字段不同机制相同）> `context`（仅业务上下文相似，**不生成训练动作**）。

## 4. Mechanism（机制侧）

多条 Claim 归纳出的**跨字段类型**稳定方案。字段（`*` = 必填）：

```yaml
mechanism_id*: MECH-0001                           # 单值
name*: 行级归组字段漏行                             # 单值（机制名，人读）
problem_mechanism*: 行级归组字段在密集跨页表格因分段/边界处理不当漏行  # 单值（问题机制，稳定本质，不含字段类型）
intervention*: 长表分段 + 行级守恒 + 连续重叠 core  # 单值（统一干预方案，跨字段类型通用）
structural_preconditions*:                        # 对象（稳定结构前提，只含稳定属性）
  cardinality: [grouped_value]                    # 列表（基数）
  value_shape: []                                 # 列表（值形态，空=不限）
  layout: [dense_table, long_table]               # 列表（版式结构）
  cross_page: true                                # 单值（是否跨页）
claims*: [CLAIM-0001, CLAIM-0002]                 # 列表（机制的各字段类型实例，引用，≥1）
cases*: [CASE-0001, CASE-0002, ...]               # 列表（归纳证据，引用，≥1）
status: active | merged | superseded | deprecated # 单值（枚举）
confidence: high | medium | low                   # 单值（枚举，归纳置信度）
created_at: 2026-08-15                            # 单值
updated_at: 2026-08-15                            # 单值
```

约束：
- `structural_preconditions` **只含稳定结构属性**（cardinality/value_shape/layout/cross_page），**不含** lane/doc_types/languages 等易变维度——这是机制层与实例层的分水岭，字段类型划分怎么变，机制层都不动。
- `claims` 挂载机制的各字段类型实例；每个实例（Claim）带易变维度（`when.lane` 等）。
- `status` 比 Claim 状态机简单：机制是归纳结果，不是待验证干预。`deprecated` 表示被新机制取代（`superseded` 保留旧记录供追溯，`deprecated` 标记已淘汰不再推荐）。
- 检索先命中 Mechanism（结构属性 AND），再在机制下定位 Claim 实例（lane/doc_types）；命中机制但无匹配实例时，推荐机制 + 标注「当前字段类型无验证实例」。

## 5. 状态机

```
              ┌─────────────┐
ExperienceCase │ (不可变)    │  一次性写入，无状态转换
              └─────────────┘

PatternClaim:
  candidate ──► confirmed ──► validated ──► superseded
     │              │
     ├──► rejected ─┴──► (保留为负经验)
     └──► unresolved（长期难例，阻断重复试错）

  confirmed = 归因/诊断/方法论确认（结论可信，但"干预→改善"未验证）
  validated = 干预验证通过（7 项全过）

Mechanism:
  active ──► merged ──► superseded（保留旧记录供追溯）
     └──────► deprecated（被新机制取代，不再推荐）
```

每个状态转换 = 一条裁判记录（消费方侧记录，如 ATF 的 Decision Ledger）；memory 核心不引入新事实 owner。

## 6. 通用能力标签与字段语义概念

标签与概念都是开放演化的检索键（见 `capability-tags.md`、`field-semantics.md`）。规则：
- 标签/概念 `validated` 后进正式索引；新标签/新概念为 `candidate`，人工确认 + 积累 Case 后升级。
- 检索匹配的是**标签/概念**（语义/值形态/基数/版式），不是字段名——字段名千变万化，标签与概念稳定。

### 6.1 字段语义概念状态机

```text
concept:  candidate ──► validated ──► superseded
               │
               └──► rejected（误归并/语义错误，作负例，防误迁移）
```

- 新概念（或已有概念的新别名实例）先 `candidate`，**不参与正式检索**（避免污染推荐）。
- 升级门槛（建议）：`candidate → validated` 需 ≥2 条来自不同单据的 Case 支撑，或 1 条 Case + 人工确认。
- 上报与审核：消费方上报新字段/新概念，memory 侧人工审核入库（双向，核心不依赖单一消费方）。

### 6.2 未覆盖字段处理链路

新单据字段在词典中无匹配时的分流（详见 `field-semantics.md` §未覆盖）：

1. 三路匹配（别名/值形态/向量 0.75）高置信命中 → 归一化到概念。
2. 向量近邻但语义不同 → 输出**易混警示**，不迁移。
3. 完全未覆盖 → 标记 unknown + 走默认 SOP + 人工确认 + 记入 pending 队列；训练后验证稳定再上报为 candidate 概念，走 4.1 状态机。
