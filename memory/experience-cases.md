# 首批 ExperienceCase（32 条）

> 日期：2026-08-13 ｜ 状态：首批（candidate，待 Phase 1 交叉验证后确认）
> 证据来源：`docs/performance/`、`[知识库]/04_Registries/`、`analysis_outputs/`（路径均为 A800 上 `[Qwen训练仓库]` 相对路径）；CASE-0013 起来源为同事 `non_goods_round3_analysis` 包；CASE-0019 起为 coding-brain Registry（4-5 月早期训练）。

---

## CASE-0001 装箱单 goods 明细行漏构造

```yaml
case_id: CASE-0001
run_ref: round2 formal eval（10 类单据，goods 501 请求）
fields: [goods_quantity, goods_name, product_no, goods_parcel, goods_carton]
layout: {document_type: packing_list, cluster: pl_mixed, page_role: dense_table}
problem:
  pattern_id: PL-ROW-UNDERCOUNT
  symptom_metric: row_delta<0 占 84/202 样本（明细行漏构造）；goods_quantity FP/FN=339/1045
intervention: 无（本 case 为失败观察）
outcome:
  baseline_ref: null
  delta: {goods F1: 0.6598, lane 错误占比 78.0%}
  protected_regression: null
evidence_refs:
  - docs/performance/2026-07-14-round2-10docs-badcase-analysis.md
  - docs/performance/2026-07-30-round5-and-7docs-cluster-id-ood-results.md
provenance: {source_revisions: [round2 frozen formal eval], decision_ref: null, created_at: 2026-08-13}
```

## CASE-0002 装箱单重复 group

```yaml
case_id: CASE-0002
run_ref: round2 formal eval（装箱单 202 样本）
fields: [goods_name, goods_quantity]
layout: {document_type: packing_list, cluster: pl_mixed, page_role: dense_table}
problem:
  pattern_id: PL-REPEATED-GROUP
  symptom_metric: 20/202 样本出现 168 个重复 group 事件
intervention: 无（失败观察）
outcome:
  baseline_ref: null
  delta: {重复 group 事件: 168}
  protected_regression: null
evidence_refs:
  - docs/performance/2026-07-14-round2-10docs-badcase-analysis.md
provenance: {source_revisions: [round2 frozen formal eval], decision_ref: null, created_at: 2026-08-13}
```

## CASE-0003 装箱单相邻数值列串位

```yaml
case_id: CASE-0003
run_ref: round2 formal eval（装箱单 202 样本）
fields: [goods_quantity, goods_carton, goods_parcel]
layout: {document_type: packing_list, cluster: pl_mixed, page_role: dense_table}
problem:
  pattern_id: PL-COLUMN-SLOT-SHIFT
  symptom_metric: 87/202 样本命中 386 个保守槽位串位事件（预测值命中相邻列 GT）
intervention: 无（失败观察）
outcome:
  baseline_ref: null
  delta: {槽位串位事件: 386}
  protected_regression: null
evidence_refs:
  - docs/performance/2026-07-14-round2-10docs-badcase-analysis.md
provenance: {source_revisions: [round2 frozen formal eval], decision_ref: null, created_at: 2026-08-13}
```

## CASE-0004 装箱单 non_goods size 字段高错误

```yaml
case_id: CASE-0004
run_ref: round2 formal eval（non_goods 514 请求）
fields: [size]
layout: {document_type: packing_list, cluster: pl_mixed, page_role: dense_table}
problem:
  pattern_id: PL-SIZE-MISMATCH
  symptom_metric: size 单字段 826 个错误（FP/FN=612/214），占装箱单 non_goods 错误 30.6%
intervention: 无（失败观察）
outcome:
  baseline_ref: null
  delta: {size 错误: 826/2695}
  protected_regression: null
evidence_refs:
  - docs/performance/2026-07-14-round2-10docs-badcase-analysis.md
provenance: {source_revisions: [round2 frozen formal eval], decision_ref: null, created_at: 2026-08-13}
```

