# 字段语义词典（v2：三层通用结构，全单据重做）

> 日期：2026-08-13 ｜ 状态：candidate（待人工确认）
> **覆盖**：16 个单据（早期 6 种：商业发票 ci / 提单 bl / 航空单 air / 贷款申请书 loan / 购买订单 po / 货物收据 cr + 第二批 10 种：借记通知单 dbn / 发货单 sdn / 形式发票 pi / 提货单 do / 海运单 swb / 出口托收申请书 aco / 装箱单 pl / 贷记通知单 crn / 销售合同 sc / 销售订单 so），**298 个字段名归并为 85 个 canonical 语义概念**。
> **来源**：`system_prompt_all_en_zh_merge_1126.py`（16 个 `*_prompt_field` + `alias_map` + `all_keys_group_map` 解析）+ `20260805_full_field_contract_audit.md` 值形态规则。

## 0. 三层结构

```
canonical 语义概念（通用，跨单据稳定）   ← 检索键之一，与能力标签互补
        ▲ 字段名实例（别名）挂载
字段名实例（各单据的命名：goods_quantity / gross_weight / total_pieces / 件数 …）
        ▲ 值形态规则
值形态规则（挂概念：币种保留 / 表头优先 / 重量三分法 …）
```

新单据字段匹配路径：字段名 + 说明 + 样例值 → 三路匹配（别名表/值形态启发/向量）→ 归一化到概念 → 打能力标签 → 命中 Claim。
**概念层是通用的；字段名只是"该概念在某单据的实例"。**

## 1. canonical 语义概念全集

记号：`字段名(出现单据数)`；`@单据` = 仅该单据特有命名；`→` 后为值形态规则编号（§3）。

### 1.1 货描明细概念（goods_group 内，按行提取）

| # | 概念 | 中文 | 字段名实例 | 值形态 | 易混 |
|---|---|---|---|---|---|
| 1 | `quantity` | 货物数量 | goods_quantity(14); goods_qty, bl_qty_of_goods, count_of_goods(旧别名); total_pieces, no_of_pieces@air; total_quantity@cr | numeric_value，→R2 | carton/parcel/pallet |
| 2 | `name` | 商品名称 | goods_name(14); bl_goods_name(旧别名); goods_description@aco; goods_services_description@loan | long_text，→R7 | product_no |
| 3 | `item_no` | 序号 | item_no(9) | numeric_value | product_no, product_code |
| 4 | `product_no` | 产品编号 | product_no(7); product_code@so; job_no@crn/dbn/sc | code_value | item_no |
| 5 | `carton` | 装箱数 | goods_carton(12) | numeric_value | quantity |
| 6 | `parcel` | 包裹数 | goods_parcel(12) | numeric_value | quantity |
| 7 | `pallet` | 托盘数 | goods_pallet(9) | numeric_value | quantity |
| 8 | `weight.gross` | 毛重 | goods_gross_weight(9); gross_weight@air | numeric_unit，→R3 | weight.net / total.weight.gross |
| 9 | `weight.net` | 净重 | goods_net_weight(9); net_weight@air | numeric_unit，→R3 | weight.gross / total.weight.net |
| 10 | `weight.unspecified` | 重量（未指明毛净） | goods_weight(6) | numeric_unit，→R3 | weight.gross/net |
| 11 | `measurement` | 体积 | goods_measurement@bl/swb | numeric_unit | — |
| 12 | `price` | 单价 | goods_price@crn/dbn/po/sc/so; price_of_goods@ci/do/pi/pl | currency_amount，→R1/R6 | amount |
| 13 | `amount` | 金额小计 | goods_amount(9); dc_amount@cr/sdn; document_amount@loan | currency_amount，→R1/R5/R6 | price / total.amount |

### 1.2 汇总概念（non_goods_group，整单/整页）

