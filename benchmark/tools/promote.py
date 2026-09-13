#!/usr/bin/env python3
"""promote a validated candidate build to release/<version>/<profile>/.

what a release dir holds:
  mtgdataset.nest    the artifact itself (gitignored, hosted on hugging face)
  build.lock.json    the forge build lock (packages, tools, models, resolved spec)
  manifest.json      the forge manifest with items[] stripped
  items.jsonl.gz     the stripped items[], one json object per line (gitignored)
  SHA256SUMS         sha256 of the .nest and of every sidecar above
  CITATION_KEY       identity of the file, read from the .nest with `nest inspect --json`

subcommands:
  promote  <candidate-dir> <version> <profile> [--dry-run] [--force]
           copies the .nest, strips the manifest, writes the sums and the key.
           refuses to overwrite an existing release dir unless --force.
  strip    <manifest.json> <out-dir>   only the manifest split (used to convert
           legacy release sidecars in place).
  key      <file.nest> [out]           only CITATION_KEY (stdout when out is omitted).
  sums     <release-dir>               rewrite SHA256SUMS for an existing release dir.

the candidate dir is what the forge wrote: <name>.nest, <name>.manifest.json,
<name>.build.lock.json. `nest` must be on PATH (or NEST_BIN set).

usage (repo root):
  python3 benchmark/tools/promote.py promote candidates/v03-retrieval-crf50 v0.3 retrieval --dry-run
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _bench_env as env  # noqa: E402

NEST_NAME = "mtgdataset.nest"
SIDECARS = ("build.lock.json", "manifest.json", "items.jsonl.gz")
KEY_FIELDS = ("content_hash", "file_hash", "chunker_version", "title", "n_chunks")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 24), b""):
            h.update(chunk)
    return h.hexdigest()


def nest_bin() -> str:
    b = os.environ.get("NEST_BIN") or shutil.which("nest")
    if not b:
        env.die("nest cli not found; put it on PATH or export NEST_BIN=/path/to/nest")
    return b


def inspect(nest: Path) -> dict:
    r = subprocess.run([nest_bin(), "inspect", "--json", str(nest)], capture_output=True, text=True)
    if r.returncode != 0:
        env.die(f"nest inspect failed on {env.rel(nest)}: {r.stderr.strip()[:300]}")
    return json.loads(r.stdout)


def nest_version() -> str:
    r = subprocess.run([nest_bin(), "--version"], capture_output=True, text=True)
    return r.stdout.strip() or "unknown"


def citation_key(nest: Path) -> str:
    info = inspect(nest)
    man = info.get("manifest", {})
    values = {
        "content_hash": info.get("content_hash"),
        "file_hash": info.get("file_hash"),
        "chunker_version": man.get("chunker_version"),
        "title": man.get("title"),
        "n_chunks": info.get("n_chunks", man.get("n_chunks")),
    }
    missing = [k for k in KEY_FIELDS if values[k] in (None, "")]
    if missing:
        env.die(f"nest inspect did not report {missing} for {env.rel(nest)}")
    lines = [f"{k} = {values[k]}" for k in KEY_FIELDS]
    lines.append(f"built_with = {nest_version()}")
    lines.append("read_with = nest inspect --json")
    return "\n".join(lines) + "\n"


def strip_manifest(src: Path, out_dir: Path, dry_run: bool = False) -> tuple[int, int]:
    """write out_dir/manifest.json (items[] replaced by a pointer) and items.jsonl.gz."""
    doc = json.loads(src.read_text())
    items = doc.pop("items", [])
    doc["items"] = {
        "stripped_to": "items.jsonl.gz",
        "n": len(items),
        "fields": sorted({k for it in items[:1] for k in it}),
    }
    if dry_run:
        return len(items), 0
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "manifest.json").write_text(json.dumps(doc, indent=1, sort_keys=True) + "\n")
    with gzip.open(out_dir / "items.jsonl.gz", "wt", compresslevel=9) as f:
        for it in items:
            f.write(json.dumps(it, sort_keys=True) + "\n")
    return len(items), (out_dir / "items.jsonl.gz").stat().st_size


def write_sums(release_dir: Path) -> str:
    lines = []
    for name in (NEST_NAME, *SIDECARS):
        p = release_dir / name
        if p.is_file():
            lines.append(f"{sha256(p)}  {name}")
    text = "\n".join(lines) + "\n"
    (release_dir / "SHA256SUMS").write_text(text)
    return text


def candidate_files(cand: Path) -> tuple[Path, Path, Path]:
    nests = sorted(cand.glob("*.nest"))
    if len(nests) != 1:
        env.die(f"{env.rel(cand)}: expected exactly one .nest, found {len(nests)}")
    nest = nests[0]
    stem = nest.stem
    manifest = cand / f"{stem}.manifest.json"
    lock = cand / f"{stem}.build.lock.json"
    for p in (manifest, lock):
        if not p.is_file():
            env.die(f"{env.rel(cand)}: missing {p.name}")
    return nest, manifest, lock


def cmd_promote(args) -> int:
    cand = Path(args.candidate)
    nest, manifest, lock = candidate_files(cand)
    dest = env.RELEASE / args.version / args.profile
    if dest.exists() and any(dest.iterdir()) and not args.force:
        env.die(f"{env.rel(dest)} exists and is not empty; pass --force to overwrite")
    info = inspect(nest)
    print(f"candidate: {env.rel(cand)}")
    print(f"  nest: {nest.name} {nest.stat().st_size} bytes, content_hash {info.get('content_hash')}")
    print(
        f"  title: {info.get('manifest', {}).get('title')}; chunker {info.get('manifest', {}).get('chunker_version')}"
    )
    n_items, _ = strip_manifest(manifest, dest, dry_run=True)
    print(f"  manifest: {manifest.name} ({manifest.stat().st_size} bytes, {n_items} items to strip)")
    print(f"destination: {env.rel(dest)}")
    print("  files: " + ", ".join((NEST_NAME, *SIDECARS, "SHA256SUMS", "CITATION_KEY")))
    if args.dry_run:
        print("dry run: nothing written")
        print("CITATION_KEY would read:")
        print(citation_key(nest), end="")
        return 0
    dest.mkdir(parents=True, exist_ok=True)
    shutil.copy2(nest, dest / NEST_NAME)
    shutil.copy2(lock, dest / "build.lock.json")
    strip_manifest(manifest, dest)
    (dest / "CITATION_KEY").write_text(citation_key(dest / NEST_NAME))
    write_sums(dest)
    print(f"promoted to {env.rel(dest)}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("promote", help="candidate dir -> release/<version>/<profile>")
    p.add_argument("candidate")
    p.add_argument("version")
    p.add_argument("profile")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--force", action="store_true")
    s = sub.add_parser("strip", help="split a manifest into manifest.json + items.jsonl.gz")
    s.add_argument("manifest")
    s.add_argument("out_dir")
    k = sub.add_parser("key", help="print or write CITATION_KEY for a .nest")
    k.add_argument("nest")
    k.add_argument("out", nargs="?")
    m = sub.add_parser("sums", help="rewrite SHA256SUMS of a release dir")
    m.add_argument("release_dir")
    args = ap.parse_args()
    if args.cmd == "promote":
        return cmd_promote(args)
    if args.cmd == "strip":
        n, size = strip_manifest(Path(args.manifest), Path(args.out_dir))
        print(f"stripped {n} items into {env.rel(Path(args.out_dir) / 'items.jsonl.gz')} ({size} bytes)")
        return 0
    if args.cmd == "key":
        text = citation_key(Path(args.nest))
        if args.out:
            Path(args.out).write_text(text)
            print(f"written: {env.rel(Path(args.out))}")
        else:
            print(text, end="")
        return 0
    if args.cmd == "sums":
        print(write_sums(Path(args.release_dir)), end="")
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
