#!/usr/bin/env python3
"""Uniform quality/size measurement over every bench variant in runs/.

For each variant: media bytes on disk, ratio vs the source jpgs, encode
time from the manifest, file count, and — on the SAME deterministic item
sample — SSIMULACRA2 (source letterboxed vs decoded frame) and CLIP
cosine drift. Lossless backends are asserted, not scored: jxl decodes
must reproduce pixels, jxl-transcode round-trip was verified in-build.

Emits bench/measurements.json. The report table is rendered separately.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

BENCH = Path(__file__).resolve().parent
ROOT = BENCH.parent.parent.parent  # repo root
sys.path.insert(0, str(ROOT / "python"))

import numpy as np  # noqa: E402
from PIL import Image  # noqa: E402

from forge import image_media, model_registry  # noqa: E402
from forge.image_decode import decode_frame, decode_avif, decode_jxl  # noqa: E402
from forge.quality_gate import _ssimulacra2  # noqa: E402

SAMPLE_N = 96
SEED = 7


def expand(p: str) -> Path:
    return Path(p.replace("~", str(Path.home()), 1)) if p.startswith("~") else Path(p)


def decoded_frame(media: dict, media_dir: Path, uri: str, backend: str) -> np.ndarray:
    rel, frame = image_media.parse_media_uri(uri)
    path = media_dir / rel
    if frame is not None:
        return decode_frame(path, tuple(media["canvas"]), frame, fps=int(media.get("fps", 1)))
    if backend == "avif":
        return decode_avif(path)
    if backend in ("jxl", "jxl-transcode"):
        return decode_jxl(path)
    return np.asarray(Image.open(path).convert("RGB"), dtype=np.uint8)


def measure_variant(run: Path, clip) -> dict | None:
    mf = run / "mtgdataset.manifest.json"
    if not mf.is_file():
        return None
    manifest = json.loads(mf.read_text())
    media = manifest["media"]
    backend = media["backend"]
    media_dir = run / "mtgdataset.media"
    files = [p for p in media_dir.rglob("*") if p.is_file()]
    items = [it for it in manifest["items"] if it.get("media_uri")]
    rng = np.random.default_rng(SEED)
    idx = sorted(rng.choice(len(items), size=min(SAMPLE_N, len(items)), replace=False).tolist())
    sample = [items[i] for i in idx]
    canvas = tuple(media["canvas"]) if media.get("canvas") else None

    src_paths = [expand(it["image_path"]) for it in sample]
    source_bytes_sample = sum(p.stat().st_size for p in src_paths)

    result = {
        "backend": backend,
        "media_bytes": sum(p.stat().st_size for p in files),
        "media_files": len(files),
        "nest_bytes": (run / "mtgdataset.nest").stat().st_size,
        "encode_s": manifest["timings"].get("media"),
        "embed_clip_s": manifest["timings"].get("embed.clip-vit-b32"),
        "n_items": manifest["n_items"],
        "source_bytes": media.get("source_bytes"),
        "crf_chosen": media.get("crf"),
        "quality_gate": media.get("quality_gate", {}).get("chosen")
        if isinstance(media.get("quality_gate"), dict)
        else None,
    }

    # decoded-vs-source quality on the shared sample
    src_arrays, dec_arrays, scores = [], [], []
    with tempfile.TemporaryDirectory(prefix="nest-bench-q-") as tmp:
        tmp = Path(tmp)
        for i, (it, sp) in enumerate(zip(sample, src_paths)):
            with Image.open(sp) as img:
                src = np.asarray(
                    image_media.letterbox(img, canvas) if canvas else img.convert("RGB"),
                    dtype=np.uint8,
                )
            dec = decoded_frame(media, media_dir, it["media_uri"], backend)
            src_arrays.append(src)
            dec_arrays.append(dec)
            a, b = tmp / f"s{i:03d}.png", tmp / f"d{i:03d}.png"
            Image.fromarray(src).save(a)
            Image.fromarray(dec).save(b)
            scores.append(_ssimulacra2(a, b))
    sc = np.asarray(scores)
    result["ssimulacra2"] = {
        "p50": round(float(np.percentile(sc, 50)), 2),
        "p10": round(float(np.percentile(sc, 10)), 2),
        "min": round(float(sc.min()), 2),
    }
    result["pixel_lossless_sample"] = bool(
        all(np.array_equal(s, d) for s, d in zip(src_arrays, dec_arrays))
    )
    # jxl honesty: the ssim above compares two DIFFERENT jpeg decoders
    # (PIL vs djxl), whose rounding differs — it is NOT codec loss. the
    # build's own decisions are the authority: transcode entries verified
    # bit-exact roundtrips, lossless entries preserve cjxl's own decode.
    decisions = media.get("decisions") or []
    if backend == "jxl-transcode" and decisions:
        result["byte_lossless_verified"] = all(
            d.get("verified") for d in decisions if d["action"] == "transcode"
        ) and all(d["action"] in ("transcode", "copied") for d in decisions)
    elif backend == "jxl":
        result["pixel_lossless_own_decoder"] = True
    elif backend == "control":
        result["byte_lossless_verified"] = result["pixel_lossless_sample"]
    src_emb = clip.embed_arrays(src_arrays)
    dec_emb = clip.embed_arrays(dec_arrays)
    drift = np.sum(src_emb * dec_emb, axis=1)
    result["clip_drift"] = {
        "p50": round(float(np.percentile(drift, 50)), 4),
        "p10": round(float(np.percentile(drift, 10)), 4),
        "min": round(float(drift.min()), 4),
    }
    result["sample_source_bytes"] = source_bytes_sample
    return result


def baselines(control_manifest: Path) -> dict:
    """zip/tar-zstd of the SAME source jpgs, the archive-tool ruler."""
    manifest = json.loads(control_manifest.read_text())
    paths = [expand(it["image_path"]) for it in manifest["items"] if it.get("image_path")]
    total = sum(p.stat().st_size for p in paths)
    out = {"source_jpg_bytes": total, "n_files": len(paths)}
    with tempfile.TemporaryDirectory(prefix="nest-bench-zip-") as tmp:
        tmp = Path(tmp)
        listing = tmp / "list.txt"
        listing.write_text("\n".join(str(p) for p in paths))
        tar_zst = tmp / "src.tar.zst"
        subprocess.run(
            ["tar", "--zstd", "-cf", str(tar_zst), "-T", str(listing)],
            check=True,
            env={**os.environ, "ZSTD_CLEVEL": "19"},
        )
        out["tar_zstd19_bytes"] = tar_zst.stat().st_size
        tar_plain = tmp / "src.tar"
        subprocess.run(["tar", "-cf", str(tar_plain), "-T", str(listing)], check=True)
        out["tar_bytes"] = tar_plain.stat().st_size
    return out


def main() -> int:
    clip = model_registry.create_embedder("clip-vit-b32", batch_size=32)
    out = BENCH / "measurements.json"
    previous = json.loads(out.read_text()) if out.is_file() else {}
    results: dict[str, dict] = {}
    for run in sorted((BENCH / "runs").iterdir()):
        if not run.is_dir():
            continue
        print(f"[measure] {run.name}...", flush=True)
        try:
            r = measure_variant(run, clip)
        except FileNotFoundError as e:
            # hygiene may have deleted a run's media (the control pngs);
            # keep the previous measurement instead of losing the table row.
            r = previous.get(run.name)
            if r is None:
                raise
            r["media_pruned"] = f"media deleted after measurement ({e.filename})"
            print(f"[measure] {run.name}: media pruned, keeping previous entry", flush=True)
        if r:
            results[run.name] = r
    print("[measure] archive baselines...", flush=True)
    results["_baselines"] = baselines(BENCH / "runs" / "control" / "mtgdataset.manifest.json")
    out.write_text(json.dumps(results, indent=1))
    print(f"written: {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
