#!/usr/bin/env python3
"""Render bench/measurements.json into bench/table.md (baselines + variant
table only, plain style). The curated report lives in ../RESULTS.md and is
maintained by hand; this script never overwrites it."""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

BENCH = Path(__file__).resolve().parent
OUT = BENCH / "table.md"

ORDER = [
    "control",
    "jxl-transcode",
    "jxl-lossless",
    "av1-v02-crf35-s8",
    "av1-still-s6-crf35",
    "av1-fps30-intra-crf35",
    "av1-inter-crf35",
    "av1-fps30-inter-crf35",
    "av1-cluster-crf35",
    "av1-auto-dualgate",
    "avif-crf35",
    "selfcontained-still-s6",
]


def lossless_cell(r: dict) -> str:
    if r.get("byte_lossless_verified"):
        return "bytes"
    if r.get("pixel_lossless_own_decoder"):
        return "pixels"
    return "bytes" if r.get("pixel_lossless_sample") else "nao"


def mb(n: int | None) -> str:
    return f"{n / 1e6:.1f}" if n else "-"


def row(name: str, r: dict, src: int) -> str:
    s2, dr = r["ssimulacra2"], r["clip_drift"]
    ratio = src / r["media_bytes"] if r["media_bytes"] else 0
    crf = f" (crf={r['crf_chosen']})" if r.get("crf_chosen") not in (None, 35) else ""
    return (
        f"| {name}{crf} | {mb(r['media_bytes'])} | {ratio:.2f}x | {r['media_files']} "
        f"| {r['encode_s']} | {s2['p50']} | {s2['p10']} | {s2['min']} "
        f"| {dr['p10']} | {lossless_cell(r)} |"
    )


def main() -> None:
    m = json.loads((BENCH / "measurements.json").read_text())
    base = m.pop("_baselines")
    src = base["source_jpg_bytes"]

    lines = [
        f"Gerado em {date.today().isoformat()} a partir de measurements.json.",
        "",
        "| baseline | MB | ratio |",
        "|---|---:|---:|",
        f"| fonte (JPEG) | {mb(src)} | 1.00x |",
        f"| tar | {mb(base['tar_bytes'])} | {src / base['tar_bytes']:.2f}x |",
        f"| tar + zstd-19 | {mb(base['tar_zstd19_bytes'])} | {src / base['tar_zstd19_bytes']:.2f}x |",
        "",
        "| variante | midia MB | ratio | arquivos | encode s | ssim2 p50 | p10 | min | deriva clip p10 | sem perda |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    for name in ORDER:
        if name in m:
            lines.append(row(name, m[name], src))
    for name in sorted(set(m) - set(ORDER)):
        lines.append(row(name, m[name], src))
    lines.append("")
    OUT.write_text("\n".join(lines) + "\n")
    print(f"written: {OUT}")


if __name__ == "__main__":
    main()
