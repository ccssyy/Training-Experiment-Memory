#!/usr/bin/env python3
"""版式软匹配：给一张新图，对 layout_index.json 做 k-NN 余弦相似度检索，不做硬归属。

用法：
    INDEX=layout_index.json EMBED_URL=http://124.220.53.207:9030/v1/embeddings \
    python3 query_layout.py --doc pl_mixed --image /path/to/new.png [--top-k 3] [--threshold 0.85]
"""
import os
import sys
import json
import base64
import argparse
import urllib.request


def encode_image(path: str):
    with open(path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode()
    payload = {"inputs": [{"image_base64": b64}]}
    req = urllib.request.Request(
        os.environ.get("EMBED_URL", "http://124.220.53.207:9030/v1/embeddings"),
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    resp = json.loads(urllib.request.urlopen(req, timeout=180).read())
    return resp["data"][0]["embedding"]


def cosine(a, b):
    dot = sum(x * y for x, y in zip(a, b))
    na = sum(x * x for x in a) ** 0.5
    nb = sum(y * y for y in b) ** 0.5
    return dot / (na * nb) if na and nb else 0.0


def query(index, doc, vec, top_k=3, threshold=0.85):
    entries = index["docs"].get(doc, [])
    scored = []
    for e in entries:
        s = cosine(vec, e["vector"])
        if s >= threshold:
            scored.append({"cluster_id": e["cluster_id"], "image": e["image"], "score": round(s, 4)})
    scored.sort(key=lambda x: -x["score"])
    return scored[:top_k]


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--doc", required=True)
    ap.add_argument("--image", required=True)
    ap.add_argument("--top-k", type=int, default=3)
    ap.add_argument("--threshold", type=float, default=0.85)
    args = ap.parse_args()

    index = json.load(open(os.environ.get("INDEX", "layout_index.json"), encoding="utf-8"))
    vec = encode_image(args.image)
    hits = query(index, args.doc, vec, top_k=args.top_k, threshold=args.threshold)
    if not hits:
        print(f"[无相似版式] {args.doc} 下没有 score >= {args.threshold} 的历史版式（走 doc_type 粗推兜底）")
    else:
        for h in hits:
            print(f"{h['score']:.4f}  {h['cluster_id']}  {h['image']}")
