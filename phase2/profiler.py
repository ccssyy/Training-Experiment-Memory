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


_concept_index_cache = None
_concept_index_cache_path = None


def load_concept_index(index_path):
    """加载 concept_index.json（进程内缓存，避免每次匹配重复解析）。返回 entries 列表。"""
    global _concept_index_cache, _concept_index_cache_path
    if _concept_index_cache is None or _concept_index_cache_path != index_path:
        with open(index_path, encoding="utf-8") as f:
            _concept_index_cache = json.load(f).get("entries", [])
        _concept_index_cache_path = index_path
    return _concept_index_cache


def _embed_text(text, server_url, timeout=30):
    """调 bge-m3 服务编码单个文本，返回向量（失败返回 None）。"""
    import urllib.request
    try:
        payload = json.dumps({"inputs": [{"text": text}]}).encode("utf-8")
        req = urllib.request.Request(
            f"{server_url.rstrip('/')}/v1/embeddings",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        resp = json.loads(urllib.request.urlopen(req, timeout=timeout).read())
        return resp["data"][0]["embedding"]
    except Exception:
        return None


def match_concept_by_vector(field_name, server_url, entries, top_k=1, threshold=0.68):
    """字段名 → bge-m3 向量 → 概念索引 k-NN。返回 (concept, score) 或 None。"""
    vec = _embed_text(field_name, server_url)
    if vec is None:
        return None
    best = None
    for e in entries:
        s = _cosine(vec, e["vector"])
        if best is None or s > best[1]:
            best = (e["concept"], s)
    if best and best[1] >= threshold:
        return best
    return None


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
    # 数值+重量/尺寸单位
    if re.search(r"\d+(\.\d+)?\s*(KG|KGS|LB|LBS|MT|CBM|M3|CM|MM)\b", s, re.I):
        return "numeric_unit", ["weight", "size"]
    # 数值+计数单位（箱/件/包，计数非重量尺寸）
    if re.search(r"\d+(\.\d+)?\s*(CTN|CTNS|PCS|CARTON|BAG|BAGS|PKG|PKGS|SET|SETS|UNIT|UNITS|EA)\b", s, re.I):
        return "numeric_value", ["quantity"]
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


def profile_fields(fields, doc_type=None, task_shape=None, image_path=None, embedding_server=None,
                   index_path=None, concept_embedding_server=None, concept_index_path=None):
    """字段列表 → 画像。

    fields: [{"name": str, "sample": str|None}, ...]
    task_shape: 可选，任务形态定性（{"lane","bbox_required","cross_page","triggers":[...]}），上下文类经验检索用。
    image_path: 可选，样例图路径；提供且 embedding_server 可达时，走版式向量级画像。
    embedding_server: 可选，版式 embedding 服务地址（如 http://127.0.0.1:9031）。
    index_path: 可选，layout_index.json 路径；提供时对版式向量做 k-NN 软匹配，得 layout_matches。
    concept_embedding_server: 可选，字段语义 embedding 服务（bge-m3，如 http://127.0.0.1:9033）。
    concept_index_path: 可选，concept_index.json 路径；别名表未命中时做语义向量兜底匹配。
    返回 dict：字段级映射 + 聚合标签集合（含可选 layout_vector / layout_matches）。
    """
    concepts = load_concepts()
    alias_index = {}
    for c in concepts:
        for a in c["aliases"]:
            alias_index.setdefault(_norm(a), c["c"])

    # 语义向量兜底：别名表未命中时，字段名 → bge-m3 → 概念索引 k-NN
    _concept_vec = concept_embedding_server and concept_index_path
    _concept_entries = None

    semantic_tags, value_shapes, cardinalities = set(), set(), set()
    field_profile = []

    for f in fields:
        name = f.get("name", "")
        sample = f.get("sample")
        norm = _norm(name)
        concept = alias_index.get(norm)
        matched_by = "alias" if concept else "none"

        # 别名表未命中 → 语义向量兜底（第三路）
        if concept is None and _concept_vec:
            if _concept_entries is None:
                _concept_entries = load_concept_index(concept_index_path)
            vhit = match_concept_by_vector(name, concept_embedding_server, _concept_entries)
            if vhit:
                concept = vhit[0]
                matched_by = "vector"

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

    # 版式标签：MVP 从 doc_type 推断（无样例图/服务时的 fallback）
    layout_tags = _infer_layout(doc_type)

    # 版式向量 + 软匹配：提供样例图 + embedding 服务时，走真实视觉向量级（可选，失败回退标签级）
    layout_vector = None
    layout_matches = []
    layout_doc_match = None
    layout_tags_visual = []
    layout_doc_conflict = False
    if image_path and embedding_server:
        layout_vector = embed_layout_vector(image_path, embedding_server)
        if layout_vector is not None and index_path:
            layout_matches = match_layout(layout_vector, doc_type, index_path)
            # 跨单据匹配：视觉确认「新图最像哪个单据」，比 doc_type 口头声明可靠
            cross = match_layout_cross(layout_vector, index_path, top_k=1, threshold=0.6)
            if cross:
                layout_doc_match = cross[0]["doc"]
                # 实测版式标签（glm-vision 核过，按单据类型查），兜底回 _infer_layout 规则
                layout_tags_visual = _DOC_LAYOUT.get(_doc_type_of(layout_doc_match), _infer_layout(doc_type))
                # 冲突：声明的 doc_type 与样例图视觉单据不一致（可能标错/拿错样例图）
                try:
                    index = load_layout_index(index_path)
                    declared_idx = _resolve_index_doc(doc_type, index.get("docs", {}).keys())
                    layout_doc_conflict = declared_idx is not None and declared_idx != layout_doc_match
                except Exception:
                    pass

    return {
        "doc_type": doc_type,
        "fields": field_profile,
        "semantic_tags": sorted(semantic_tags),
        "value_shapes": sorted(vs for vs in value_shapes if vs),
        "cardinalities": sorted(cardinalities),
        "layout_tags": sorted(layout_tags),
        "layout_vector": layout_vector,
        "layout_matches": layout_matches,
        "layout_matched": bool(layout_matches),
        "layout_doc_match": layout_doc_match,
        "layout_doc_match_type": _doc_type_of(layout_doc_match),
        "layout_doc_match_cn": doc_cn(layout_doc_match),
        "layout_doc_scope": _doc_scope_of(layout_doc_match),
        "layout_doc_scope_cn": _SCOPE_CN.get(_doc_scope_of(layout_doc_match), ""),
        "layout_doc_lane": _SCOPE_TO_LANE.get(_doc_scope_of(layout_doc_match)),
        "layout_tags_visual": sorted(layout_tags_visual),
        "layout_doc_conflict": layout_doc_conflict,
        "task_shape": task_shape or {},
        "unmatched_fields": [f["name"] for f in field_profile if f["matched_by"] == "none"],
    }


def embed_layout_vector(image_path, server_url, timeout=60):
    """调版式 embedding 服务，返回图片的 2048 维版式向量（失败返回 None，调用方回退标签级）。"""
    import base64
    import urllib.request

    try:
        with open(image_path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode("ascii")
        payload = json.dumps({"inputs": [{"image_base64": b64}]}).encode("utf-8")
        req = urllib.request.Request(
            f"{server_url.rstrip('/')}/v1/embeddings",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        resp = json.loads(urllib.request.urlopen(req, timeout=timeout).read())
        return resp["data"][0]["embedding"]
    except Exception:
        return None


# ── 版式向量软匹配（对 layout_index.json 做 k-NN）─────────────────
_INDEX_CACHE = None
_INDEX_CACHE_PATH = None

_DOC_TYPE_TO_INDEX = {
    "packing_list": "pl_mixed", "pl": "pl_mixed", "装箱单": "pl_mixed",
    "aco": "aco_non_goods", "托收": "aco_non_goods", "collection": "aco_non_goods",
    "crn": "crn_mixed", "贷记": "crn_mixed", "credit": "crn_mixed",
    "dbn": "dbn_mixed", "借记": "dbn_mixed", "debit": "dbn_mixed",
    "do": "do_mixed", "提货": "do_mixed", "delivery": "do_mixed",
    "sdn": "sdn_mixed", "发货": "sdn_mixed",
    "so": "so_mixed", "销售订单": "so_mixed", "sales_order": "so_mixed",
    "swb": "swb_mixed", "海运": "swb_mixed", "waybill": "swb_mixed", "提单": "swb_mixed",
}


def load_layout_index(index_path):
    """加载 layout_index.json（进程内缓存，避免每次匹配重复解析 94MB）。"""
    global _INDEX_CACHE, _INDEX_CACHE_PATH
    if _INDEX_CACHE is None or _INDEX_CACHE_PATH != index_path:
        with open(index_path, encoding="utf-8") as f:
            _INDEX_CACHE = json.load(f)
        _INDEX_CACHE_PATH = index_path
    return _INDEX_CACHE


def _resolve_index_doc(doc_type, index_keys):
    """把语义 doc_type 映射到 index 的单据 key；映射不上返回 None。"""
    dt = (doc_type or "").strip()
    if dt in index_keys:
        return dt
    if dt in _DOC_TYPE_TO_INDEX:
        return _DOC_TYPE_TO_INDEX[dt]
    # 模糊：index key 的关键词出现在 doc_type 里
    lowered = dt.lower()
    for key in index_keys:
        stem = key.split("_")[0]  # aco_non_goods -> aco
        if stem and (stem in lowered or lowered in stem):
            return key
    return None


def _cosine(a, b):
    dot = sum(x * y for x, y in zip(a, b))
    na = sum(x * x for x in a) ** 0.5
    nb = sum(y * y for y in b) ** 0.5
    return dot / (na * nb) if na and nb else 0.0


def match_layout(layout_vector, doc_type, index_path, top_k=3, threshold=0.75):
    """对 layout_index.json 做 k-NN 软匹配，返回 top-k 相似版式簇（不做硬归属）。

    返回 [{"cluster_id", "score", "image"}, ...]，按相似度降序；无命中返回 []。
    """
    if layout_vector is None or not index_path:
        return []
    try:
        index = load_layout_index(index_path)
    except Exception:
        return []
    idx_doc = _resolve_index_doc(doc_type, index.get("docs", {}).keys())
    if idx_doc is None:
        return []
    entries = index["docs"].get(idx_doc, [])
    scored = []
    for e in entries:
        s = _cosine(layout_vector, e["vector"])
        if s >= threshold:
            scored.append({"cluster_id": e["cluster_id"], "score": round(s, 4), "image": e["image"]})
    scored.sort(key=lambda x: -x["score"])
    return scored[:top_k]


# 单据类型 → 中文名（单据类型不含后缀；_mixed/_goods/_non_goods 是标注字段范围，非类型）
_DOC_CN = {
    "pl": "装箱单",
    "swb": "海运单",
    "aco": "托收",
    "crn": "贷记通知",
    "dbn": "借记通知",
    "do": "提货单",
    "sdn": "发货单",
    "so": "销售订单",
}

# 标注字段范围后缀 → 中文说明
_SCOPE_CN = {
    "mixed": "全字段",
    "goods": "仅货描",
    "non_goods": "仅非货描",
}

# 标注字段范围后缀 → lane 推断（mixed 全字段不限定 lane）
_SCOPE_TO_LANE = {
    "mixed": None,
    "goods": "goods",
    "non_goods": "non_goods",
}


def _doc_type_of(doc):
    """目录名（swb_mixed / aco_non_goods）→ 单据类型（swb / aco）。后缀是标注范围，非类型。"""
    if not doc:
        return ""
    if doc in _DOC_CN:
        return doc
    for t in _DOC_CN:
        if doc.startswith(t + "_"):
            return t
    return doc.split("_")[0]


def _doc_scope_of(doc):
    """目录名 → 标注范围（mixed/goods/non_goods），无后缀返回空。"""
    t = _doc_type_of(doc)
    if t and doc != t:
        return doc[len(t) + 1:]
    return ""


def doc_cn(doc):
    """单据目录名/缩写 → 中文名（去掉标注范围后缀）。"""
    return _DOC_CN.get(_doc_type_of(doc), doc or "")


# 单据类型 → 版式结构标签（glm-vision 核 8 单据代表图所得，2026-08-15）
_DOC_LAYOUT = {
    "pl": ["dense_table"],
    "swb": ["multi_block", "cross_page"],
    "aco": ["dense_table"],
    "crn": ["multi_block"],
    "dbn": ["dense_table"],
    "do": ["dense_table"],
    "sdn": ["long_table"],
    "so": ["long_table", "cross_page"],
}


def match_layout_cross(layout_vector, index_path, top_k=1, threshold=0.6):
    """跨所有单据匹配，返回最像的 top-k 版式簇（含 doc 字段）。

    用于「视觉确认单据类型」：跨单据区分度强（0.42~0.60），比 doc_type 口头声明更可靠。
    返回 [{"doc", "cluster_id", "score", "image"}, ...]；无命中返回 []。
    """
    if layout_vector is None or not index_path:
        return []
    try:
        index = load_layout_index(index_path)
    except Exception:
        return []
    scored = []
    for doc, entries in index.get("docs", {}).items():
        for e in entries:
            s = _cosine(layout_vector, e["vector"])
            if s >= threshold:
                scored.append({"doc": doc, "cluster_id": e["cluster_id"], "score": round(s, 4), "image": e["image"]})
    scored.sort(key=lambda x: -x["score"])
    return scored[:top_k]


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