| # | 概念 | 中文 | 字段名实例 | 值形态 |
|---|---|---|---|---|
| 14 | `subtotal` | 金额小计 | subtotal(9) | currency_amount |
| 15 | `total.amount` | 总金额 | total_amount(9); total_value@cr/sdn; amount_of_documer@aco | currency_amount，→R1 |
| 16 | `total.amount.upper` | 大写总额 | total_amount_upper@do/pi/pl; total_value_upper@cr/sdn | long_text |
| 17 | `total.qty` | 数量总计 | total_qty(10); total_quantity@cr/sdn | numeric_value |
| 18 | `total.weight.gross` | 毛重总计 | total_gross_weight(10); total_weight@bl/do/pl/swb | numeric_unit |
| 19 | `total.weight.net` | 净重总计 | total_net_weight(10) | numeric_unit |

### 1.3 独立/单据级概念

| # | 概念 | 中文 | 字段名实例 | 值形态 |
|---|---|---|---|---|
| 20 | `currency` | 币种 | currency(9); document_currency@loan; local_currency@aco | currency_amount，→R1 |
| 21 | `container` | 集装箱号 | container_no(9) | code_value |
| 22 | `container.count` | 集装箱数 | container_count@bl/swb | numeric_value |
| 23 | `seal` | 铅封号 | seal_no(9) | code_value |
| 24 | `marks` | 唛头 | shipping_marks(9) | long_text |
| 25 | `hs_code` | HS 编码 | hs_code(7) | code_value |
| 26 | `size` | 尺寸 | size@do/pl | numeric_unit |
| 27 | `title_unit` | 表头单位 | goods_qty_title_unit(9); goods_weight_title_unit(4); goods_gross/net/carton/pallet/parcel_title_unit@do/pl | numeric_unit，→R4 |

### 1.4 当事人概念

| # | 概念 | 中文 | 字段名实例 |
|---|---|---|---|
| 28 | `party.buyer` | 买方 | buyer(10); buyer_zh/buyer_en(别名); applicant_name@aco; efip@aco |
| 29 | `party.seller` | 卖方 | seller(9); seller_zh/en(别名); title_company@do/pi/pl/sdn; issuer@do/pl; issued_by@air |
| 30 | `party.consignee` | 收货方 | consignee(9); bl_consignee@bl; receiver@po/so; ship_to_*(别名) |
| 31 | `party.shipper` | 发货方 | shipper(9); bl_shipper@bl |
| 32 | `party.factory` | 制造商 | factory(7); manufacturer@po/so; manufacturer_address@crn/dbn/sc |
| 33 | `party.beneficiary` | 受益人 | beneficiary(9); beneficiary_name@aco |
| 34 | `party.carrier` | 承运人 | carrier(8); bl_carrier@bl; carrier_agent@air; forwarding_agent@bl/swb; agent_for_carrier@bl |
| 35 | `party.notify` | 通知方 | notify@air; bl_notify_party@bl |
| 36 | `party.drawee` | 付款人 | drawee_name@aco |
| 37 | `party.contact` | 联系人 | buyer_contact(9); seller_contact(7); contact_person; contact_agent@aco; beneficiary_contact@aco; buyer_tel@po/so |

### 1.5 地址概念

| # | 概念 | 中文 | 字段名实例 |
|---|---|---|---|
| 38 | `address` | 地址（挂 party） | buyer_address(10); seller_address(9); consignee_address(8); shipper_address(8); factory_address(4); beneficiary_address(3); supplier_address(3); manufacturer_address(3); receiver_address@po/so; notify_address@air; bl_notify_party_address@bl; forwarding_agent_address@bl/swb; collection_point_address(7); issued_by_address@air; carrier_agent_address@air; drawee_address@aco |

### 1.6 银行概念

| # | 概念 | 中文 | 字段名实例 |
|---|---|---|---|
| 39 | `bank.beneficiary` | 收款行 | beneficiary_bank(6); beneficiary_bank_en(别名) |
| 40 | `bank.account` | 账号 | beneficiary_account(6); applicant_account_no@aco; export_account_no@aco; credit_account@aco; debit_account*@aco |
| 41 | `bank.issuing` | 开证行 | issue_bank@cr/sdn; issuing_bank@aco; available_with@aco; credit_available_witt@aco |
| 42 | `bank.collection` | 代收行 | collection_bank_nan/adc@aco |
| 43 | `bank.intermediary` | 代理行 | intermediary_bank_name, intermediary_bank_swift_code |
| 44 | `bank.swift` | SWIFT 代码 | swift_code(6) |

