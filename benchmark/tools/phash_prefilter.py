#!/usr/bin/env python3
"""phash as a prefilter for same-illustration pairs: what a 64-bit hash buys before any model runs.

the neardup profile orders the corpus by clip similarity, which costs one
embedding per image before the encoder starts. a perceptual hash costs a
resize and a dct per image and no gpu. this measures, on the reprints
corpus (every printing on disk whose illustration_id occurs more than
once), how well hamming distance on that hash finds the pairs that share
an illustration, and how many candidate pairs it leaves for a model to
confirm.

phash: grayscale, 32x32 bicubic, dct-ii, the top-left 8x8 block, one bit
per coefficient above the block median (the imagehash recipe, no import).

usage (repo root, MTG_DATA set):
  python3 benchmark/tools/phash_prefilter.py --out data/phash.json
"""

from __future__ import annotations

import argparse
import json
import sqlite3
import time
from pathlib import Path

import numpy as np
from PIL import Image
from scipy.fft import dctn

import _bench_env as env


def phash64(path: Path) -> np.uint64:
    with Image.open(path) as img:
        g = img.convert("L").resize((32, 32), Image.Resampling.BICUBIC)
    coeffs = dctn(np.asarray(g, dtype=np.float64), norm="ortho")[:8, :8]
    bits = (coeffs > np.median(coeffs)).ravel()
    return np.uint64(int("".join("1" if b else "0" for b in bits), 2))


def hamming_matrix(h: np.ndarray) -> np.ndarray:
    x = h[:, None] ^ h[None, :]
    out = np.zeros(x.shape, dtype=np.uint8)
    for _ in range(64):
        out += (x & np.uint64(1)).astype(np.uint8)
        x >>= np.uint64(1)
    return out


def load_corpus() -> tuple[list[str], list[Path], dict[str, str]]:
    root = env.require_data_root()
    corpus = json.load(open(env.CORPORA / "reprints-2787.json"))
    ids = corpus["ids"]
    con = sqlite3.connect(root / "mtg.sqlite")
    ill = {}
    for oracle, illustration, uri in con.execute(
        "select oracle_id, illustration_id, image_uri from printings where image_uri is not null"
    ):
        stem = uri.rsplit("/", 1)[-1].split(".")[0].split("?")[0]
        ill[f"{stem}|{oracle}"] = illustration
    paths = []
    for key in ids:
        stem = key.split("|", 1)[0]
        paths.append(root / "images" / "normal" / "front" / stem[0] / stem[1] / f"{stem}.jpg")
    missing = [k for k in ids if k not in ill]
    if missing:
        env.die(f"{len(missing)} reprint ids have no printings row, e.g. {missing[0]}")
    return ids, paths, ill


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", required=True)
    ap.add_argument("--max-hamming", type=int, default=16)
    args = ap.parse_args()

    ids, paths, ill = load_corpus()
    t0 = time.perf_counter()
    hashes = np.array([phash64(p) for p in paths], dtype=np.uint64)
    hash_s = time.perf_counter() - t0
    n = len(ids)
    dist = hamming_matrix(hashes)
    labels = np.array([ill[k] for k in ids])
    same = labels[:, None] == labels[None, :]
    iu = np.triu_indices(n, 1)
    d, s = dist[iu], same[iu]
    total_pairs, true_pairs = int(len(d)), int(s.sum())

    thresholds = []
    for thr in range(0, args.max_hamming + 1):
        picked = d <= thr
        tp = int((picked & s).sum())
        cand = int(picked.sum())
        thresholds.append(
            {
                "hamming_le": thr,
                "candidate_pairs": cand,
                "true_pairs_found": tp,
                "precision": round(tp / cand, 4) if cand else None,
                "recall": round(tp / true_pairs, 4),
                "pairs_left_for_a_model_pct": round(100 * cand / total_pairs, 4),
            }
        )
    # the distribution of the true pairs' distances, to see where the mass is
    true_d = d[s]
    hist = {int(k): int(v) for k, v in zip(*np.unique(true_d, return_counts=True), strict=True)}
    payload = {
        "corpus": "reprints-2787",
        "n_images": n,
        "total_pairs": total_pairs,
        "true_pairs": true_pairs,
        "groups": int(len(set(labels))),
        "hash_wall_s": round(hash_s, 1),
        "hash_per_image_ms": round(1000 * hash_s / n, 2),
        "thresholds": thresholds,
        "true_pair_hamming_histogram": hist,
        "true_pair_hamming_p50": float(np.median(true_d)),
        "true_pair_hamming_p90": float(np.percentile(true_d, 90)),
        "true_pair_hamming_max": int(true_d.max()),
    }
    Path(args.out).write_text(json.dumps(payload, indent=1) + "\n")
    for t in thresholds:
        print(t)
    print(
        "true pair hamming p50/p90/max:",
        payload["true_pair_hamming_p50"],
        payload["true_pair_hamming_p90"],
        payload["true_pair_hamming_max"],
    )


if __name__ == "__main__":
    main()
