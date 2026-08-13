# 字段语义词典初版（v1）

> 日期：2026-08-13 ｜ 状态：初版（candidate，待人工确认后 validated）
> 一手来源（A800 `/data/sam/Qwen2.5-VL-main`）：
> - `analysis_outputs/20260805_full_field_contract_audit.md`（全字段合同审计）
> - `analysis_outputs/20260805_field_contract_confirmation.md`（字段合同最终确认单，方案 A）
> - `DataPrepare/system_prompt_all_en_zh_merge_1126.py`（`hm_alias` 别名表 + `pl_prompt_field` 字段全集说明）

## 0. 定位

L3 字段层匹配的**目标空间**：新单据的字段名/字段说明/样本值 → 归一化到本词典的 canonical 字段 → 迁移该字段的历史经验。三路匹配（别名表 / 值形态启发 / 语义向量）都以本词典为锚。

**初版范围**：以装箱单（最难单据）字段全集为核心 + 8 类单据合同差异为补充；其余 9 类单据的字段说明后续按同法补齐。

## 1. canonical 字段表

### 1.1 货描明细字段（进入 group，按行提取）

| canonical | 中文 | 别名/定位词 | 值形态 | 基数 | 易混 |
|---|---|---|---|---|---|
| `item_no` | 序号 | item_no | numeric_value | single_value（逐行） | product_no, product_code |
| `product_no` | 产品编号 | product_no | code_value | single_value | item_no, goods_name |
| `product_code` | 商品编码 | Product Code | code_value | single_value（逐行） | item_no |
| `goods_name` | 商品名称 | Description of Goods / Commodity / bl_goods_name | long_text | single_value（逻辑实体优先拆分） | product_no |
| `goods_quantity` | 货物数量 | QTY / Quantity / PCS / goods_qty / bl_qty_of_goods / count_of_goods | numeric_value | single_value（逐行） | goods_carton/parcel/pallet |
| `goods_carton` | 装箱数量 | Cartons / CTNS | numeric_value | single_value（逐行） | goods_quantity |
| `goods_parcel` | 包裹数量 | Packages / Pkgs / Bales / bundle | numeric_value | single_value（逐行） | goods_quantity |
| `goods_pallet` | 托盘数量 | pallet / drum | numeric_value | single_value（逐行） | goods_quantity |
| `goods_gross_weight` | 货物毛重 | Gross Weight / G.W. | numeric_unit | single_value（逐行） | goods_net_weight, total_gross_weight |
| `goods_net_weight` | 货物净重 | Net Weight / N.W. | numeric_unit | single_value（逐行） | goods_gross_weight, total_net_weight |
| `goods_weight` | 货物重量（未指明毛净） | Weight / KGS / MT（无 GW/NW 提示） | numeric_unit | single_value（逐行） | goods_gross/net_weight |
| `goods_measurement` | 商品体积 | Measurement / CBM | numeric_unit | single_value（逐行） | — |
| `price_of_goods` | 单价 | goods_price / price_of_goods | currency_amount | single_value（逐行） | goods_amount |
| `goods_amount` | 商品金额小计 | Amount | currency_amount | single_value（逐行） | price_of_goods, total_amount |

### 1.2 表头单位字段（非 group，列表）

`goods_qty_title_unit` / `goods_weight_title_unit` / `goods_gross_weight_title_unit` / `goods_net_weight_title_unit` / `goods_carton_title_unit` / `goods_pallet_title_unit` / `goods_parcel_title_unit`。全部 `numeric_unit`（单位文本），仅取表头，不投影到行值。

### 1.3 汇总字段（非 group，列表）

| canonical | 中文 | 定位词 | 值形态 |
|---|---|---|---|
| `subtotal` | 金额小计 | Sub Total | currency_amount |
| `total_amount` | 商品总金额 | Total / Total Amount | currency_amount |
| `total_amount_upper` | 大写总金额 | SAY / ONLY | long_text |
| `total_gross_weight` | 毛重总计 | Total（毛重列底部） | numeric_unit |
| `total_net_weight` | 净重总计 | Total（净重列底部） | numeric_unit |
| `total_qty` | 数量总计 | Total（数量列底部） | numeric_value |