### 1.7 运输概念

| # | 概念 | 中文 | 字段名实例 |
|---|---|---|---|
| 45 | `port.loading` | 发货港 | port_of_loading(10); bl_port_of_loading@bl; airport_of_departure@air |
| 46 | `port.discharge` | 目的港 | port_of_discharge(10); bl_port_of_discharge@bl; airport_of_destination@air |
| 47 | `port.transhipment` | 中转港 | port_of_transhipment(6) |
| 48 | `place.delivery` | 交货地 | bl_place_of_delivery@bl; delivery_to@cr/sdn; final_destination@bl/swb; shipment_to@aco |
| 49 | `place.receipt` | 收货地 | bl_place_of_receipt@bl; delivery_from@cr/sdn; collection_point(7); shipment_from@aco |
| 50 | `vessel` | 船名 | vessel_name(7); vessel@loan/swb; bl_vessel@bl |
| 51 | `voyage` | 航程号 | bl_voyage_number@bl |
| 52 | `flight` | 航班号 | flight_no(6); flight_num@air |
| 53 | `awb` | 运单号 | awb/mawb/hawb@air; air_waybill@aco |

### 1.8 日期概念

| # | 概念 | 中文 | 字段名实例 |
|---|---|---|---|
| 54 | `date.issue` | 签发日期 | issue_date(9); bl_issue_date@bl; date@aco/loan |
| 55 | `date.invoice` | 开票日期 | invoice_date(6); invoice_due_date@loan |
| 56 | `date.shipment` | 装运日期 | shipment_date(7); bl_on_board_date@bl |
| 57 | `date.delivery` | 交货日期 | delivery_date(8) |
| 58 | `date.flight` | 航班日期 | flight_date(7) |
| 59 | `date.order` | 订单日期 | order_date(5) |
| 60 | `date.contract` | 合同日期 | contract_date(3) |
| 61 | `date.received` | 收到日期 | received_date@cr/sdn |
| 62 | `date.due` | 到期日 | payment_due_date(6); latest_repayment_date@loan |

### 1.9 编号概念

| # | 概念 | 中文 | 字段名实例 |
|---|---|---|---|
| 63 | `no.invoice` | 发票号 | invoice_number(6); invoice_no@bl/cr/sdn/swb |
| 64 | `no.order` | 订单号 | order_number(8); order_no@bl/swb |
| 65 | `no.contract` | 合同号 | contract_no(8) |
| 66 | `no.bl` | 提单号 | bl_no(7); bl_id@bl |
| 67 | `no.pi` | 形式发票号 | pi_number@do/pl; proforma_invoice_number(4) |
| 68 | `no.packing` | 装箱单号 | packing_list_no@do/pl |
| 69 | `no.lc` | 信用证号 | certificate_no(3); lc_number@bl; credit_no@aco; dc_no@cr/sdn; back_to_back_credi@aco |
| 70 | `no.reference` | 参考号 | reference(5); reference_no(8); our_reference_no(3); our_ref@aco; forward_contract_nc@aco |
| 71 | `no.deliver` | 交货单号 | deliver_order_no(3); dn_no@sdn |
| 72 | `no.document` | 单据号 | document_no(5); subcontract_no(4) |

### 1.10 条款/申报/其他概念

