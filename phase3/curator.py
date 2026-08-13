#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""curator：回灌引擎——EvidenceEvent → candidate Claim → 验证门槛 → 状态机转换。

链路（doc 07 §1.9）：读训练事实 → 追加 EvidenceEvent → 关联/创建 Case → 生成 candidate
→ 验证门槛 → 人工验收 → validated/rejected/unresolved。
"""
import json
import os

from evidence import EvidenceEvent
from validate import decide

HERE = os.path.dirname(os.path.abspath(__file__))


def load_claims():
    with open(os.path.join(HERE, "..", "phase2", "data", "claims.json"), encoding="utf-8") as f:
        return json.load(f)


def build_candidate(event):
    """从 EvidenceEvent 生成 candidate Claim（status=candidate）。"""
    return {
        "claim_id": None,  # 待分配
        "status": "candidate",
        "problem_pattern": event.badcase_analysis.get("problem_pattern", ""),
        "intervention_strategy": event.badcase_analysis.get("suggested_fix", ""),
        "evidence_event": event.event_id,
        "run_ref": event.run_ref,
    }


def curate(event, human_approval=False):
    """回灌主流程：判定状态 + 生成 candidate。返回结构化结果。"""
    is_diagnostic = event.kind == "diagnostic"
    result = decide(event, human_approval=human_approval, is_diagnostic=is_diagnostic)
    result["event_id"] = event.event_id
    result["candidate"] = build_candidate(event) if result["status"] != "blocked" else None
    return result


def render(result):
    """渲染回灌结果（供 dry-run 展示）。"""
    lines = [f"[{result['event_id']}] → {result['status']}"]
    if result.get("gates"):
        for g in result["gates"]:
            lines.append(f"  ⛔ {g}")
    if result.get("rejected_hits"):
        for r in result["rejected_hits"]:
            lines.append(f"  ✗ {r}")
    if result.get("passed"):
        for p in result["passed"]:
            lines.append(f"  ✓ {p}")
    if result.get("failed"):
        for f in result["failed"]:
            lines.append(f"  ○ {f}")
    lines.append(f"  reason: {result['reason']}")
    return "\n".join(lines)


if __name__ == "__main__":
    pass