## CASE-0005 装箱单重量标题单位错配

```yaml
case_id: CASE-0005
run_ref: round2 formal eval（non_goods）
fields: [goods_gross_weight_title_unit, goods_net_weight_title_unit]
layout: {document_type: packing_list, cluster: pl_mixed, page_role: dense_table}
problem:
  pattern_id: PL-WEIGHT-UNIT-MISMATCH
  symptom_metric: gross 标题单位 237 错误（FP/FN=106/131），net 203 错误（FP/FN=82/121）
intervention: 无（失败观察）
outcome:
  baseline_ref: null
  delta: {gross+net 标题单位错误: 440}
  protected_regression: null
evidence_refs:
  - docs/performance/2026-07-14-round2-10docs-badcase-analysis.md
provenance: {source_revisions: [round2 frozen formal eval], decision_ref: null, created_at: 2026-08-13}
```

## CASE-0006 GB512 后期输出坍缩

```yaml
case_id: CASE-0006
run_ref: 6other_po0512 GB512 实验（ckpt80）
fields: []
layout: {document_type: mixed, cluster: null, page_role: null}
problem:
  pattern_id: PL-OUTPUT-COLLAPSE
  symptom_metric: GB512 后期 checkpoint80 输出全 0；sqrt LR 缩放无收益
intervention: 切回 GB256 + LR2e-4 主线
outcome:
  baseline_ref: GB256 主线
  delta: {坍缩消除}
  protected_regression: null
evidence_refs:
  - docs/performance/2026-05-16-6other-po0512-phase2-hg-gb512-lr-control.md
  - docs/performance/2026-05-16-6other-po0512-regen-formal-gb-lr-scaling.md
provenance: {source_revisions: [6other po0512], decision_ref: null, created_at: 2026-08-13}
```

## CASE-0007 销售合同金额清洗（币种与 value 分离）

```yaml
case_id: CASE-0007
run_ref: 销售合同金额清洗实验
fields: [goods_amount, currency]
layout: {document_type: sales_contract, cluster: sc_mixed, page_role: labeled_value}
problem:
  pattern_id: PL-CURRENCY-IN-VALUE
  symptom_metric: value 内混币种导致 exact 判错（纯格式问题非模型进步）
intervention: value 去币种 + currency 独立 + bbox 保留；训练/测试/repair 同一清洗函数
outcome:
  baseline_ref: 清洗前
  delta: {amount F1: 0.4211 → 1.0000}
  protected_regression: null
evidence_refs:
  - docs/performance/2026-07-09-10newdocs-19docs-field-exact-indexes.md
provenance: {source_revisions: [销售合同清洗], decision_ref: null, created_at: 2026-08-13}
```

## CASE-0008 vLLM 版本影响 bbox 定位

```yaml
case_id: CASE-0008
run_ref: exp6 awq vs bf16/bnb bbox 对比
fields: [bbox 相关字段]
layout: {document_type: mixed, cluster: null, page_role: null}
problem:
  pattern_id: PL-RUNTIME-BBOX-DRIFT
  symptom_metric: vLLM 0.16 no-tower IoU 0.747 vs 0.21 tower-enabled 0.068
intervention: 固定 vLLM 版本 + 显式 target 语言层（language-only QLoRA）
outcome:
  baseline_ref: vLLM 0.21 tower-enabled
  delta: {IoU: 0.068 → 0.747}
  protected_regression: null
evidence_refs:
  - runs/20260609_exp6_awq_vs_bf16_bnb_bbox_comparison
provenance: {source_revisions: [exp6 bbox 对比], decision_ref: null, created_at: 2026-08-13}
```

## CASE-0009 CI product_no 严重漏抽

