# 端到端演示：画像 → 检索 → 建议卡

> 日期：2026-08-13 ｜ 复现命令：`python3 phase2/demo.py`（零 GPU，Mac 本地即可）
> 演示完整链路：字段定义 → 画像引擎 → 检索引擎 → 建议卡。

## 演示输入（新单据字段定义）

一个「装箱单」新任务，给出 4 个字段名 + 样例值：

| 字段名 | 样例值 |
|---|---|
| `goods_quantity` | 1,392 BAGS |
| `goods_name` | GPU A100 Module |
| `goods_carton` | 10 CTN |
| `goods_parcel` | 200 PACKAGES |

## 第 1 步：画像引擎输出

每个字段归一化到 canonical 概念 + 打上语义标签 + 值形态：

```python
{
  "doc_type": "packing_list",
  "fields": [
    {"name": "goods_quantity", "concept": "quantity", "matched_by": "alias",
     "semantic": ["quantity"], "value_shape": "numeric_value", "cardinality": "grouped_value"},
    {"name": "goods_name", "concept": "name", "matched_by": "alias",
     "semantic": ["item"], "value_shape": "long_text", "cardinality": "single_value"},
    {"name": "goods_carton", "concept": "carton", "matched_by": "alias",
     "semantic": ["quantity","parcel"], "value_shape": "numeric_value", "cardinality": "single_value"},
    {"name": "goods_parcel", "concept": "parcel", "matched_by": "alias",
     "semantic": ["quantity","parcel"], "value_shape": "numeric_value", "cardinality": "single_value"}
  ],
  "semantic_tags": ["item","parcel","quantity","size","weight"],
  "value_shapes": ["long_text","numeric_value"],
  "layout_tags": ["dense_table","long_table"]
}
```

## 第 2 步：检索结果（top-3）

画像的标签集合 vs 每条 Claim 的 capability_tags 求交集，按分数排序：

| 排名 | Claim | 命中标签 | 分数来源 |
|---|---|---|---|
| 1 | CLAIM-0001 漏行 | quantity + dense_table + long_table | 语义 100% + 版式命中 |
| 2 | CLAIM-0002 重复 group/串位 | parcel+quantity + 版式 | 语义命中 |
| 3 | CLAIM-0007 低频字段漏抽 | parcel + dense_table | 语义部分命中 |

## 第 3 步：建议卡（最终输出）

```markdown
# 策略建议卡
## 任务画像摘要
- 单据类型：packing_list
- 命中语义标签：item, parcel, quantity, size, weight
- 版式标签：dense_table, long_table

## 候选策略
### 1. CLAIM-0001（candidate，迁移层级 mechanism）
- 问题模式：行级归组数量字段在密集跨页表格易漏行
- 建议干预：长表分段 + 行级守恒 + 连续重叠 core
- 失效边界：单值字段不适用; 短表<10行收益有限
- 支撑证据：CASE-0001（row_delta<0 占 84/202 样本；goods_quantity FP/FN=339/1045）

### 2. CLAIM-0002（candidate，迁移层级 mechanism）
- 问题模式：归组字段在长表易重复 group / 相邻列串位
- 建议干预：行对齐 + 连续重叠 core + 槽位去重
- 支撑证据：CASE-0002（168 个重复 group）; CASE-0003（386 个串位事件）

## 保护条件与回归提示
- 以上均为建议，不自动改参数；人工接受后进入 plan。
```

## 关键机制说明

1. **字段名解耦**：`goods_quantity`/`goods_carton`/`goods_parcel` 三个不同字段名，靠别名表归一化到 `quantity`/`carton`/`parcel` 三个概念，再挂 `quantity`/`parcel` 标签——不是靠"装箱单"这个字段名命中，而是靠能力标签，可迁移到任何同类密集表格单据。

2. **值形态过滤**：`grouped_value` 经验不会被推荐给 `single_value` 字段（这条在场景 B 中生效）。

3. **无匹配降级**：场景 C（未知字段 `custom_field_x`）命中不了任何经验时，走「回退默认 SOP」而非强行推荐。

## 复现

```bash
cd phase2
python3 demo.py     # 4 个场景：装箱单 / 出口托收 / 未知字段 / bbox 任务
```
