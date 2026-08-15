# 机制层（Mechanism）Schema 设计

> 状态：设计稿，待确认后落地。
> 动机：当前经验归纳只有「Case → Claim」两层，导致同一个优化机制（如"漏行"）在货描/非货描下被切成多条 Claim，且字段类型划分一旦变更，Claim 的适用条件就失效。加一层机制层，把「跨字段类型的稳定方案」和「字段类型划分」解耦。

## 1. 问题：Claim 被字段类型切碎

现在 26 条 Claim 里，"漏行"这个机制在 goods 和非 goods 下各一条（或各带 lane 条件），本质是**同一个机制的两个实例**。字段类型（lane/标注范围）是易变的划分，不该作为经验归纳的主键。

## 2. 三层对象模型

```
EvidenceEvent（证据事件，不可变）
  └─ ExperienceCase（案例：单次观察，绑证据）
       多案例聚合 ──► PatternClaim（实例：机制在某字段类型下的适用，有状态机）
                       多实例归纳 ──► Mechanism（机制：跨字段类型稳定，有结构前提）
```

职责划分：

| 层 | 粒度 | 触发条件 | 稳定性 |
|---|---|---|---|
| **Mechanism** | 跨字段类型 | 稳定结构属性（基数/值形态/版式/跨页） | 稳定 |
| **Claim** | 字段类型级 | when（含易变 lane/doc_types/languages） | 中 |
| **Case** | 字段级 | 无（绑具体证据） | 事实 |

核心：**机制层只基于稳定的结构属性归纳，不碰易变的字段类型标签**。这样字段类型划分怎么变，机制层都不动。

## 3. Mechanism 对象 schema

```yaml
mechanism_id*: MECH-0001                       # 单值，唯一标识
name*: 行级归组字段漏行                         # 机制名（人读）
problem_mechanism*: >                           # 问题机制（稳定本质，不含字段类型）
  行级归组字段在密集跨页表格中因分段/边界处理不当导致漏行
intervention*: >                                # 统一干预方案（跨字段类型通用）
  长表分段 + 行级守恒 + 连续重叠 core
structural_preconditions*:                      # 稳定结构前提（触发机制的稳定属性）
  cardinality: [grouped_value]                  # 基数（字段是行级归组）
  value_shape: []                               # 值形态（空 = 不限）
  layout: [dense_table, long_table]             # 版式结构
  cross_page: true                              # 是否跨页
claims*: [CLAIM-0001, CLAIM-0002]               # 机制的各字段类型实例（引用）
cases*: [CASE-0001, CASE-0002, ...]             # 归纳证据（引用）
status: active | merged | superseded            # 机制状态（比 Claim 状态机简单）
confidence: high | medium | low                 # 归纳置信度
created_at: 2026-08-15
updated_at: 2026-08-15
```

字段图例同 schema.md（`*` = 必填）。

关键点：
- `structural_preconditions` 是机制层与实例层的分水岭——它**只含稳定结构属性**（cardinality/value_shape/layout/cross_page），**不含** lane/doc_types/languages 这些易变维度。
- `claims` 挂载实例：每个 Claim 是机制在某字段类型下的适用，含易变维度（when.lane 等）。
- `status` 只有 active/merged/superseded：机制是归纳结果，不是待验证干预，不需要 candidate/validated 那套状态机。

## 4. PatternClaim 的改动

Claim 加一个字段指向归属机制：

```yaml
mechanism_id: MECH-0001   # 归属机制（可空；单机制未归纳时 null）
```

其余字段不变。Claim 的 `when`（lane/doc_types/languages）仍是机制下的**实例化条件**。

## 5. 检索流程变化

```
画像（字段 → 概念 + 结构属性：基数/值形态/版式）
  → ① 命中 Mechanism：structural_preconditions AND 匹配（稳定属性）
  → ② 在命中的 Mechanism 下，用易变维度（when.lane/doc_types）定位 Claim 实例
  → ③ 三种结果：
       a. 命中实例 → 推荐具体 Claim（现有逻辑）
       b. 命中机制但无匹配实例 → 推荐机制 + 标注「此机制在 X 字段类型验证过，
          当前字段类型无验证实例，谨慎」（机制层兜底新字段类型）
       c. 机制和实例都不中 → 回退默认 SOP
```

机制层最大的增量价值是 **③b**：新字段类型（如 lane 新增第三类）来了，稳定机制还能兜底，只是提示"无当前类型的验证实例"。

## 6. 字段类型变更的应对（结合机制层）

| 变更 | 处置 | 动的层 |
|---|---|---|
| 字段重新归类（某字段 goods→non_goods） | 只改 Taxonomy 的字段→类型映射 | Taxonomy |
| lane 划分变更（二分→三分） | Taxonomy 枚举变更；重新评估 Claim 的 `when.lane` 引用 | Taxonomy + Claim 引用 |
| 机制本体 | **不动**（基于稳定结构属性，不依赖字段类型） | 无 |

所以字段类型变更的代价被压到最小：机制层零改动，只动 Taxonomy 映射 + Claim 引用。

## 7. 落地步骤（待确认）

1. **schema.md**：加 Mechanism 对象 + 三层对象模型；Claim 加 `mechanism_id`。
2. **抽机制**：把 26 条 Claim 按 `problem_mechanism` + `intervention` 聚类，抽出 MECH-* 机制（预计 10~15 个），每条 Claim 挂 `mechanism_id`。
3. **数据落库**：`phase2/data/mechanisms.json` + 同步 Claim。
4. **retriever**：实现「① 命中机制 → ② 定位实例 → ③ 三结果」的检索链。
5. **建议卡**：展示命中机制 + 实例 + "无实例兜底"标注。

## 8. 待确认的决策点

1. **机制粒度**：抽多粗？建议按"干预方案"聚类（同干预方案 = 同机制），而非按问题表象。
2. **机制状态**：active/merged/superseded 是否够？是否需要 `deprecated`（机制被新机制取代）。
3. **③b 兜底**：命中机制但无实例时，是直接推荐机制，还是只提示不推荐（更保守）？
