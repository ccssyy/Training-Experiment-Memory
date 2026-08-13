#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Phase 2-MVP 端到端 demo：两个新单据 → 画像 → 检索 → 建议卡。

验证目标（见 11-phase2-plan.md §3）：
1. schema 机器可读（Case/Claim JSON 落盘读回）
2. 字段语义匹配走通
3. 规则检索排序合理
4. 值形态过滤生效
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from profiler import profile_fields
from advisor import advise


def main():
    print("=" * 70)
    print("场景 A：装箱单（密集表格，行级归组数量字段）")
    print("=" * 70)
    packing_list = [
        {"name": "goods_quantity", "sample": "1,392 BAGS"},
        {"name": "goods_name", "sample": "GPU A100 Module"},
        {"name": "goods_carton", "sample": "10 CTN"},
        {"name": "goods_parcel", "sample": "200 PACKAGES"},
    ]
    profile_a = profile_fields(packing_list, doc_type="packing_list")
    print(advise(profile_a, top_k=3))

    print("\n" + "=" * 70)
    print("场景 B：出口托收申请书（多区块，银行/编号字段）")
    print("=" * 70)
    aco = [
        {"name": "issuing_bank", "sample": "BANK OF NINGBO BEIJING BRANCH"},
        {"name": "available_with", "sample": "BANK OF NINGBO BEIJING BRANCH"},
        {"name": "beneficiary_bank", "sample": "Standard Chartered"},
        {"name": "beneficiary_account", "sample": "IT136102000805364000002915051"},
        {"name": "invoice_no", "sample": "INV-2026-001"},
    ]
    profile_b = profile_fields(aco, doc_type="aco")
    print(advise(profile_b, top_k=3))

    print("\n" + "=" * 70)
    print("场景 C：无匹配字段（冷启动降级）")
    print("=" * 70)
    unknown = [
        {"name": "custom_field_x", "sample": "some novel value 123"},
    ]
    profile_c = profile_fields(unknown, doc_type="unknown")
    print(advise(profile_c, top_k=3))

    print("\n" + "=" * 70)
    print("场景 D：需 bbox 定位的新任务（上下文类经验 → task_shape 命中）")
    print("=" * 70)
    bbox_task = [
        {"name": "product_no", "sample": "SKU-88231"},
        {"name": "goods_amount", "sample": "USD 535.00"},
    ]
    profile_d = profile_fields(bbox_task, doc_type="sales_contract", task_shape={"bbox_required": True, "triggers": ["vllm_runtime"]})
    print(advise(profile_d, top_k=3))


if __name__ == "__main__":
    main()
