# 首批 PatternClaim（9 条）

> 日期：2026-08-13 ｜ 状态：首批（candidate / validated，依历史证据强度区分；见 schema 状态机）
> `supported_by` 指向 `experience-cases.md`；`capability_tags` 见 `capability-tags.md`。

---

## CLAIM-0001 行级归组数量字段在密集跨页表格易漏行

```yaml
claim_id: CLAIM-0001
status: candidate            # 问题已量化确认，干预在多案例上未验证
capability_tags:
  semantic: [quantity]
  value_shape: [numeric_value]
  cardinality: [grouped_value, row_aligned, cross_page_group]
  layout: [dense_table, long_table]
problem_pattern: 行级归组数量字段（goods_quantity）在密集跨页表格易漏行（row_delta<0）
intervention_strategy: 长表分段 + 行级守恒 + 连续重叠 core；推理用无标签 planner 切窗
applicability:
  preconditions: [行级归组的数量字段, 密集表格, 可能跨页]
  contraindications: [单值字段不适用, 短表（<10 行）收益有限]
  confidence: medium
  transfer_level: mechanism   # 字段不同但"行级归组数量"机制相同即可迁移
supported_by: [CASE-0001]
outcome_aggregate: {typical_delta: 装箱单 goods F1 0.6598~0.6744 仍为最低, cost_range: 未知, stability: 未知}
```

## CLAIM-0002 归组字段在长表易重复 group / 相邻列串位

```yaml
claim_id: CLAIM-0002
status: candidate
capability_tags:
  semantic: [quantity, parcel]
  value_shape: [numeric_value]
  cardinality: [grouped_value, row_aligned, multi_value]
  layout: [dense_table, long_table]
problem_pattern: 归组字段在长表易重复 group（168 事件）+ 相邻数值列串位（386 事件）
intervention_strategy: 行对齐 + 连续重叠 core + 槽位去重（字段/文本/空间位置约束）
applicability:
  preconditions: [多数值列密集表格, 行级归组]
  contraindications: [单列数值表不适用, 字段间语义距离远时串位风险低]
  confidence: medium
  transfer_level: mechanism
supported_by: [CASE-0002, CASE-0003]
outcome_aggregate: {typical_delta: 串位为保守下界 386 事件, cost_range: 未知, stability: 未知}
```

## CLAIM-0003 尺寸/重量标题单位字段易错配

```yaml
claim_id: CLAIM-0003
status: candidate
capability_tags:
  semantic: [size, weight, unit]
  value_shape: [numeric_unit]
  cardinality: [single_value, multi_value]
  layout: [dense_table, multi_block]
problem_pattern: 尺寸（size）与重量标题单位（gross/net weight title unit）字段在装箱单 non_goods 高频错配
intervention_strategy: 单位独立建模（数值与单位解耦）+ 标题单位专项样本
applicability:
  preconditions: [数值+单位字段, 标题与数值分离的版式]
  contraindications: [无单位字段不适用]
  confidence: medium
  transfer_level: structural
supported_by: [CASE-0004, CASE-0005]
outcome_aggregate: {typical_delta: size 30.6% / gross+net 单位 440 错误, cost_range: 未知, stability: 未知}
```

## CLAIM-0004 训练 batch 过大 + LR 不匹配导致输出坍缩

```yaml
claim_id: CLAIM-0004
status: validated            # 历史多轮稳定主线，坍缩可复现且切回后消除
capability_tags:
  semantic: []
  value_shape: []
  cardinality: []
  layout: []
problem_pattern: GB512 后期输出坍缩（ckpt80 全 0）；sqrt LR 缩放无收益
intervention_strategy: GB256 + LR2e-4 稳定主线；避免盲目放大 batch 与 sqrt LR 缩放
applicability:
  preconditions: [Qwen3-VL-32B-AWQ + LoRA 类训练]
  contraindications: [其他模型规模/训练栈需重新验证]
  confidence: high
  transfer_level: context
supported_by: [CASE-0006]
outcome_aggregate: {typical_delta: 坍缩消除, cost_range: 8*A800, stability: 多轮稳定}
```

## CLAIM-0005 金额字段需 value 去币种 + currency 独立