### 1.4 独立字段（非 group）

| canonical | 中文 | 定位词 | 值形态 | 基数 |
|---|---|---|---|---|
| `currency` | 币种 | 跟随金额（三位代码 USD，无代码用 $） | currency_amount | single/multi |
| `container_no` | 集装箱编号 | Container No / Container Id | code_value | multi |
| `seal_no` | 铅封号 | Seal No | code_value | multi |
| `shipping_marks` | 唛头 | Shipping Marks / Marks | long_text | multi |
| `hs_code` | HS 编码 | HS Code | code_value | multi |
| `size` | 尺寸（长宽高） | Size / Dimension / MEAS | numeric_unit | multi（全局，即使表格内） |

### 1.5 非货描字段（party/地址/银行/运输/日期/编号，摘要）

| 类 | 字段 |
|---|---|
| 当事人 | buyer(买方)/seller(卖方)/consignee(收货方)/shipper(发货方)/factory(制造商)/beneficiary(受益人)/issuer(出具人)/carrier(承运人) |
| 地址 | buyer_address/seller_address/consignee_address/shipper_address/factory_address/collection_point(+_address)/beneficiary_bank_address |
| 银行 | beneficiary_bank/beneficiary_account/swift_code/payment_info/payment_company |
| 运输 | port_of_loading(发货港)/port_of_discharge(目的港)/port_of_transhipment(中转港)/vessel_name/flight_no/bl_no/incoterm |
| 日期 | invoice_date/issue_date/shipment_date/flight_date/delivery_date/payment_due_date |
| 编号 | invoice_number/order_number/contract_no/pi_number/packing_list_no/certificate_no/reference/our_reference_no/deliver_order_no/subcontract_no |
| 条款 | payment_term/payment_terms_tenor/country_of_origin/packaging_method |

## 2. 别名表（canonical → 别名，取自 `hm_alias`）

```yaml
goods_name: [bl_goods_name, goods_name]
goods_quantity: [goods_qty, bl_qty_of_goods, count_of_goods]
price_of_goods: [goods_price, price_of_goods]
# 中英别名（非货描）：
buyer: [buyer_zh, buyer_en, buyer]
consignee: [ship_to_zh, consignee_zh, ship_to_en, consignee_en]
seller: [seller, seller_zh, seller_en, title_seller_zh, title_seller_en, title_company]
shipper: [shipper_zh, shipper_en]
beneficiary: [beneficiary_zh, beneficiary_en]
factory: [factory_zh, factory_en]
# 反向索引 hm[v] → canonical（用于匹配时归一化）
```

## 3. 值形态规则（从字段合同审计提炼）

### 3.1 币种规则

- 金额/单价与币种在**同一原文值/同一单元格**时，币种**必须保留**（`USD535.00` 不能去 USD）。
- `currency` 是整单独立字段，不与行内币种互斥；**禁止把全局/表头币种投影到每行**。
- 反例（已确认 contract 冲突）：销售合同/借记/贷记/提货/销售订单的 Gold 曾删行内币种，导致 exact 判错——去掉 USD 前缀后 amount F1 0.4211→1.0000。

### 3.2 单位规则（方案 A：严格表头优先）

- 表头单位 → `goods_*_title_unit`，**不投影到行值**。
- 行内单位随值保留（`30 箱` 单位在行内 → 保留；纯数字 `1/2/3` 单位只在表头 → 不投影）。
- 字段路由顺序：**显式字段/表头 → 表格列归属 → 同行语义 → 单位 taxonomy 兜底**。

### 3.3 重量三分法

- `goods_gross_weight`（毛重）/ `goods_net_weight`（净重）/ `goods_weight`（未指明毛净重）三选一。
- 有明确 GW/NW 时**绝对不提取** `goods_weight`；gross/net 严格排除单件（Unit G.W./Unit N.W.）与皮重（Tare Weight）。

### 3.4 数量/包装四字段边界