```yaml
case_id: CASE-0009
run_ref: 商业发票（CI）货描评测
fields: [product_no]
layout: {document_type: commercial_invoice, cluster: ci, page_role: dense_table}
problem:
  pattern_id: PL-IDENTIFIER-UNDEREXTRACT
  symptom_metric: product_no F1 0.3509（严重漏抽）
intervention: targeted 增强 + product_no 专项（待验证）
outcome:
  baseline_ref: null
  delta: {product_no F1: 0.3509}
  protected_regression: null
evidence_refs:
  - docs/performance/2026-07-22-round2-10docs-document-field-metrics.md
provenance: {source_revisions: [CI 货描评测], decision_ref: null, created_at: 2026-08-13}
```

## CASE-0010 7docs cluster 整簇留出 ID/OOD 双评

```yaml
case_id: CASE-0010
run_ref: 7docs 旁路实验（487 训练图）
fields: []
layout: {document_type: mixed_7docs, cluster: id/ood_core/ood_tail, page_role: null}
problem:
  pattern_id: PL-RANDOM-SPLIT-OVERESTIMATE
  symptom_metric: 随机图片切分无法回答版式泛化
intervention: cluster 整簇留出 + ID/OOD-core/OOD-tail 三区评测 + family bootstrap
outcome:
  baseline_ref: Base（AWQ）
  delta: {goods micro F1: 0.3951 → 0.6363, 三区全正；non_goods 0.4314 → 0.4963}
  protected_regression: null
evidence_refs:
  - docs/performance/2026-07-30-round5-and-7docs-cluster-id-ood-results.md
provenance: {source_revisions: [7docs 旁路], decision_ref: null, created_at: 2026-08-13}
```

## CASE-0011 round1 字段面四方不对齐 → 评估污染

```yaml
case_id: CASE-0011
run_ref: round1 10 新单据
fields: [9 个训练排除字段]
layout: {document_type: mixed, cluster: null, page_role: null}
problem:
  pattern_id: PL-FIELD-CONTRACT-MISALIGN
  symptom_metric: 9 个训练排除字段仍进入评估 → 整体判 contaminated
intervention: 字段面四方对齐（prompt/训练标签/Gold/evaluator 一致）
outcome:
  baseline_ref: null
  delta: {round1 判 contaminated，不作 baseline}
  protected_regression: null
evidence_refs:
  - docs/performance/2026-07-14-round2-10docs-badcase-analysis.md
provenance: {source_revisions: [round1], decision_ref: null, created_at: 2026-08-13}
```

## CASE-0012 CR goods_parcel 低频字段漏抽

```yaml
case_id: CASE-0012
run_ref: 贷记通知单（CR）货描评测
fields: [goods_parcel]
layout: {document_type: credit_note, cluster: crn, page_role: dense_table}
problem:
  pattern_id: PL-LOWFREQ-FIELD-UNDEREXTRACT
  symptom_metric: goods_parcel 有值样本低频（support 15 波动大）；5x 上采样后 322→1610 有值样本
intervention: 低频字段 5x 上采样（有值样本）
outcome:
  baseline_ref: null
  delta: {有值样本占比 → 约 34%}
  protected_regression: 未验证副作用
evidence_refs:
  - [知识库]/04_Registries/Issue Registry.md（ISS-20260428-cr-parcel-lowfreq）
  - [知识库]/04_Registries/Metric Registry.md
provenance: {source_revisions: [CR parcel 5x], decision_ref: null, created_at: 2026-08-13}
```

---

## 以下 CASE-0013~0018 来源：同事 non_goods round3 分析包（checkpoint-342）

## CASE-0013 non_goods 多字段同值冒充（跨字段复用同值同 bbox）

