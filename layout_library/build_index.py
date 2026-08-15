#!/usr/bin/env python3
"""构建版式向量索引：遍历已聚类的近重复簇，每簇存全量（大簇均匀抽样）图片向量，产出 layout_index.json。

不做硬聚类、不选代表图、不做 centroid；每张图一个向量条目，匹配侧走 k-NN 软匹配。
用法：
    EMBED_URL=http://124.220.53.207:9030/v1/embeddings \
    SOURCE_ROOT=/path/to/normalized \
    OUT=layout_index.json \
    MAX_PER_CLUSTER=50 \
    python3 build_index.py [doc_name ...]
不给 doc_name 时处理全部 8 个单据。
"""
import os
import sys
import json
import base64
import urllib.request
from pathlib import Path

EMBED_URL = os.environ.get("EMBED_URL", "http://124.220.53.207:9030/v1/embeddings")
SOURCE_ROOT = os.environ.get("SOURCE_ROOT")  # 必填：normalized/<doc>_mixed/groups 的父目录
OUT = os.environ.get("OUT", "layout_index.json")
MAX_PER_CLUSTER = int(os.environ.get("MAX_PER_CLUSTER", "50"))
DOCS = ["aco_non_goods", "crn_mixed", "dbn_mixed", "do_mixed", "sdn_mixed", "so_mixed", "swb_mixed", "pl_mixed"]
IMG_EXTS = {".jpg", ".jpeg", ".png"}


def collect_cluster_images(cluster_dir: Path, max_per_cluster: int):
    """簇内全部图片；超过 max_per_cluster 时均匀抽样，保留版式多样性。"""
    imgs = sorted(p for p in cluster_dir.iterdir() if p.suffix.lower() in IMG_EXTS)
    if len(imgs) <= max_per_cluster:
        return imgs
    step = len(imgs) / max_per_cluster
    return [imgs[int(i * step)] for i in range(max_per_cluster)]


def encode_image(path: str):
    with open(path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode()
    payload = {"inputs": [{"image_base64": b64}]}
    req = urllib.request.Request(
        EMBED_URL, data=json.dumps(payload).encode(), headers={"Content-Type": "application/json"}, method="POST"
    )
    resp = json.loads(urllib.request.urlopen(req, timeout=180).read())
    return resp["data"][0]["embedding"]


def build(docs):
    index = {"version": 1, "dim": 2048, "max_per_cluster": MAX_PER_CLUSTER, "docs": {}}
    for doc in docs:
        doc_root = Path(SOURCE_ROOT) / doc / "groups"
        if not doc_root.exists():
            print(f"[skip] {doc}: 无 groups 目录 {doc_root}")
            continue
        entries = []
        clusters = sorted(d for d in doc_root.iterdir() if d.is_dir() and d.name.startswith("cluster_"))
        print(f"[start] {doc}: {len(clusters)} 簇")
        for cluster_dir in clusters:
            imgs = collect_cluster_images(cluster_dir, MAX_PER_CLUSTER)
            if not imgs:
                print(f"  [warn] {cluster_dir.name}: 无图片，跳过")
                continue
            ok = 0
            for img in imgs:
                try:
                    vec = encode_image(str(img))
                except Exception as e:
                    print(f"  [err] {doc}/{cluster_dir.name}/{img.name}: {e}")
                    continue
                rel = str(img.relative_to(SOURCE_ROOT))
                entries.append({"cluster_id": cluster_dir.name, "image": rel, "vector": vec})
                ok += 1
            print(f"  [ok] {cluster_dir.name}: {ok}/{len(imgs)} 张")
        index["docs"][doc] = entries
    return index


if __name__ == "__main__":
    if not SOURCE_ROOT:
        sys.exit("请设置 SOURCE_ROOT（normalized/<doc>_mixed/groups 的父目录）")
    docs = sys.argv[1:] if len(sys.argv) > 1 else DOCS
    index = build(docs)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False)
    total = sum(len(v) for v in index["docs"].values())
    print(f"\n完成：{len(index['docs'])} 单据，共 {total} 个版式向量 -> {OUT}")
