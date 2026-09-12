#!/usr/bin/env python3
"""Deep lossless battery over the same 2048 source JPEGs of the variant bench.

Two honest classes, never conflated:
  byte-reversible : the ORIGINAL JPEG bytes are reconstructible bit-exact
                    (jxl-transcode; verified by djxl round-trip sha256).
  pixel-exact     : same decoded pixels, different bytes; the original file
                    is NOT reconstructible (jpegtran/jpegoptim re-save,
                    pixel-domain codecs over the decoded frames).

Also runs the "invented" path the plan called for: lossless VIDEO (ffv1,
x264 qp0) over the letterboxed frames, in source order and in the
semantic cluster order, to measure whether inter prediction over ordered
frames can beat per-image lossless — published whatever the number is.

Outputs one folder per generation under bench/lossless/ and
bench/lossless/results.json.
"""

from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
import time
from pathlib import Path

BENCH = Path(__file__).resolve().parent
OUT = BENCH / "lossless"
CONTROL = BENCH / "runs" / "control"
CLUSTER_MANIFEST = BENCH / "runs" / "av1-cluster-crf35" / "mtgdataset.manifest.json"
JPEGTRAN = "/opt/homebrew/opt/mozjpeg/bin/jpegtran"
VERIFY_N = 64


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def src_paths() -> list[Path]:
    manifest = json.loads((CONTROL / "mtgdataset.manifest.json").read_text())
    home = str(Path.home())
    out = []
    for it in manifest["items"]:
        p = it["image_path"]
        out.append(Path(p.replace("~", home, 1) if p.startswith("~") else p))
    return out


def run_per_file(name: str, paths: list[Path], cmd_fn, ext: str) -> dict:
    d = OUT / name
    d.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    for i, p in enumerate(paths):
        dst = d / f"{i:06d}{ext}"
        if dst.exists():
            continue
        r = subprocess.run(cmd_fn(p, dst), capture_output=True)
        if r.returncode != 0:
            raise RuntimeError(f"{name}: {p}: {r.stderr.decode()[:200]}")
    total = sum(f.stat().st_size for f in d.iterdir() if f.is_file())
    return {"bytes": total, "files": len(paths), "encode_s": round(time.time() - t0, 1)}


