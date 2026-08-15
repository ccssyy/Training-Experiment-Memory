#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""experience-retriever：画像 → 能力标签命中 → top-k Claim（含 transfer_level）。

规则打分 + 值形态过滤（grouped_value 经验不推荐给 single_value 字段）。
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")


def load_claims():
    with open(os.path.join(DATA, "claims.json"), encoding="utf-8") as f:
        return json.load(f)


def load_mechanisms():
    path = os.path.join(DATA, "mechanisms.json")
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _overlap(a, b):
    return len(set(a) & set(b))


def _value_shape_filter(claim, profile):
    """值形态/基数过滤矩阵：claim 的强约束在画像中不满足 → 过滤。

    规则（保守，只过滤明确不兼容的）：
    1. 基数：claim 需要 grouped_value（行级归组经验），画像无 grouped_value 字段 → 过滤。
    2. 值形态强类型：claim 的 value_shape 全是强类型（currency_amount/date_value/numeric_unit），
       画像字段无对应值形态 → 过滤（如金额经验不适用无金额字段的任务）。
    """
    claim_card = claim["capability_tags"].get("cardinality", [])
    profile_card = set(profile.get("cardinalities", []))
    # 1. 基数：grouped_value 经验不推荐给无 grouped_value 字段的画像
    if "grouped_value" in claim_card and "grouped_value" not in profile_card:
        return True

    # 2. 值形态强类型：金额/日期/带单位数值经验，画像无对应值形态 → 过滤
    claim_vs = claim["capability_tags"].get("value_shape", [])
    profile_vs = set(profile.get("value_shapes", []))
    strong_types = {"currency_amount", "date_value", "numeric_unit"}
    if claim_vs and set(claim_vs) <= strong_types and not (set(claim_vs) & profile_vs):
        return True

    return False


def _applicability_check(claim, profile):
    """结构化适用性判定。返回 (when_ok, contra_hits)。

    when = AND（全满足才推荐）；contraindications = OR（命中任一即降权）。
    画像缺失某维度 → 该维度宽松通过（不因缺数据误拒）。
    """
    app = claim.get("applicability") or {}
    when = app.get("when") or {}
    task_shape = profile.get("task_shape") or {}
    prof_map = {"cardinality": "cardinalities", "value_shape": "value_shapes", "layout": "layout_tags"}

    when_ok = True
    # lane（画像单值 vs when 列表；用户显式 lane 优先，否则用视觉推断的 lane）
    if when.get("lane"):
        p_lane = task_shape.get("lane") or profile.get("layout_doc_lane")
        if p_lane and p_lane not in when["lane"]:
            when_ok = False
    # languages（画像列表 vs when 列表）
    if when.get("languages"):
        p_langs = task_shape.get("languages") or []
        if p_langs and not (set(p_langs) & set(when["languages"])):
            when_ok = False
    # doc_types（画像单值 vs when 列表）
    if when.get("doc_types"):
        p_doc = profile.get("doc_type")
        if p_doc and p_doc not in when["doc_types"]:
            when_ok = False
    # cardinality / value_shape / layout（画像列表 vs when 列表）
    for dim, prof_key in prof_map.items():
        if when.get(dim):
            p_vals = set(profile.get(prof_key) or [])
            if p_vals and not (p_vals & set(when[dim])):
                when_ok = False
    # distribution / data_scale：画像暂无，宽松通过（后续接入）

    # contraindications OR
    contra_hits = []
    for c in app.get("contraindications") or []:
        if isinstance(c, str):  # 旧格式字符串，跳过结构化判定
            continue
        if _cond_match(c.get("when") or {}, profile, task_shape):
            contra_hits.append(c.get("reason", ""))

    return when_ok, contra_hits


def _cond_match(cond, profile, task_shape):
    """单个 contraindication 条件是否命中（条件内所有键都命中才算命中）。"""
    if cond.get("lane") and task_shape.get("lane") != cond["lane"]:
        return False
    for dim, prof_key in (("cardinality", "cardinalities"), ("value_shape", "value_shapes"), ("layout", "layout_tags")):
        if cond.get(dim):
            p = set(profile.get(prof_key) or [])
            if p and not (p & set(cond[dim])):
                return False
    return True


def _match_mechanism(mechanism, profile):
    """机制的结构前提匹配（AND，画像缺维度宽松通过）。

    structural_preconditions 只含稳定属性（semantic/cardinality/value_shape/layout/cross_page），
    不含易变字段类型——机制层命中不看 lane/doc_types。
    """
    sp = mechanism.get("structural_preconditions") or {}
    for dim, prof_key in (("semantic", "semantic_tags"), ("cardinality", "cardinalities"),
                          ("value_shape", "value_shapes"), ("layout", "layout_tags")):
        if sp.get(dim):
            p_vals = set(profile.get(prof_key) or [])
            if p_vals and not (p_vals & set(sp[dim])):
                return False
    if sp.get("cross_page") is not None:
        p_cross = (profile.get("task_shape") or {}).get("cross_page")
        if p_cross is not None and p_cross != sp["cross_page"]:
            return False
    return True