```yaml
claim_id: CLAIM-0005
status: validated            # amount F1 0.4211→1.0000，纯格式归因清晰
capability_tags:
  semantic: [monetary, unit]
  value_shape: [currency_amount]
  cardinality: [single_value]
  layout: [labeled_value]
problem_pattern: 币种混入 value 导致 exact 判错（纯格式问题非模型进步）
intervention_strategy: value 去币种 + currency 独立 + bbox 保留；训练/测试/repair 同一清洗函数
applicability:
  preconditions: [金额字段含币种符号]
  contraindications: [币种在训练目标内需单独评估]
  confidence: high
  transfer_level: direct
supported_by: [CASE-0007]
outcome_aggregate: {typical_delta: amount F1 +0.5789, cost_range: 低, stability: 高}
```

## CLAIM-0006 推理运行时版本影响 bbox 定位

```yaml
claim_id: CLAIM-0006
status: validated            # IoU 0.068→0.747，归因清晰
capability_tags:
  semantic: []
  value_shape: []
  cardinality: [per_value_bbox]
  layout: []
problem_pattern: vLLM 版本与 LoRA 模块加载直接影响 bbox（0.16 no-tower 0.747 vs 0.21 tower 0.068）
intervention_strategy: 固定 vLLM 版本 + language-only QLoRA（显式 target 语言层）；训练/评估/推理运行时同合同
applicability:
  preconditions: [需要 bbox 定位的任务]
  contraindications: [纯文本抽取无 bbox 需求时影响小]
  confidence: high
  transfer_level: context
supported_by: [CASE-0008]
outcome_aggregate: {typical_delta: IoU +0.679, cost_range: 低, stability: 高}
```

## CLAIM-0007 标识/低频字段需专项增强

```yaml
claim_id: CLAIM-0007
status: candidate
capability_tags:
  semantic: [identifier, parcel]
  value_shape: [code_value, numeric_value]
  cardinality: [single_value, multi_value]
  layout: [dense_table]
problem_pattern: 标识字段（product_no）与低频字段（goods_parcel）漏抽严重
intervention_strategy: targeted 增强 + 低频字段受控上采样（标记来源 score_note）+ 字段配额 + floor 保护
applicability:
  preconditions: [低频有值字段, 标识类字段]
  contraindications: [高频字段过度上采样会样本膨胀]
  confidence: medium
  transfer_level: structural
supported_by: [CASE-0009, CASE-0012]
outcome_aggregate: {typical_delta: product_no F1 0.3509 / parcel 有值样本→34%, cost_range: 中, stability: 未验证}
```

## CLAIM-0008 评估需 cluster 整簇留出 + ID/OOD 双评

```yaml
claim_id: CLAIM-0008
status: validated            # ID/OOD/OOD-tail 三区全正 + family bootstrap 区间为正
capability_tags:
  semantic: []
  value_shape: []
  cardinality: []
  layout: [cross_page]
problem_pattern: 随机图片切分无法回答版式泛化（内容级 train/test 重叠）
intervention_strategy: cluster 整簇留出 + ID/OOD-core/OOD-tail 三区评测 + family bootstrap + 泄漏闭包（SHA/像素 SHA/感知 hash/family/cluster）
applicability:
  preconditions: [有 cluster/family 元数据的数据集]
  contraindications: [无版式聚类元数据时需先补聚类]
  confidence: high
  transfer_level: context
supported_by: [CASE-0010]
outcome_aggregate: {typical_delta: goods micro F1 +0.2412, cost_range: 低, stability: 高}
```

## CLAIM-0009 评估字段面必须四方对齐

```yaml
claim_id: CLAIM-0009
status: validated            # round1 contaminated → round2 valid_eval，流程修复验证
capability_tags:
  semantic: []
  value_shape: []
  cardinality: []
  layout: []
problem_pattern: prompt/训练标签/Gold/evaluator 字段面不一致导致评估污染
intervention_strategy: 字段面四方对齐 + 训练排除字段不入评估 + test lock 四状态（valid_eval/contaminated/contract 失效/证据不足）
applicability:
  preconditions: [任何字段级 KIE 评估]
  contraindications: [无]
  confidence: high
  transfer_level: context
supported_by: [CASE-0011]
outcome_aggregate: {typical_delta: 污染结果只作历史追溯, cost_range: 低, stability: 高}
```
