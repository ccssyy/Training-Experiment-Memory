#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""回灌闭环 dry-run：用 3 条历史证据走全流程，验证 EvidenceEvent + 验证门槛 + 状态机结构。

1. 正例 CASE-0007 金额清洗 → 应走通 candidate→validated（7 项全过）
2. 反例 CASE-0006 GB512 坍缩 → 应命中 rejected（输出坍缩）
3. 归因例 CASE-0019 空输出二分 → 应走 confirmed（归因确认，非干预验证）
"""
from evidence import EvidenceEvent
from curator import curate, render


def main():
    print("=" * 70)
    print("dry-run 1：正例 · 金额清洗（amount F1 0.4211 → 1.0000）")
    print("=" * 70)
    e1 = EvidenceEvent(
        event_id="EVT-0001",
        run_ref="销售合同金额清洗实验",
        badcase_analysis={
            "problem_pattern": "币种混入 value 导致 exact 判错",
            "suggested_fix": "value 去币种 + currency 独立 + bbox 保留",
        },
        metrics={
            "delta": {"amount_F1": "0.4211 → 1.0000"},
            "improved": True,
            "degradation": {"protected": False, "bbox_card_group": False},
        },
        evaluator={"valid": True, "runtime_raw": True, "id_ood": "ID/OOD 同合同复测"},
        provenance={"source_revisions": ["销售合同清洗"], "created_at": "2026-08-13"},
    )
    print(render(curate(e1, human_approval=True)))

    print("\n" + "=" * 70)
    print("dry-run 2：反例 · GB512 输出坍缩（ckpt80 全 0）")
    print("=" * 70)
    e2 = EvidenceEvent(
        event_id="EVT-0002",
        run_ref="6other po0512 GB512 实验",
        badcase_analysis={
            "problem_pattern": "GB512 后期输出坍缩",
            "suggested_fix": "切回 GB256 + LR2e-4",
        },
        metrics={
            "delta": {"collapse": "ckpt80 全 0"},
            "improved": False,
            "degradation": {"core": True, "empty_output": True},
        },
        evaluator={"valid": True, "runtime_raw": True, "id_ood": "N/A"},
        provenance={"source_revisions": ["6other po0512"], "created_at": "2026-08-13"},
    )
    print(render(curate(e2)))

    print("\n" + "=" * 70)
    print("dry-run 3：归因例 · 空输出二分（选错字段 vs 真实负样本）")
    print("=" * 70)
    e3 = EvidenceEvent(
        event_id="EVT-0003",
        run_ref="EXP-20260421-empty-source-split",
        kind="diagnostic",
        badcase_analysis={
            "problem_pattern": "空输出混同选错字段与真实负样本",
            "suggested_fix": "二分归因：选错字段加锚点 vs 真实负样本控比例",
        },
        metrics={
            "delta": {"可避免比例": "CI 77%/BL 71%/Air 94%/PO 7%/CR 0%"},
            "improved": None,  # 归因分析，无"干预改善"
        },
        evaluator={"valid": True, "runtime_raw": False, "id_ood": "N/A"},
        provenance={"source_revisions": ["0414_5_goods"], "created_at": "2026-08-13"},
    )
    print(render(curate(e3)))

    print("\n" + "=" * 70)
    print("dry-run 4：门槛拦截 · 缺证据（应 block）")
    print("=" * 70)
    e4 = EvidenceEvent(
        event_id="EVT-0004",
        run_ref="某实验",
        badcase_analysis={},   # 缺 problem_pattern
        metrics={},            # 缺 delta
        evaluator={},
        provenance={"created_at": "2026-08-13"},
    )
    print(render(curate(e4)))


if __name__ == "__main__":
    main()
