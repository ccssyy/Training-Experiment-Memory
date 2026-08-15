#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""strategy-advisor：top-k Claim → 建议卡（策略 + 证据 + 反证）。

永不自动改参数，输出仅为建议。
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")


def load_claims():
    with open(os.path.join(DATA, "claims.json"), encoding="utf-8") as f:
        return json.load(f)


def load_cases():
    with open(os.path.join(DATA, "cases.json"), encoding="utf-8") as f:
        return json.load(f)


def render_card(profile, ranked):
    """把画像 + top-k Claim 渲染成 Markdown 建议卡。"""
    cases = {c["case_id"]: c for c in load_cases()}
    lines = []
    lines.append("# 策略建议卡\n")
    lines.append("## 任务画像摘要\n")
    lines.append(f"- 单据类型：{profile.get('doc_type') or '未知'}")
    lines.append(f"- 命中语义标签：{', '.join(profile.get('semantic_tags', [])) or '无'}")
    lines.append(f"- 值形态：{', '.join(profile.get('value_shapes', [])) or '无'}")
    vis_layout = profile.get('layout_tags_visual') or profile.get('layout_tags') or []
    lines.append(f"- 版式标签：{', '.join(vis_layout) or '无'}")
    if profile.get("layout_doc_match"):
        dtype = profile.get("layout_doc_match_type") or profile["layout_doc_match"]
        cn = profile.get("layout_doc_match_cn") or ""
        scope_cn = profile.get("layout_doc_scope_cn") or ""
        desc = dtype
        if cn:
            desc = f"{dtype}（{cn}" + (f"，{scope_cn}标注" if scope_cn else "") + "）"
        lines.append(f"- 版式视觉确认：{desc}，样例图最像该单据")
    if profile.get("layout_doc_conflict"):
        dtype = profile.get("layout_doc_match_type") or profile.get("layout_doc_match")
        cn = profile.get("layout_doc_match_cn") or dtype
        lines.append(
            f"- 警告：声明的单据类型（{profile.get('doc_type')}）与样例图版式不一致，"
            f"视觉判定更像 {cn}（{dtype}），请核对是否标错或拿错样例图"
        )
    if profile.get("unmatched_fields"):
        lines.append(f"- 未匹配字段（需人工确认语义）：{', '.join(profile['unmatched_fields'])}")
    lines.append("")

    if not ranked:
        lines.append("## 无匹配经验\n")
        lines.append("> 回退默认 SOP（通用抽取规范）+ 人工确认字段语义。\n")
        return "\n".join(lines)

    lines.append("## 候选策略\n")
    for i, r in enumerate(ranked, 1):
        lines.append(f"### {i}. {r['claim_id']}（{r['status']}，迁移层级 {r['transfer_level']}）\n")
        lines.append(f"- **问题模式**：{r['problem_pattern']}")
        lines.append(f"- **建议干预**：{r['intervention_strategy']}")
        lines.append(f"- **命中标签**：语义 {r['matched_tags']['semantic'] or '—'} / 版式 {r['matched_tags']['layout'] or '—'}")
        lines.append(f"- **失效边界**：{'; '.join(r['contraindications']) or '—'}")
        # 证据回溯
        ev = []
        for cid in r["supported_by"]:
            case = cases.get(cid)
            if case:
                ev.append(f"{cid}（{case['problem'].get('symptom', '')}）")
        lines.append(f"- **支撑证据**：{'; '.join(ev) or '—'}")
        lines.append("")

    lines.append("## 保护条件与回归提示\n")
    lines.append("- 以上均为建议，不自动改参数；人工接受后进入 plan。")
    lines.append("- 应用前核对：字段面对齐、评估口径、值形态是否与经验一致。")
    return "\n".join(lines)


def advise(profile, top_k=5):
    from retriever import retrieve
    ranked = retrieve(profile, top_k=top_k)
    return render_card(profile, ranked)


if __name__ == "__main__":
    from profiler import profile_fields
    demo = [
        {"name": "goods_quantity", "sample": "1,392 BAGS"},
        {"name": "goods_name", "sample": "GPU A100 Module"},
        {"name": "goods_carton", "sample": "10 CTN"},
    ]
    profile = profile_fields(demo, doc_type="packing_list")
    print(advise(profile))
