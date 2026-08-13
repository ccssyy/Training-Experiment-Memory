#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""task-profilers：新单据字段定义 → 分层画像（字段 → 概念 → 语义标签）。

MVP 三路匹配只实现前两路（别名表 + 值形态启发），向量路留 P4。
"""
import json
import re
import os

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")


def load_concepts():
    with open(os.path.join(DATA, "concepts.json"), encoding="utf-8") as f:
        return json.load(f)


def _norm(name):
    """字段名归一化：小写、去下划线/连字符，用于别名匹配。"""
    return re.sub(r"[^a-z0-9]", "", (name or "").lower())


def value_shape_heuristic(sample):
    """值形态启发：根据样例值判断 value_shape / semantic。

    返回 (value_shape, extra_semantic)。启发规则从 field-semantics.md 值形态规则提炼。
    """
    if sample is None or sample == "":
        return None, []
    s = str(sample).strip()
    # 金额：币种符号/代码 + 数字
    if re.search(r"[\$€£¥]|USD|CNY|HKD|EUR|CHF|RMB", s, re.I) and re.search(r"\d", s):
        return "currency_amount", ["monetary"]
    # 日期：形如 2026-03-25 / 25 MAR 2026
    if re.search(r"\d{4}[-/]\d{1,2}[-/]\d{1,2}", s) or re.search(r"\d{1,2}\s*(JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEP|OCT|NOV|DEC)\s*\d{4}", s, re.I):
        return "date_value", ["temporal"]
    # 数值+单位（重量/尺寸）
    if re.search(r"\d+(\.\d+)?\s*(KG|KGS|LB|LBS|MT|G|CTN|CBM|M3|PCS|CM|MM)\b", s, re.I):
        return "numeric_unit", ["weight", "size"]
    # 纯数值
    if re.fullmatch(r"[\d,\.\s]+", s):
        return "numeric_value", ["quantity"]
    # 编号（字母数字混合）
    if re.search(r"[A-Z]{2,}[0-9]|[0-9][A-Z]{2,}", s):
        return "code_value", ["identifier"]
    # 长文本
    if len(s) > 40:
        return "long_text", ["item"]
    return "short_text", []


def profile_fields(fields, doc_type=None, task_shape=None):
    """字段列表 → 画像。

    fields: [{"name": str, "sample": str|None}, ...]
    task_shape: 可选，任务形态定性（{"lane","bbox_required","cross_page","triggers":[...]}），上下文类经验检索用。
    返回 dict：字段级映射 + 聚合标签集合。
    """
    concepts = load_concepts()
    alias_index = {}
    for c in concepts:
        for a in c["aliases"]:
            alias_index.setdefault(_norm(a), c["c"])

    semantic_tags, value_shapes, cardinalities = set(), set(), set()
    field_profile = []

    for f in fields:
        name = f.get("name", "")
        sample = f.get("sample")
        norm = _norm(name)
        concept = alias_index.get(norm)
        matched_by = "alias" if concept else "none"

        vs, extra_sem = value_shape_heuristic(sample)
        sem = set()

        if concept:
            # 从概念取语义标签/值形态/基数
            cmap = next((c for c in concepts if c["c"] == concept), None)
            if cmap:
                sem.update(cmap.get("semantic", []))
                vs = cmap.get("vs") or vs
                card = cmap.get("card", "single_value")
            else:
                card = "single_value"
        else:
            # 未命中概念：只靠值形态启发给语义
            card = "single_value"

        sem.update(extra_sem)
        semantic_tags.update(sem)
        value_shapes.add(vs) if vs else None
        cardinalities.add(card)

        field_profile.append({
            "name": name,
            "sample": sample,
            "concept": concept,
            "matched_by": matched_by,
            "semantic": sorted(sem),
            "value_shape": vs,
            "cardinality": card,
        })

    # 版式标签：MVP 从 doc_type 推断（后续可接版式画像）
    layout_tags = _infer_layout(doc_type)

    return {
        "doc_type": doc_type,
        "fields": field_profile,
        "semantic_tags": sorted(semantic_tags),
        "value_shapes": sorted(vs for vs in value_shapes if vs),
        "cardinalities": sorted(cardinalities),
        "layout_tags": sorted(layout_tags),
        "task_shape": task_shape or {},
        "unmatched_fields": [f["name"] for f in field_profile if f["matched_by"] == "none"],
    }


def _infer_layout(doc_type):
    """从单据类型粗推版式标签（MVP 规则，后续接版式画像）。"""
    dt = (doc_type or "").lower()
    if "packing" in dt or "装箱" in dt:
        return ["dense_table", "long_table"]
    if any(k in dt for k in ["invoice", "order", "发票", "订单"]):
        return ["dense_table", "multi_block"]
    if any(k in dt for k in ["waybill", "bill", "提单", "海运"]):
        return ["multi_block", "labeled_value"]
    return ["multi_block"]


if __name__ == "__main__":
    import pprint
    demo = [
        {"name": "goods_quantity", "sample": "1,392 BAGS"},
        {"name": "goods_amount", "sample": "USD 535.00"},
        {"name": "buyer", "sample": "Acme Corp"},
        {"name": "invoice_no", "sample": "INV-2026-001"},
    ]
    pprint.pprint(profile_fields(demo, doc_type="packing_list"))