def score_claim(claim, profile):
    """规则打分。返回 (score, matched_tags)。

    原则：有语义标签的 claim 以语义命中为主信号，版式只做加分、不兜底；
    语义为空的"上下文类"claim（训练稳定性/运行时/评估口径）靠 task_shape.triggers 命中。
    """
    ct = claim["capability_tags"]
    sem = profile.get("semantic_tags", [])
    lay = profile.get("layout_tags", [])
    claim_sem = ct.get("semantic", [])
    claim_lay = ct.get("layout", [])

    matched = {
        "semantic": sorted(set(claim_sem) & set(sem)),
        "layout": sorted(set(claim_lay) & set(lay)),
        "task_shape": [],
    }
    n_sem = len(matched["semantic"])
    n_lay = len(matched["layout"])

    if claim_sem:
        # 有语义标签：语义是主信号，零语义命中则版式不兜底
        if n_sem == 0:
            return 0.0, matched
        score = 0.7 * (n_sem / len(claim_sem)) + 0.3 * (n_lay / max(1, len(claim_lay)))
    else:
        # 上下文类 claim（semantic 空）：靠 task_shape.triggers 命中
        n_trig = _trigger_overlap(claim, profile, matched)
        if n_trig > 0:
            score = 0.8  # 触发词命中是强信号
        elif n_lay > 0:
            score = 0.3 * (n_lay / len(claim_lay))
        else:
            return 0.0, matched

    # status 加权：validated（干预验证）> confirmed（归因/诊断确认）
    if claim["status"] == "validated":
        score += 0.15
    elif claim["status"] == "confirmed":
        score += 0.08

    return round(score, 4), matched


def _trigger_overlap(claim, profile, matched):
    """task_shape.triggers 与 profile 的触发词求交集。"""
    claim_trig = (claim.get("task_shape") or {}).get("triggers", [])
    profile_trig = set((profile.get("task_shape") or {}).get("triggers", []))
    hit = sorted(set(claim_trig) & profile_trig)
    matched["task_shape"] = hit
    return len(hit)


def _effective_profile(profile):
    """增强画像：版式标签视觉优先。

    有视觉确认（layout_tags_visual 非空）时，版式标签以视觉为准（真实视觉判定，
    比 doc_type 粗推可靠）；无视觉确认才用粗推标签。避免「声明 doc_type 标错时，
    粗推标签仍救活不相关经验」的问题。
    """
    p = dict(profile)
    vis = profile.get("layout_tags_visual") or []
    if vis:
        p["layout_tags"] = sorted(vis)
    return p


def retrieve_with_mechanism(profile, top_k=5):
    """检索 + 机制层。返回 (results, mechanism_fallbacks)。

    results：现有格式，外加 mechanism_id/mechanism_name 字段。
    mechanism_fallbacks：命中机制（结构属性）但无匹配 Claim 实例的机制（③b 兜底：推荐机制+提示）。
    """
    profile = _effective_profile(profile)
    claims = load_claims()
    mechanisms = load_mechanisms()
    mech_by_id = {m["mechanism_id"]: m for m in mechanisms}

    # ① 命中机制（结构属性，不看字段类型）
    matched_mechs = [m for m in mechanisms if _match_mechanism(m, profile)]

    # ② 定位 Claim 实例（现有逻辑，加机制信息）
    results = []
    for c in claims:
        if _value_shape_filter(c, profile):
            continue  # 值形态不匹配直接过滤
        when_ok, contra_hits = _applicability_check(c, profile)
        if not when_ok:
            continue  # when 不满足 → 不推荐
        score, matched = score_claim(c, profile)
        if score <= 0:
            continue
        if contra_hits:
            score = max(0.0, score - 0.5)  # 命中失效边界 → 显著降权
        mid = c.get("mechanism_id")
        results.append({
            "claim_id": c["claim_id"],
            "mechanism_id": mid,
            "mechanism_name": mech_by_id[mid]["name"] if mid in mech_by_id else None,
            "status": c["status"],
            "score": round(score, 4),
            "matched_tags": matched,
            "transfer_level": c["applicability"].get("transfer_level"),
            "problem_pattern": c["problem_pattern"],
            "intervention_strategy": c["intervention_strategy"],
            "contraindications": [
                x.get("reason", str(x)) if isinstance(x, dict) else x
                for x in c["applicability"].get("contraindications", [])
            ],
            "contra_hits": contra_hits,
            "supported_by": c["supported_by"],
        })
    results.sort(key=lambda r: -r["score"])

    # ③b 兜底：命中机制但无匹配实例
    hit_mech_ids = {r["mechanism_id"] for r in results if r.get("mechanism_id")}
    fallbacks = [m for m in matched_mechs if m["mechanism_id"] not in hit_mech_ids]

    return results[:top_k], fallbacks


def retrieve(profile, top_k=5):
    """返回 top-k Claim 列表，含分数、匹配标签、transfer_level（向后兼容）。"""
    results, _ = retrieve_with_mechanism(profile, top_k)
    return results


if __name__ == "__main__":
    from profiler import profile_fields
    demo = [
        {"name": "goods_quantity", "sample": "1,392 BAGS"},
        {"name": "goods_name", "sample": "GPU A100 Module"},
        {"name": "goods_carton", "sample": "10 CTN"},
    ]
    profile = profile_fields(demo, doc_type="packing_list")
    import pprint
    pprint.pprint(profile)
    print("=== top-k ===")
    pprint.pprint(retrieve(profile))