| # | 概念 | 中文 | 字段名实例 |
|---|---|---|---|
| 73 | `payment.term` | 付款条款 | payment_term(9); payment_terms_tenor(6); payment_method@po/so; payment_dp@aco |
| 74 | `payment.info` | 收款信息 | payment_info(6); payment_company(6) |
| 75 | `incoterm` | 贸易条款 | incoterm(10); icc_incoterms@aco |
| 76 | `freight` | 运费条款 | freight_payable_at@bl/swb; freight_payment_terms@bl; freight_repaid@air; wt_val_payment@air |
| 77 | `declared_value` | 申报价值 | declared_value@bl/swb; carriage_declared_value@air; customs_declared_value@air |
| 78 | `origin` | 原产国 | country_of_origin(6); origin@bl/swb |
| 79 | `signature` | 签章 | buyer_seal; seller_seal; shipper_signature@air; carrier_signature@air; carrier_signature_key@air; bl_seal@bl |
| 80 | `packaging` | 包装方式 | packaging_method@do/pl |
| 81 | `goods.attr` | 商品属性 | goods_color@po/so; brand_name@po/so |
| 82 | `title` | 单据标题 | title(7) |
| 83 | `remarks` | 备注说明 | remarks@po/so; handling_information@air; other_instructions@aco |
| 84 | `doc.count` | 随附单据份数 | insurance_policy/customs_invoice/original_bl/commercial_invoice@aco（份数类） |
| 85 | `financing` | 融资指示 | financing_required/financing_not_requir@aco; pre_shipment_financing@loan; fx_swap@aco; prepayment_or_purc@aco |

## 2. 值形态规则（挂概念，来源：字段合同审计 + 最终确认单）

| # | 规则 | 挂载概念 | 内容 |
|---|---|---|---|
| R1 | 币种保留 | price, amount, total.*, currency | 币种与数值同单元格/同原文值时**必须保留**；currency 为整单独立字段；禁止把全局/表头币种投影到每行。反例：销售合同去 USD 后 amount F1 0.4211→1.0000 |
| R2 | 数量表头优先 | quantity | 字段路由：显式表头 → 表格列归属 → 同行语义 → 单位兜底；Quantity/Qty 列的值即使带 BAGS/LB/KGS/MT 也归 quantity；排除内包装（Inner Qty）、长度/面积/体积 |
| R3 | 重量三分法 | weight.gross / net / unspecified | 有明确 GW/NW 时绝对不取 unspecified；gross/net 排除单件（Unit G.W./N.W.）与皮重（Tare） |
| R4 | 表头单位不投影 | title_unit | 单位只在表头 → 进 *_title_unit，不拼到行值；行内单位随值保留 |
| R5 | 负号保留 | amount（贷记） | 贷记通知单 goods_amount/goods_quantity/total_amount 保留负号 |
| R6 | 容差跟随 | price, amount | 容差只跟随直接相连的明细/汇总值；合同段落全局容差不复制到每行 |
| R7 | 品名单据化 | name | 按单据固定"核心品名"（销售合同丢规格）或"完整描述"；同一单元格不同逻辑实体拆分 |

## 3. 易混概念对（跨单据警示）

| 易混对 | 区分依据 |
|---|---|
| quantity ↔ carton/parcel/pallet | 总件数 vs 包装数，靠表头（QTY vs Cartons/Packages/Pallet） |
| item_no ↔ product_no ↔ product_code | 序号 / 产品编号 / 商品编码；复杂 SKU 进 product_no 或 product_code |
| weight.gross ↔ weight.net ↔ weight.unspecified | GW/NW 提示词 |
| weight.* ↔ total.weight.* | 行级（group）vs 整单汇总（Total 底部） |
| price ↔ amount ↔ total.amount | 单价 / 金额小计 / 总额 |
| no.invoice ↔ no.packing ↔ no.pi | 发票号 / 装箱单号 / 形式发票号（共用编号时装箱单优先） |
| party.buyer ↔ party.consignee | 买方 vs 收货方 |
| party.seller ↔ party.shipper | 卖方 vs 发货方（issuer/issued_by/title_company 已归入 party.seller，页眉公司不再单独标 seller） |
| port.loading ↔ port.discharge ↔ port.transhipment | 发货港 / 目的港 / 中转港 |
| date.issue ↔ date.invoice ↔ date.shipment ↔ date.delivery ↔ date.flight | 引导词区分 |
| no.order ↔ no.contract ↔ no.deliver | 订单号 / 合同号 / 交货单号 |
| no.reference ↔ our_reference_no | 参考号 vs 卖方内部参考号 |

## 4. 两批单据命名差异（迁移关键）

早期 6 单据与第二批 10 单据**命名体系不同**，归并时已对齐：

