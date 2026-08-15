#!/usr/bin/env python3
"""给 85 个字段语义概念建 bge-m3 向量索引。

对每个概念的 canonical 名 + 中文名 + 所有别名分别编码，产出 concept_index.json。
匹配时字段名对索引做 k-NN，命中 entry 即归到对应概念。
用法：
    EMBED_URL=http://127.0.0.1:9033/v1/embeddings python3 build_concept_index.py
"""
import json
import os
import sys
import urllib.request

EMBED_URL = os.environ.get("EMBED_URL", "http://127.0.0.1:9033/v1/embeddings")
CONCEPTS = os.environ.get("CONCEPTS", "data/concepts.json")
OUT = os.environ.get("OUT", "../indexes/concept_index.json")
BATCH = int(os.environ.get("BATCH", "256"))


def enc_batch(texts):
    req = urllib.request.Request(
        EMBED_URL,
        data=json.dumps({"inputs": [{"text": t} for t in texts]}).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    resp = json.loads(urllib.request.urlopen(req, timeout=120).read())
    return [d["embedding"] for d in sorted(resp["data"], key=lambda x: x["index"])]


def main():
    concepts = json.load(open(CONCEPTS, encoding="utf-8"))
    texts, meta = [], []
    for c in concepts:
        for t in [c["c"], c.get("zh", "")] + c.get("aliases", []):
            if t:
                texts.append(t)
                meta.append((c["c"], t))

    entries = []
    for i in range(0, len(texts), BATCH):
        batch = texts[i : i + BATCH]
        vecs = enc_batch(batch)
        for (concept, text), vec in zip(meta[i : i + BATCH], vecs):
            entries.append({"concept": concept, "text": text, "vector": vec})
        print(f"  已编码 {min(i + BATCH, len(texts))}/{len(texts)}")

    index = {"version": 1, "dim": 1024, "entries": entries}
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False)
    n_concepts = len({e["concept"] for e in entries})
    print(f"\n完成：{len(entries)} 个文本片段 → {n_concepts} 个概念 -> {OUT}")


if __name__ == "__main__":
    main()
