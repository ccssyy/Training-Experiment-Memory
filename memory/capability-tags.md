# 通用能力标签初版（v1）

> 日期：2026-08-13 ｜ 状态：初版（candidate，待人工确认后 validated 进正式索引）
> 来源：`07-colleague-synthesis.md` §1.2 的 4 类标签体系，结合 Qwen 真实字段/版式落地。

标签是检索键，**与字段名解耦**。检索顺序（同事方案）：字段语义 → 值形态 → 基数 → 粒度 → 字段关系 → bbox → 页面版式 → 单据类型 → 模型/prompt/evaluator。

## 1. 语义 semantic（字段"是什么"）

| 标签 | 含义 | Qwen 对应字段示例 |
|---|---|---|
| `quantity` | 数量 | goods_quantity, total_qty, item_no |
| `monetary` | 金额 | goods_amount, total_amount |
| `weight` | 重量（含单位） | goods_gross_weight, goods_net_weight, gross/net weight title unit |
| `size` | 尺寸/规格 | size |
| `parcel` | 件数/包装数 | goods_parcel, goods_carton |
| `identifier` | 标识/编号 | product_no, item_no, order_no, invoice_no, container_no |
| `item` | 品名/货物描述 | goods_name（长文本） |
| `party` | 当事人 | buyer/seller/consignee/shipper/factory/beneficiary/carrier |
| `address` | 地址 | buyer_address, consignee_address |
| `temporal` | 时间 | issue_date, shipment_date, invoice_date |
| `unit` | 单位（独立于数值） | currency, weight_unit |
| `status` | 状态 | 单据状态、字段是否存在 |
| `transport` | 运输 | port_of_loading/discharge, vessel_name, flight_no, awb, voyage |
| `location` | 地点（非运输） | country_of_origin/origin, place_of_delivery/receipt |
| `bank` | 银行 | beneficiary_bank, issue_bank, swift_code, bank account |
| `payment` | 付款 | payment_term, payment_info, financing |
| `term` | 单据条款/元数据项 | incoterm, freight, declared_value, signature, packaging, title, remarks, doc.count |

## 2. 值形态 value_shape（字段值"长什么样"）

| 标签 | 含义 |
|---|---|
| `numeric_value` | 纯数值（数量、编号） |
| `numeric_unit` | 数值 + 单位（重量、尺寸，单位错配是装箱单高频失败） |
| `currency_amount` | 金额（币种 + 数值，币种混入 value 是纯格式判错主因） |
| `code_value` | 编码值（product_no/item_no 易混） |
| `date_value` | 日期值 |
| `short_text` | 短文本（名称、当事人） |
| `long_text` | 长文本（goods_name 长货描） |
| `mixed_value` | 混合值（文本 + 数字混杂） |

## 3. 基数/关系 cardinality（字段值"几个、怎么排"）

| 标签 | 含义 |
|---|---|
| `single_value` | 单值字段（一个字段一个值） |
| `multi_value` | 多值字段（一个字段多个值） |
| `grouped_value` | 归组字段（货描明细按行归组：name/quantity/… 组内多字段） |
| `row_aligned` | 行对齐（组内字段按行对齐，行错位是装箱单第一大失败） |
| `cross_page_group` | 跨页归组（明细跨页连续性） |
| `one_to_many` | 一对多关系（单据头 → 多明细行） |
| `per_value_bbox` | 每个值独立 bbox（逐值定位需求） |

## 4. 版式视觉 layout（页面"长什么样"）

| 标签 | 含义 |
|---|---|
| `dense_table` | 密集表格（装箱单核心版式） |
| `long_table` | 长表（≥10 行，需分段训练） |
| `multi_block` | 多区块（多区域版式，角色字段易混淆） |
| `labeled_value` | 标签-值对（标题 + 值） |
| `cross_page` | 跨页 |
| `rotated` | 旋转版式 |
| `handwritten` | 手写 |
| `stamped` | 印章 |

## 5. 标签演化规则

- 本表所有标签状态 = `candidate`；经人工确认后 `validated` 进正式索引。
- 新标签由画像引擎/消费方上报，人工审核入库。
- 匹配时 `grouped_value` 经验不推荐给 `single_value` 字段（值形态不匹配直接过滤）。
