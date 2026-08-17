# 字段语义概念映射与状态说明

> 供提取自然语言字段时查用。完整概念见 `scripts/data/concepts.json`（85 个 canonical 概念）。

## 1. 单据类型 → doc_type

> 版式索引覆盖 14 类单据（表中 ✅ 标注，2026-08-17 起 ci/bl/air/pi/sc/po 已补）；索引未覆盖时脚本会提示并跳过版式视觉确认（仅按声明类型匹配，非报错）。

| 用户说法 | doc_type | 版式索引 |
|---|---|---|
| 装箱单 / packing list | `packing_list` | ✅ |
| 商业发票 / invoice / CI | `commercial_invoice` | ✅ |
| 提单 / bill of lading / BL | `bill_of_lading` | ✅ |
| 海运单 / sea waybill / SWB | `sea_waybill` | ✅ |
| 航空单 / air waybill | `air_waybill` | ✅ |
| 形式发票 / proforma invoice / PI | `proforma_invoice` | ✅ |
| 销售订单 / sales order / SO | `sales_order` | ✅ |
| 销售合同 / sales contract / SC | `sales_contract` | ✅ |
| 购买订单 / purchase order / PO | `purchase_order` | ✅ |
| 贷记通知 / credit note / CR | `credit_note` | ✅ |
| 借记通知 / debit note / DB | `debit_note` | ✅ |
| 提货单 / delivery order / DO | `delivery_order` | ✅ |
| 发货单 / shipping note / SDN | `shipping_note` | ✅ |
| 出口托收 / aco | `aco` | ✅ |

> 注意：提单（BL）与海运单（SWB）是两种不同单据，勿混淆。

## 2. 语义 → 字段名（常见别名）

| 语义 | 常见字段名 / 别名 |
|---|---|
| 数量 | `goods_quantity` / `quantity` / `qty` / `total_qty` |
| 金额 / 单价 | `goods_amount` / `amount` / `goods_price` / `price_of_goods` / `total_amount` |
| 币种 | `currency` / `document_currency` |
| 品名 / 货描 | `goods_name` / `name` |
| 毛重 | `goods_gross_weight` / `gross_weight` / `gw` |
| 净重 | `goods_net_weight` / `net_weight` / `nw` |
| 尺寸 / 体积 | `size` / `measurement` / `cbm` |
| 箱数 / 件数 | `goods_carton` / `goods_parcel` / `carton` / `parcel` |
| 买方 | `buyer` |
| 卖方 | `seller` / `title_company` |
| 收货方 | `consignee` |
| 发货方 | `shipper` |
| 收款行 | `beneficiary_bank` |
| 账号 | `beneficiary_account` |
| 开证行 | `issue_bank` / `issuing_bank` |
| 发票号 | `invoice_no` / `invoice_number` |
| 订单号 | `order_no` / `order_number` |
| 提单号 | `bl_no` / `bl_id` |
| 集装箱号 | `container_no` |
| 铅封号 | `seal_no` |
| HS 编码 | `hs_code` |
| 港口 / 船名 / 航班 | `port_of_loading` / `vessel_name` / `flight_no` |
| 日期 | `issue_date` / `invoice_date` / `shipment_date` / `delivery_date` |

## 3. 样例值 → 值形态启发（自动）

| 样例值 | 自动判定 |
|---|---|
| `USD 535.00` / `$535` | `currency_amount`（金额） |
| `2026-03-25` / `25 MAR 2026` | `date_value`（日期） |
| `1,392 KGS` / `10 CTN` | `numeric_unit`（数值+单位） |
| `1,392` | `numeric_value`（纯数值） |
| `INV-2026-001` / `SKU-88231` | `code_value`（编号） |

## 4. Claim 状态含义（转述给用户时用）

| 状态 | 含义 | 转述口径 |
|---|---|---|
| `validated` | 干预验证通过（7 项全过） | 「这条经验经过了验证」 |
| `confirmed` | 归因/诊断确认（结论可信，干预未验证） | 「这条结论可信，但干预效果还没验证」 |
| `candidate` | 待验证候选 | 「这是候选经验，仅供参考」 |

## 5. 检索逻辑（简要）

1. 字段名 → 别名表命中 → canonical 概念 → 语义标签（数量/金额/当事人/银行/编号/重量/尺寸/运输/日期…）。
2. 聚合标签集合 vs 每条 Claim 的 `capability_tags` 求交集 → 打分排序。
3. 值形态过滤：`grouped_value` 经验不推荐给 `single_value` 字段。
4. 版式标签从 doc_type 粗推（`packing_list`→密集表格+长表）。
5. 完全无命中 → 回退默认 SOP。