```yaml
case_id: CASE-0013
run_ref: round3 non-goods checkpoint-342（vLLM 0.16 no-tower 双 LoRA）
fields: [issuing_bank, available_with, collection_bank_nan, beneficiary_bank, beneficiary_account, reference, order_number, document_no, reference_no, swb_id]
layout: {document_type: mixed_non_goods, cluster: null, page_role: multi_block}
problem:
  pattern_id: NG-SAME-VALUE-CROSS-FIELD
  symptom_metric: 多字段输出完全相同的值+bbox——aco issuing_bank=available_with=collection_bank_nan(BANK OF NINGBO)；pi beneficiary_bank=beneficiary_account(同一 IBAN)；pi reference=order_number(PO-BC-001024)；swb document_no=reference_no=swb_id(NAM7900733)
intervention: 无（失败观察）
outcome:
  baseline_ref: null
  delta: {round3 non-goods F1: 0.8044}
  protected_regression: null
evidence_refs:
  - records/round3_badcase_recheck/report.md（逐图判定：1649d108/61b23e31/9ace41a4/0144fb97 明确复现）
  - records/round3_eval/ROUND3_HANDOFF.md
provenance: {source_revisions: [20260717_cluster_8to2_v1 test], decision_ref: null, created_at: 2026-08-13}
```

## CASE-0014 checkbox/份数字段幻觉（无值输出 0 或错误值）

```yaml
case_id: CASE-0014
run_ref: round3 non-goods checkpoint-342
fields: [certification_of_origi, original_bl, commercial_invoice, customs_invoice, insurance_policy, draft]
layout: {document_type: aco, cluster: null, page_role: multi_block}
problem:
  pattern_id: NG-CHECKBOX-HALLUCINATION
  symptom_metric: 份数/checkbox 字段错配——certification_of_origi=B/L、original_bl=125100148...；多个缺失/checkbox 字段输出 0，违背"无值不出 key"
intervention: 无（失败观察）
outcome:
  baseline_ref: null
  delta: {aco F1: 0.8565, badcase 522 行}
  protected_regression: null
evidence_refs:
  - records/round3_badcase_recheck/report.md（0885e398 部分复现）
  - records/round3_eval/ROUND3_HANDOFF.md（aco 优先级 2）
provenance: {source_revisions: [20260717_cluster_8to2_v1 test], decision_ref: null, created_at: 2026-08-13}
```

## CASE-0015 形式发票漏 buyer/buyer_address（当事人混淆）

```yaml
case_id: CASE-0015
run_ref: round3 non-goods checkpoint-342
fields: [buyer, buyer_address, consignee, consignee_address]
layout: {document_type: proforma_invoice, cluster: pi, page_role: multi_block}
problem:
  pattern_id: NG-PARTY-OMISSION
  symptom_metric: 非货描输出无 buyer/buyer_address，只输出 consignee/consignee_address
intervention: 无（失败观察）
outcome:
  baseline_ref: null
  delta: {pi F1: 0.6320（10 单据最低）, badcase 158 行}
  protected_regression: null
evidence_refs:
  - records/round3_badcase_recheck/report.md（0b63a76d 明确复现）
  - records/round3_eval/ROUND3_HANDOFF.md（pi 优先级 4）
provenance: {source_revisions: [20260717_cluster_8to2_v1 test], decision_ref: null, created_at: 2026-08-13}
```

## CASE-0016 销售订单 group 缺 goods_name

```yaml
case_id: CASE-0016
run_ref: round3 non-goods checkpoint-342
fields: [goods_name]
layout: {document_type: sales_order, cluster: so, page_role: dense_table}
problem:
  pattern_id: NG-GROUP-FIELD-OMISSION
  symptom_metric: 10 个 group 全部缺少 goods_name（前两行漏抽，范围更大）
intervention: 无（失败观察）
outcome:
  baseline_ref: null
  delta: {so F1: 0.8575, badcase 112 行}
  protected_regression: null
evidence_refs:
  - records/round3_badcase_recheck/report.md（3471b630 部分复现）
provenance: {source_revisions: [20260717_cluster_8to2_v1 test], decision_ref: null, created_at: 2026-08-13}
```

## CASE-0017 多行单价漏归组

```yaml
case_id: CASE-0017
run_ref: round3 non-goods checkpoint-342
fields: [price_of_goods]
layout: {document_type: proforma_invoice, cluster: pi, page_role: dense_table}
problem:
  pattern_id: NG-PRICE-ROW-UNGROUPED
  symptom_metric: 4 条明细的 quantity/amount 已逐行抽取，但单价只输出 1 个独立 price_of_goods=USD 19.00，未逐行归组
intervention: 无（失败观察）
outcome:
  baseline_ref: null
  delta: null
  protected_regression: null
evidence_refs:
  - records/round3_badcase_recheck/report.md（33737a32 部分复现）
provenance: {source_revisions: [20260717_cluster_8to2_v1 test], decision_ref: null, created_at: 2026-08-13}
```

