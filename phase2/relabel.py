#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把 claims.json 的 applicability 从旧格式（preconditions/字符串 contraindications）
升级为结构化 when + contraindications{when,reason}（见 docs/applicability-dimensions.md）。"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
PATH = os.path.join(HERE, "data", "claims.json")

LANGS = ["zh", "en", "zh_en"]

# 字段语义类：claim_id -> {lane, doc_types, contra}
FIELD_SEMANTIC = {
    "CLAIM-0001": {"lane": ["goods"], "doc_types": ["packing_list"], "contra": [
        {"when": {"cardinality": "single_value"}, "reason": "单值字段不适用，本经验针对行级归组"},
        {"when": {"cardinality": "single_value"}, "reason": "短表(<10行)收益有限"},
    ]},
    "CLAIM-0002": {"lane": ["goods"], "doc_types": ["packing_list"], "contra": [
        {"when": {"cardinality": "single_value"}, "reason": "单列数值表不适用"},
    ]},
    "CLAIM-0003": {"lane": ["goods", "non_goods"], "doc_types": ["packing_list"], "contra": [
        {"when": {"value_shape": "numeric_value"}, "reason": "无单位字段不适用"},
    ]},
    "CLAIM-0005": {"lane": ["goods", "non_goods"], "doc_types": ["sales_contract"], "contra": [
        {"when": {}, "reason": "币种在目标内需单独评估"},
    ]},
    "CLAIM-0007": {"lane": ["goods"], "doc_types": [], "contra": [
        {"when": {}, "reason": "高频字段过度上采样会膨胀"},
    ]},
    "CLAIM-0010": {"lane": ["non_goods"], "doc_types": ["aco", "proforma_invoice", "sea_waybill"], "contra": [
        {"when": {}, "reason": "合法共享值需人工豁免"},
    ]},
    "CLAIM-0011": {"lane": ["non_goods"], "doc_types": ["aco"], "contra": [
        {"when": {"value_shape": "numeric_value"}, "reason": "数值型字段不适用"},
    ]},
    "CLAIM-0012": {"lane": ["non_goods"], "doc_types": ["proforma_invoice", "sales_order"], "contra": [
        {"when": {"cardinality": "single_value"}, "reason": "单当事人单据不适用"},
    ]},
    "CLAIM-0016": {"lane": ["non_goods"], "doc_types": [], "contra": []},
}


def main():
    claims = json.load(open(PATH, encoding="utf-8"))
    for c in claims:
        cid = c["claim_id"]
        app = c.get("applicability") or {}
        app.pop("preconditions", None)

        if cid in FIELD_SEMANTIC:
            r = FIELD_SEMANTIC[cid]
            app["when"] = {"lane": r["lane"], "doc_types": r["doc_types"], "languages": LANGS}
            app["contraindications"] = r["contra"]
        else:
            # 上下文类：when 不设 lane/doc_types（跨单据/lane 通用，靠 task_shape 命中）
            app["when"] = {"languages": LANGS}
            old = app.get("contraindications") or []
            app["contraindications"] = [
                {"when": {}, "reason": x} for x in old if isinstance(x, str) and x != "无"
            ]
        c["applicability"] = app

    with open(PATH, "w", encoding="utf-8") as f:
        json.dump(claims, f, ensure_ascii=False, indent=2)
    print(f"重标完成：{len(claims)} 条，字段语义类 {len(FIELD_SEMANTIC)} 条 + 上下文类 {len(claims)-len(FIELD_SEMANTIC)} 条")


if __name__ == "__main__":
    main()
