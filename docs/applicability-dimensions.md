# 结构化适用性判别维度（经验可采纳/不适用判定）

> 日期：2026-08-14 ｜ 状态：定稿（schema 升级 + 检索器判定 + 版式向量接入）
> 目标：把 PatternClaim 的「可采纳/不适用」条件从自由文本升级为机器可判定的结构化维度，并接入真实版式向量。

## 1. 判别维度全景（10 维）

| 层 | 维度 | 取值 | 来源 |
|---|---|---|---|
| 字段层 | 语义标签 | `semantic`（quantity/monetary/party/bank/…） | capability_tags.semantic |
| 字段层 | 值形态 | `value_shape`（numeric_value/currency_amount/…） | capability_tags.value_shape |
| 字段层 | 基数 | `cardinality`（single/grouped/row_aligned/…） | capability_tags.cardinality |
| 字段层 | 字段分布 | `support_min` / `pos_ratio_min`（样本量/正负比） | **新增** |
| 单据层 | 单据类型 | `doc_types`（packing_list/…） | **新增** |
| 单据层 | 单据版式 | `layout`（dense_table/…）+ 视觉向量 | capability_tags.layout + **embedding 向量** |
| 任务层 | lane | `goods` / `non_goods` | **新增（一级判别）** |
| 任务层 | 语言 | `zh` / `en` / `zh_en` | **新增** |
| 数据层 | 数据规模 | `data_scale.min_samples` | **新增** |
| 时效层 | 有效期 | `expires_at` | **新增（过期降级）** |

## 2. applicability 结构化 schema

```yaml
applicability:
  when:                              # 可采纳条件：AND，全部满足才推荐
    lane: [goods]                    # 一级判别（货描/非货描迁移能力不同）
    languages: [zh, en, zh_en]       # 语言
    doc_types: [packing_list]        # 单据类型
    cardinality: [grouped_value]     # 字段基数
    value_shape: [numeric_value]     # 值形态
    layout: [dense_table, long_table]  # 版式（标签级）
    distribution:                    # 字段分布门槛（可选）
      support_min: 20
    data_scale:                      # 数据规模（可选）
      min_samples: 2000
  contraindications:                 # 不适用：OR，命中任一条即降权/过滤
    - when: {lane: non_goods}
      reason: 非货描迁移能力弱，本经验仅货描验证过
    - when: {cardinality: single_value}
      reason: 单值字段不适用，本经验针对行级归组
  confidence: high | medium | low
  transfer_level: direct | structural | mechanism | context
  expires_at: 2026-12-31            # 可选，过期降级为 observed
```

**判定逻辑**：
- `when` 全部命中 → 可采纳；`contraindications` 命中任一条 → 不适用（过滤或显著降权）。
- 画像里缺失某维度（如未提供语言/数据规模）→ 该维度**不参与判定**（宽松通过），不因缺数据而误拒。

## 3. 版式向量接入点

版式维度分两级：
- **标签级**（零 GPU）：`layout` 标签（dense_table/long_table/…），doc_type 粗推兜底。
- **向量级**（需 GPU）：新任务样例图 → 调 embedding 服务（公网 9030）→ 2048 维版式向量 → 与历史经验的版式锚比余弦相似度。

接入方式：`profiler` 增加可选 `image_path` + `embedding_server` 参数。提供则走向量级，不提供则回退标签级。**保持零 GPU 的规则画像可用**。

## 4. 与现有 capability_tags 的关系

- `capability_tags` 是**检索键**（命中用）：semantic/value_shape/cardinality/layout。
- `applicability.when` 是**适用判定**（命中后细化）：复用 cardinality/value_shape/layout，新增 lane/languages/doc_types/distribution/data_scale。
- 两者不重复存储——`when` 里的 cardinality/value_shape/layout 从 capability_tags 派生，仅 `when` 独有的（lane/languages/doc_types/distribution/data_scale）需显式补。

## 5. 实施顺序

1. schema.md 升级 applicability 定义（本文档即依据）。
2. profiler 加版式向量路（可选 fallback）。
3. retriever 实现 when AND / contraindications OR 判定。
4. 26 条 Claim applicability 重标（补 lane/languages/doc_types + 结构化 contraindications）。