## CASE-0018 海运单字段幻觉（从错误区域取值）

```yaml
case_id: CASE-0018
run_ref: round3 non-goods checkpoint-342
fields: [freight_payable_at, document_no, container_no]
layout: {document_type: sea_waybill, cluster: swb, page_role: multi_block}
problem:
  pattern_id: NG-FIELD-HALLUCINATION
  symptom_metric: freight_payable_at=NAGOYA;JAPAN 从其他港口/地点区域冒出（图内 Freight Payable 区域无该值）；container_no 被 non-goods 同 bbox 复用为 document_no
intervention: 无（失败观察）
outcome:
  baseline_ref: null
  delta: {swb F1: 0.8213, badcase 301 行}
  protected_regression: null
evidence_refs:
  - records/round3_badcase_recheck/report.md（020223e3/07944f15 部分复现）
  - records/round3_eval/ROUND3_HANDOFF.md（swb 优先级 3）
provenance: {source_revisions: [20260717_cluster_8to2_v1 test], decision_ref: null, created_at: 2026-08-13}
```

---

## 以下 CASE-0019~0024 来源：coding-brain Registry（4-5 月早期训练）

## CASE-0019 空输出来源二分（选错字段 vs 真实负样本）

```yaml
case_id: CASE-0019
run_ref: EXP-20260421-empty-source-split
fields: [goods_name, 空输出相关字段]
layout: {document_type: mixed_5goods, cluster: null, page_role: null}
problem:
  pattern_id: PL-EMPTY-OUTPUT-SOURCE
  symptom_metric: 空输出需二分——CI 总空 1073（830 选错字段/243 真无货）；BL 1185（845/340）；Air 459（430/29）；PO 131（9/122）；CR 420（0/420）
intervention: 区分"选错字段"（加字段锚点）vs"真实负样本"（控比例）
outcome:
  baseline_ref: null
  delta: {可避免比例: CI 77% / BL 71% / Air 94% / PO 7% / CR 0%}
  protected_regression: null
evidence_refs:
  - [知识库]/04_Registries/Experiment Registry.md（EXP-20260421-empty-source-split）
  - [知识库]/04_Registries/Metric Registry.md
provenance: {source_revisions: [0414_5_goods], decision_ref: null, created_at: 2026-08-13}
```

## CASE-0020 BL group 标注口径迁移导致指标下降

```yaml
case_id: CASE-0020
run_ref: EXP-20260507-bl-group-regression
fields: [goods_name, goods_weight, goods_parcel, goods_quantity]
layout: {document_type: bill_of_lading, cluster: bl, page_role: dense_table}
problem:
  pattern_id: PL-LABEL-CALIBER-SHIFT
  symptom_metric: BL F1 0.7606→0.6960；行项目字段下降，goods_name 略升——根因是 group 标注口径从旧合并 group 迁移到真实多 group，非全局 OCR 退化
intervention: 不回退 group 修复，转向 targeted 增强 + 字段配额
outcome:
  baseline_ref: 0427 BL
  delta: {BL F1: -0.0646（口径迁移，非退化）}
  protected_regression: null
evidence_refs:
  - [知识库]/04_Registries/Experiment Registry.md（EXP-20260507-bl-group-regression）
provenance: {source_revisions: [0427/0506 BL], decision_ref: null, created_at: 2026-08-13}
```

## CASE-0021 late checkpoint 不一定更好