def verify_jxl_roundtrip(name: str, paths: list[Path]) -> int:
    d = OUT / name
    ok = 0
    tmp = OUT / "_verify"
    tmp.mkdir(exist_ok=True)
    for i in range(0, len(paths), max(1, len(paths) // VERIFY_N)):
        back = tmp / "back.jpg"
        r = subprocess.run(
            ["djxl", str(d / f"{i:06d}.jxl"), str(back)], capture_output=True
        )
        if r.returncode == 0 and sha(back) == sha(paths[i]):
            ok += 1
    shutil.rmtree(tmp)
    return ok


def verify_pixels(name: str, paths: list[Path], ext: str) -> int:
    import numpy as np
    from PIL import Image

    d = OUT / name
    ok = 0
    for i in range(0, len(paths), max(1, len(paths) // 32)):
        a = np.asarray(Image.open(paths[i]).convert("RGB"))
        b = np.asarray(Image.open(d / f"{i:06d}{ext}").convert("RGB"))
        if a.shape == b.shape and np.array_equal(a, b):
            ok += 1
    return ok


def video_row(tag: str, codec_args: list[str], order: list[int] | None, n: int) -> dict:
    png_dir = CONTROL / "mtgdataset.media" / "mtgdataset-png"
    seq = order if order is not None else list(range(n))
    lst = OUT / f"_{tag}.txt"
    lst.write_text("".join(f"file '{png_dir / f'{i:06d}.png'}'\n" for i in seq))
    dst = OUT / f"video-{tag}.mkv"
    t0 = time.time()
    r = subprocess.run(
        ["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-r", "1",
         "-i", str(lst), *codec_args, str(dst)],
        capture_output=True,
    )
    lst.unlink()
    if r.returncode != 0:
        return {"error": r.stderr.decode()[:200]}
    return {"bytes": dst.stat().st_size, "files": 1, "encode_s": round(time.time() - t0, 1)}


def main() -> int:
    OUT.mkdir(exist_ok=True)
    paths = src_paths()
    n = len(paths)
    source = sum(p.stat().st_size for p in paths)
    results: dict[str, dict] = {"_source": {"bytes": source, "files": n}}

    print("[1/8] jxl-transcode -e 9 (byte-reversible)", flush=True)
    r = run_per_file(
        "jxl-e9", paths,
        lambda p, d: ["cjxl", str(p), str(d), "--lossless_jpeg=1", "-e", "9"], ".jxl",
    )
    r["class"] = "byte-reversible"
    r["verified"] = f"{verify_jxl_roundtrip('jxl-e9', paths)}/{VERIFY_N} roundtrips sha256-ok"
    results["jxl-transcode-e9"] = r

    print("[2/8] jpegtran -optimize (pixel-exact)", flush=True)
    r = run_per_file(
        "jpegtran-opt", paths,
        lambda p, d: [JPEGTRAN, "-copy", "none", "-optimize", "-outfile", str(d), str(p)], ".jpg",
    )
    r["class"] = "pixel-exact"
    r["verified"] = f"{verify_pixels('jpegtran-opt', paths, '.jpg')}/32 pixel-identical"
    results["jpegtran-optimize"] = r

    print("[3/8] jpegtran -progressive (pixel-exact)", flush=True)
    r = run_per_file(
        "jpegtran-prog", paths,
        lambda p, d: [JPEGTRAN, "-copy", "none", "-optimize", "-progressive",
                      "-outfile", str(d), str(p)], ".jpg",
    )
    r["class"] = "pixel-exact"
    r["verified"] = f"{verify_pixels('jpegtran-prog', paths, '.jpg')}/32 pixel-identical"
    results["jpegtran-progressive"] = r

    print("[4/8] jpegoptim --strip-all (pixel-exact)", flush=True)
    d = OUT / "jpegoptim"
    d.mkdir(exist_ok=True)
    t0 = time.time()
    for i, p in enumerate(paths):
        dst = d / f"{i:06d}.jpg"
        if not dst.exists():
            shutil.copy(p, dst)
    subprocess.run(
        ["jpegoptim", "-q", "--strip-all", *[str(d / f"{i:06d}.jpg") for i in range(n)]],
        capture_output=True,
    )
    results["jpegoptim-strip"] = {
        "bytes": sum(f.stat().st_size for f in d.iterdir()),
        "files": n,
        "encode_s": round(time.time() - t0, 1),
        "class": "pixel-exact",
        "verified": f"{verify_pixels('jpegoptim', paths, '.jpg')}/32 pixel-identical",
    }

    print("[5/8] webp lossless (pixel-domain)", flush=True)
    r = run_per_file(
        "webp-lossless", paths,
        lambda p, d: ["cwebp", "-quiet", "-lossless", "-z", "6", str(p), "-o", str(d)], ".webp",
    )
    r["class"] = "pixel-domain (decoded)"
    results["webp-lossless"] = r

    print("[6/8] zstd-19 over jxl-transcode output (double compression)", flush=True)
    jd = BENCH / "runs" / "jxl-transcode" / "mtgdataset.media" / "mtgdataset-jxl"
    tar = OUT / "jxl-plus-zstd.tar.zst"
    t0 = time.time()
    subprocess.run(
        ["tar", "--zstd", "-cf", str(tar), "-C", str(jd), "."],
        capture_output=True, env={"ZSTD_CLEVEL": "19", "PATH": "/opt/homebrew/bin:/usr/bin:/bin"},
    )
    results["jxl-transcode+zstd19"] = {
        "bytes": tar.stat().st_size, "files": 1,
        "encode_s": round(time.time() - t0, 1), "class": "byte-reversible",
    }

    perm = json.loads(CLUSTER_MANIFEST.read_text())["media"].get("order_permutation")

    print("[7/8] lossless video ffv1: source order + cluster order", flush=True)
    results["video-ffv1-srcorder"] = {
        **video_row("ffv1-srcorder", ["-c:v", "ffv1", "-level", "3"], None, n),
        "class": "pixel-domain (decoded)",
    }
    results["video-ffv1-clusterorder"] = {
        **video_row("ffv1-clusterorder", ["-c:v", "ffv1", "-level", "3"], perm, n),
        "class": "pixel-domain (decoded)",
    }

    print("[8/8] lossless video x264 qp0 inter, cluster order", flush=True)
    results["video-x264qp0-clusterorder"] = {
        **video_row(
            "x264qp0-clusterorder",
            ["-c:v", "libx264", "-qp", "0", "-preset", "medium", "-pix_fmt", "yuv444p"],
            perm, n,
        ),
        "class": "pixel-domain (decoded, yuv444)",
    }

    for k, v in results.items():
        if k != "_source" and "bytes" in v:
            v["ratio_vs_source"] = round(source / v["bytes"], 3)
    (OUT / "results.json").write_text(json.dumps(results, indent=1))
    print(json.dumps(results, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
