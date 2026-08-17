#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""构建新增 6 类单据（ci/bl/air/po/pi/sc）的版式向量索引片段。

与 build_index.py 的区别：源数据不是 round2 normalized 的 cluster_* 结构，
而是 goods/mixed/non_goods 三分类（train/test 目录）或 round2 的非 cluster 目录。
本脚本不做聚类，按单据类型均匀抽样图片 → qwen3-vl-embedding 编码 → 输出索引片段 json
（{"version":1,"dim":2048,"docs":{doc:[{cluster_id,image,vector}]}}），
由本地合并进 indexes/layout_index.json（8→14 类）。

用法（A800）：
    MAX_PER_DOC=300 OUT=layout_extra.json python3 build_index_extra.py
"""
import base64
import json
import os
import random
import sys
import urllib.request
from pathlib import Path

EMBED_URL = os.environ.get("EMBED_URL", "http://124.220.53.207:9030/v1/embeddings")
OUT = os.environ.get("OUT", "layout_extra.json")
MAX_PER_DOC = int(os.environ.get("MAX_PER_DOC", "300"))
IMG_EXTS = {".jpg", ".jpeg", ".png"}
RANDOM_SEED = int(os.environ.get("RANDOM_SEED", "42"))

# 单据类型 → 数据源根目录（取全部版本目录的 train/test，避免只取最新版本漏增量）
SOURCES = {
    "ci": [
        "/data/sam/Qwen2.5-VL-main/benchmark_all_doc/00_source_datasets/goods/ci",
        "/data/sam/Qwen2.5-VL-main/benchmark_all_doc/00_source_datasets/non_goods/ci",
    ],
    "bl": [
        "/data/sam/Qwen2.5-VL-main/benchmark_all_doc/00_source_datasets/goods/bl",
        "/data/sam/Qwen2.5-VL-main/benchmark_all_doc/00_source_datasets/non_goods/bl",
    ],
    "air": [
        "/data/sam/Qwen2.5-VL-main/benchmark_all_doc/00_source_datasets/mixed/air",
    ],
    "po": [
        "/data/sam/Qwen2.5-VL-main/benchmark_all_doc/00_source_datasets/mixed/po",
    ],
    "pi": [
        "/data/sam/Qwen2.5-VL-main/benchmark_all_doc/00_source_datasets/round2/20260711_latest_label_v2/normalized/pi",
    ],
    "sc": [
        "/data/sam/Qwen2.5-VL-main/benchmark_all_doc/00_source_datasets/round2/20260711_latest_label_v2/normalized/sc_mixed",
    ],
}


def collect_images(src_root: str):
    """收集源根下所有图片（含版本子目录 train/test），返回 [(abs_path, rel_to_root)]。"""
    root = Path(src_root)
    imgs = []
    for p in root.rglob("*"):
        if p.suffix.lower() in IMG_EXTS:
            imgs.append((str(p), str(p.relative_to(root))))
    return imgs


def encode_image(path: str):
    with open(path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode()
    payload = {"inputs": [{"image_base64": b64}]}
    req = urllib.request.Request(
        EMBED_URL, data=json.dumps(payload).encode(), headers={"Content-Type": "application/json"}, method="POST"
    )
    resp = json.loads(urllib.request.urlopen(req, timeout=180).read())
    return resp["data"][0]["embedding"]


def build():
    index = {"version": 1, "dim": 2048, "max_per_doc": MAX_PER_DOC, "docs": {}}
    rng = random.Random(RANDOM_SEED)
    for doc, roots in SOURCES.items():
        # 收集该单据类型全部源的全部图
        all_imgs = []
        for r in roots:
            all_imgs.extend(collect_images(r))
        if not all_imgs:
            print(f"[skip] {doc}: 无图片")
            continue
        # 均匀抽样至 MAX_PER_DOC（固定 seed 可复现）
        if len(all_imgs) > MAX_PER_DOC:
            all_imgs = rng.sample(all_imgs, MAX_PER_DOC)
        entries = []
        ok = 0
        for abs_path, rel in all_imgs:
            # cluster_id 用来源根名（如 goods_ci / non_goods_bl），image 存相对源根的路径
            src_name = None
            for r in roots:
                if abs_path.startswith(r):
                    src_name = os.path.basename(r.rstrip("/"))
                    break
            src_name = src_name or "src"
            try:
                vec = encode_image(abs_path)
            except Exception as e:
                print(f"  [err] {doc}/{rel}: {e}")
                continue
            entries.append({"cluster_id": f"{src_name}:{Path(rel).parent}", "image": rel, "vector": vec})
            ok += 1
        index["docs"][doc] = entries
        print(f"[ok] {doc}: {ok}/{len(all_imgs)} 张")
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False)
    total = sum(len(v) for v in index["docs"].values())
    print(f"\n完成：{len(index['docs'])} 单据，共 {total} 个版式向量 -> {OUT}")


if __name__ == "__main__":
    build()