```yaml
case_id: CASE-0021
run_ref: exp4 5goods checkpoint selection
fields: []
layout: {document_type: mixed_5goods, cluster: null, page_role: null}
problem:
  pattern_id: PL-LATE-CKPT-RISK
  symptom_metric: ckpt1015 macro 0.8537 推荐；ckpt1575 只高 0.0007 但带风险标记；ckpt1295 macro 0.8318 负面选点（不如 ep9/ep9.67 稳）
intervention: 密集保存 + 多 checkpoint 评估 + 0.003 平局阈值 + 风险标记
outcome:
  baseline_ref: null
  delta: {ckpt1015 macro F1: 0.8537, weighted 0.8081}
  protected_regression: null
evidence_refs:
  - [知识库]/04_Registries/Model Registry.md
  - docs/performance/2026-05-12-exp4-best-checkpoint-selection.md
provenance: {source_revisions: [exp4 5goods], decision_ref: null, created_at: 2026-08-13}
```

## CASE-0022 页眉/letterhead 卖方抬头是当事人坏例集中模式

```yaml
case_id: CASE-0022
run_ref: EXP-20260508-target-field-review
fields: [seller]
layout: {document_type: mixed_6other, cluster: null, page_role: letterhead}
problem:
  pattern_id: NG-LETTERHEAD-PARTY
  symptom_metric: 目标字段坏例 82 张中，seller 页眉/左上 logo 或 letterhead 卖方抬头 45/82
intervention: 版式/公司频次用于 prompt 或样本修复
outcome:
  baseline_ref: null
  delta: {letterhead 卖方抬头: 45/82}
  protected_regression: null
evidence_refs:
  - [知识库]/04_Registries/Experiment Registry.md（EXP-20260508-target-field-review）
provenance: {source_revisions: [0506_6_others], decision_ref: null, created_at: 2026-08-13}
```

## CASE-0023 跨硬件训练吞吐分层

```yaml
case_id: CASE-0023
run_ref: EXP-20260509-bw1000-a800-throughput
fields: []
layout: {document_type: mixed_5goods, cluster: null, page_role: null}
problem:
  pattern_id: PL-CROSS-HW-THROUGHPUT
  symptom_metric: BW1000 4 卡 0.729 samples/s vs A800 0.911 samples/s，约 A800 80%
intervention: 结论分层表达"可正确训练但不等价"，主训练前需优化复测
outcome:
  baseline_ref: A800 4 卡
  delta: {BW1000 吞吐: A800 的 80%}
  protected_regression: null
evidence_refs:
  - [知识库]/04_Registries/Training Run Registry.md
  - [知识库]/04_Registries/Decision Registry.md（跨硬件分层表达）
provenance: {source_revisions: [0428 五类货描], decision_ref: null, created_at: 2026-08-13}
```

## CASE-0024 样本贡献比失衡导致低占比单据被淹没

```yaml
case_id: CASE-0024
run_ref: EXP-20260423-5goods-balance
fields: []
layout: {document_type: mixed_5goods, cluster: null, page_role: null}
problem:
  pattern_id: PL-SAMPLE-IMBALANCE
  symptom_metric: 五类货描样本贡献比 14.3:1，PO/Air 被淹没
intervention: 平衡到 2.3:1（CI 7936/BL 6271/Air 4026/PO 3509/CR 3452）
outcome:
  baseline_ref: 0414 失衡
  delta: {贡献比: 14.3:1 → 2.3:1}
  protected_regression: 未验证模型指标
evidence_refs:
  - [知识库]/04_Registries/Experiment Registry.md（EXP-20260423-5goods-balance）
  - [知识库]/04_Registries/Dataset Registry.md
provenance: {source_revisions: [0423_5_goods_balanced], decision_ref: null, created_at: 2026-08-13}
```

---

## 以下 CASE-0025~0028 来源：session-digests（训练前置/数据工程方法论）

## CASE-0025 badcase 分类法（7 类错误 + 训练侧三分）