| 差异模式 | 早期（6 单据） | 第二批（10 单据） |
|---|---|---|
| 字段前缀 | bl_ 前缀（bl_shipper/bl_port_of_loading）、裸名（net_weight/gross_weight@air） | 统一 goods_/total_ 前缀 |
| 单价 | price_of_goods（ci/do/pi/pl） | goods_price |
| 发票号 | invoice_no（bl/cr/sdn/swb） | invoice_number |
| 订单号 | order_no（bl/swb） | order_number |
| 船名 | bl_vessel / vessel | vessel_name |
| 提单号 | bl_id | bl_no |
| 参考号 | reference_no / reference / our_ref | reference / our_reference_no |
| 发货港 | bl_port_of_loading / airport_of_departure | port_of_loading |
| 数量 | total_pieces/no_of_pieces（air）/ total_quantity（cr） | goods_quantity/total_qty |
| 品名 | bl_goods_name / goods_services_description（loan） | goods_name |

**含义**：新单据若字段名接近"早期命名"（如 `bl_` 前缀、`net_weight`），应归一化到同一概念而非新建；这正是别名表 + 向量的价值场景。

## 5. 与能力标签的映射

概念 → capability-tags（语义标签见 capability-tags.md）：

- quantity/carton/parcel/pallet/total.qty → `quantity` + `numeric_value` + `grouped_value`
- weight.gross/net/unspecified、total.weight.*、size、measurement → `weight`/`size` + `numeric_unit`
- price/amount/subtotal/total.amount/currency → `monetary` + `currency_amount`
- item_no → `identifier` + `numeric_value`（序号，数值型标识）
- product_no/no.*/container/seal/hs_code → `identifier` + `code_value`
- name → `item` + `long_text`
- party.* → `party` + `short_text`；address → `address` + `long_text`
- date.* → `temporal` + `date_value`
- port.loading/discharge/transhipment、vessel、voyage、flight、awb → `transport` + `short_text`
- origin、place.delivery/receipt → `location` + `short_text`
- bank.* → `bank` + `short_text`
- payment.term/info、financing → `payment` + `short_text`
- incoterm、freight、declared_value、signature、packaging、goods.attr、title、remarks、doc.count → `term`（goods.attr/packaging 亦可挂 `item`）

## 6. 未覆盖字段处理链路

新单据字段在词典中无匹配时，分三种结局（详见 `schema.md` §4.2）：

```
新单据字段（字段名 + 说明 + 样例值）
   │
   ├─ 三路匹配（别名 / 值形态启发 / 向量≥0.75）
   │     高置信命中 → 归一化到概念，复用经验
   │     低置信 → Top-N 候选概念 + 匹配依据 + 人工确认
   │
   ├─ 向量近邻但语义不同 → 输出「易混警示」，不迁移（如 item_no↔product_no）
   │
   └─ 完全未覆盖（真·新字段）
         训练前：标记 unknown + 走默认 SOP + 人工确认语义 + 记入 pending 队列
         训练中：作为新字段独立处理
         训练后：验证稳定/语义明确 → 上报 candidate 概念（或 candidate 别名实例）
                 → 人工审核入库 → 积累 ≥2 条不同单据 Case（或 1 条 + 人工确认）→ validated 进正式索引
                 → 下次同类字段即可命中（回灌闭环）
```

三个执行约定（建议值，待最终拍板）：

1. **升级门槛**：candidate 概念需 ≥2 条来自不同单据的 Case，或 1 条 + 人工确认，才 validated——与 Case→Claim 的"单次实验不当通用规律"原则一致。
2. **审核归属**：消费方上报、memory 侧审核（双向），核心不依赖单一消费方。
3. **unknown 呈现**：给 Top-N 最接近概念 + 明确的"无高置信匹配"标记，不黑盒、不误导强推。

## 7. 待补

1. `hm_alias` 中英别名（buyer_zh/en 等）的完整并入（§1.4 已列部分）。
2. 值形态启发正则（编号/金额/日期/名称判别式）正式化。
3. 概念 → bge-m3 向量锚（Phase 2 做，词典先提供文本锚）。