- `goods_quantity` = 商品总件数（QTY/Quantity/PCS），排除内包装数量（Inner Qty）、长度/面积/体积。
- `goods_carton` = 箱数；`goods_parcel` = 包裹数；`goods_pallet` = 托盘数。
- 表头优先下：`Quantity` 列里的值即使带 BAGS/LB/KGS/MT/CTNS 也进 `goods_quantity`（形式发票 `1,392 BAGS`、提货单 `11,000.00Lb`）。
- 包装字段由**显式包装表头**决定（Carton/Parcel/Pallet），单位词不覆盖表头（海运单 `200 CTNS` 在 `QUANTITY:` 后仍归 quantity）。

### 3.5 负号规则

- 贷记通知单 `goods_amount`/`goods_quantity`/`total_amount` 保留负号（已对齐，非主因）。

### 3.6 容差规则

- 容差（`±2%`）只跟随**直接相连的明细/汇总值**进入对应字段；合同段落的全局容差**不复制到每行**。

### 3.7 品名规则

- `goods_name` 按单据固定"**核心品名**"（销售合同只留品名，丢规格尺寸）或"完整描述"，两个相反目标需在数据集/评估中分别固定。
- 排除独立列的型号/规格参数；同一单元格内不同逻辑实体需拆分。

## 4. 易混字段对（跨单据警示）

| 易混对 | 区分依据 |
|---|---|
| item_no ↔ product_no ↔ product_code | 序号 / 产品编号 / 商品编码（Product Code 表头）；复杂 SKU/型号进 product_no 或 product_code，不进 item_no |
| goods_quantity ↔ goods_carton/parcel/pallet | 总件数 vs 包装数，靠表头（QTY vs Cartons/Packages/Pallet） |
| goods_gross_weight ↔ goods_net_weight ↔ goods_weight | 毛/净/未指明，靠 GW/NW 提示词 |
| goods_*_weight ↔ total_*_weight | 行级（group）vs 整单汇总（Total 底部），Subtotal 属行级大类 |
| goods_amount ↔ price_of_goods ↔ total_amount | 金额小计 / 单价 / 整单总额 |
| goods_name ↔ product_no | 品名 vs 产品号 |
| invoice_number ↔ packing_list_no ↔ pi_number | 发票号 / 装箱单号 / 形式发票号（共用编号时装箱单优先） |
| invoice_date ↔ issue_date ↔ shipment_date ↔ delivery_date ↔ flight_date | 各类日期靠引导词区分 |
| buyer ↔ consignee | 买方 vs 收货方（ship to / Consignee） |
| seller ↔ shipper ↔ issuer ↔ title_company | 卖方 vs 发货方 vs 出具人 vs 顶部标题公司 |
| order_number ↔ contract_no ↔ deliver_order_no | 订单号 / 合同号 / 交货单号 |
| reference ↔ our_reference_no | 参考号 vs 卖方内部参考号 |
| port_of_loading ↔ port_of_discharge ↔ port_of_transhipment | 发货港 / 目的港 / 中转港 |

## 5. 与能力标签的映射

本词典字段 → `capability-tags.md` 标签的对应（供检索时双路命中）：

- `goods_quantity`/`goods_carton`/`goods_parcel`/`goods_pallet` → `quantity` + `numeric_value` + `grouped_value`
- `goods_gross_weight`/`goods_net_weight`/`goods_weight`/`size`/`goods_measurement` → `weight`/`size` + `numeric_unit`
- `goods_amount`/`price_of_goods`/`total_amount`/`currency` → `monetary` + `currency_amount`
- `product_no`/`product_code`/`item_no` → `identifier` + `code_value`
- `goods_name` → `item` + `long_text`

## 6. 待补（后续切片）

1. 其余 9 类单据（ci/bl/air/po/cr/dbn/sdn/pi/do/swb/sc/so/crn/aco）的 `*_prompt_field` 字段说明逐一并入。
2. `alias_map`（per doc_type 的字段别名差异，约 1350 行）——尤其海运单 packages/ctns 多层语义、销售订单 product_code 等单据级规则。
3. 值形态启发规则（编号/金额/日期/名称的正则判别）正式化。