```yaml
case_id: CASE-0025
run_ref: exp5 badcase taxonomy（checkpoint-1015）
fields: [goods_weight, goods_parcel, goods_quantity, goods_name, product_no, item_no]
layout: {document_type: mixed_5goods, cluster: null, page_role: null}
problem:
  pattern_id: PL-BADCASE-TAXONOMY
  symptom_metric: 167 条复核中漏抽 102 / 误抽 5 / 字段混淆 9 / 边界错误 12 / OCR 规范化 7 / 标签问题 32；仅看 CSV 无法区分这些
intervention: 固定 7 类错误枚举（漏抽/误抽/字段混淆/边界/OCR/标签问题/只监控）+ 图片/GT/Predict/bbox 联合复核 + 训练侧三分（train yes 134 / review 32 / no 1）
outcome:
  baseline_ref: checkpoint-1015
  delta: {漏抽占比: 61.1%, 标签问题: 19.2%}
  protected_regression: null
evidence_refs:
  - [Qwen训练仓库]/docs/performance/2026-05-13-exp5-multimodal-badcase-taxonomy.md
provenance: {source_revisions: [exp5 badcase taxonomy], decision_ref: null, created_at: 2026-08-13}
```

## CASE-0026 测试 badcase 去测试化后才能入训

```yaml
case_id: CASE-0026
run_ref: exp5 badcase taxonomy 决策
fields: []
layout: {document_type: mixed_5goods, cluster: null, page_role: null}
problem:
  pattern_id: PL-BADCASE-DECONTAMINATE
  symptom_metric: 标准测试集 badcase 若直接入训会造成泄漏；但全丢弃又浪费诊断价值
intervention: 测试 badcase 只用于诊断和规则归纳，转成"去测试化的版式/字段模式"入训，不直接回灌测试图片
outcome:
  baseline_ref: null
  delta: {入训原则: 去测试化模式，非原图}
  protected_regression: null
evidence_refs:
  - [Qwen训练仓库]/docs/performance/2026-05-13-exp5-multimodal-badcase-taxonomy.md
provenance: {source_revisions: [exp5 badcase taxonomy], decision_ref: null, created_at: 2026-08-13}
```

## CASE-0027 JSONL 行数不等于唯一图片数

```yaml
case_id: CASE-0027
run_ref: training-preflight-lessons
fields: []
layout: {document_type: mixed, cluster: null, page_role: null}
problem:
  pattern_id: PL-ROW-VS-IMAGE-COUNT
  symptom_metric: mode 扩展、负样本、上采样会让 JSONL 行数膨胀，误当图片数导致数据 admission 误判
intervention: 数据 admission 区分 row count 与 unique image count，manifest 核对以实际图片数为准
outcome:
  baseline_ref: null
  delta: null
  protected_regression: null
evidence_refs:
  - [Qwen训练仓库]/docs/data/2026-08-05-training-preflight-lessons.md
provenance: {source_revisions: [training-preflight-lessons], decision_ref: null, created_at: 2026-08-13}
```

## CASE-0028 训练前置门禁链（8 门禁 + 顺序）

```yaml
case_id: CASE-0028
run_ref: training-preflight-lessons
fields: []
layout: {document_type: mixed, cluster: null, page_role: null}
problem:
  pattern_id: PL-PREFLIGHT-GATES
  symptom_metric: 数据/生成/运行/训练问题事后无法分离，误归因模型训练（泄漏、字段面漂移、运行时挂载、checkpoint 误判混杂）
intervention: 8 门禁顺序执行——SourceSnapshot → SplitPlanner → FieldContractGate → DistributionAudit → DataAdmissionGate → TestLock → RuntimeReceipt → CheckpointGate
outcome:
  baseline_ref: null
  delta: {门禁候选: 8 个 ATF 需求}
  protected_regression: null
evidence_refs:
  - [Qwen训练仓库]/docs/data/2026-08-05-training-preflight-lessons.md
provenance: {source_revisions: [training-preflight-lessons], decision_ref: null, created_at: 2026-08-13}
```

---

## 以下 CASE-0029~0032 来源：round5 完整归档 + round3 训练包 digest

## CASE-0029 非货描 ID/OOD 迁移弱于货描

```yaml
case_id: CASE-0029
run_ref: 20260728_7docs_cluster_id_ood_pilot_v1
fields: [total_net_weight, total_gross_weight]
layout: {document_type: mixed_7docs, cluster: id/ood_core/ood_tail, page_role: null}
problem:
  pattern_id: PL-LANE-MIGRATION-ASYMMETRY
  symptom_metric: 货描 micro F1 +0.2412 全分区提升无单据回退；非货描只 +0.0649，召回 0.5982→0.5643，提货单 0.4372→0.3333，重量字段回退
intervention: 无（观察，lane 迁移能力不对称）
outcome:
  baseline_ref: base 模型
  delta: {货描: +0.2412, 非货描: +0.0649, 非货描召回: -0.0339}
  protected_regression: 非货描重量字段/提货单回退
evidence_refs:
  - [Qwen训练仓库]/docs/performance/2026-08-04-10docs-bypass-id-ood-complete-experiment-archive.md
provenance: {source_revisions: [7docs id/ood pilot data_v2], decision_ref: null, created_at: 2026-08-13}
```

## CASE-0030 content-level 重叠导致指标只能标 as-run

```yaml
case_id: CASE-0030
run_ref: 5goods-exp5 / 6other-exp4 完整归档
fields: []
layout: {document_type: mixed, cluster: null, page_role: null}
problem:
  pattern_id: PL-CONTENT-LEVEL-OVERLAP
  symptom_metric: 两组 source snapshot 存在"同图片内容、不同文件名/标签序列化"重叠——货描 75/482、非货描 65/485
intervention: 历史指标标注 as-run 口径，不当严格无泄漏泛化指标
outcome:
  baseline_ref: null
  delta: {重叠: 货描 75/482, 非货描 65/485}
  protected_regression: null
evidence_refs:
  - [Qwen训练仓库]/docs/performance/2026-08-04-5goods-exp5-and-6other-exp4-complete-experiment-archive.md
provenance: {source_revisions: [exp5/exp4 archive], decision_ref: null, created_at: 2026-08-13}
```

## CASE-0031 训练配置单点断言失效（fail-open）

```yaml
case_id: CASE-0031
run_ref: round3-training-package-invariant
fields: []
layout: {document_type: mixed, cluster: null, page_role: null}
problem:
  pattern_id: PL-CONFIG-DRIFT-FAIL-OPEN
  symptom_metric: goods video_max_pixels 从冻结 65536 漂移为 65516，旧 targeted test 仍 1 passed（只抽查少数 flag）
intervention: package-level 白名单残差比较 + 17 项负例矩阵（RED 1 failed → GREEN 20 passed）
outcome:
  baseline_ref: 第二轮 package
  delta: {负例矩阵: 17 项, 测试: 20 passed}
  protected_regression: null
evidence_refs:
  - round3-training-package-invariant.md（session-digest）
provenance: {source_revisions: [round3 training package], decision_ref: null, created_at: 2026-08-13}
```

## CASE-0032 多机 smoke 合同传播遗漏 + launcher/child 身份分叉

```yaml
case_id: CASE-0032
run_ref: round3-smoke-launch-contract + goods-smoke-mode-identity
fields: []
layout: {document_type: mixed, cluster: null, page_role: null}
problem:
  pattern_id: PL-MULTINODE-CONTRACT-PROPAGATION
  symptom_metric: non_goods coordinator 未把 one-step/SwanLab/resume/端口传给 remote rank；goods launcher 与 child 各自派生 output 路径，dry plan 与实际 preflight 不一致
intervention: RUN_MODE 状态机 + remote rank 合同传播 + launcher/child 单一 resolver + collision guard（168→181 passed）
outcome:
  baseline_ref: null
  delta: {测试: 181 passed, 负例: 13 失败→通过}
  protected_regression: null
evidence_refs:
  - round3-smoke-launch-contract.md（session-digest）
  - round3-goods-smoke-mode-identity.md（session-digest）
provenance: {source_revisions: [round3 training package], decision_ref: null, created_at: 2026-08-13}
```
