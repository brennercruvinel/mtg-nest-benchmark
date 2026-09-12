# mtg-nest-benchmark

38,627 magic card scans in one searchable file, and the numbers for every way we tried to make that file smaller.

## what this is

the benchmark and the artifacts of compressing and indexing the magic: the gathering card image corpus into single-file `.nest` containers with the [nest](https://github.com/hoffresearch/nest) engine. the source is 3.975 GB of jpeg (38,627 cards, normal/front, from the scryfall bulk data via the spellbook app cache). every experiment lives under `benchmark/experiments/NN-slug/` with a `results.json`, and `RESULTS.md` is rendered from those files. the product recipes are the four toml files in `profiles/`.

one `.nest` carries codec-compressed media, the int8 vectors of two embedding spaces, an hnsw index, bm25, a graph and the source spans, all in one mmap-able, content-addressed file. that is the product thesis: one file instead of a directory of media plus a sidecar index. the closest relative I know of is lance, which has blob semantics, vectors and full text search but is a directory of fragments, not a file; sqlite-vec plus fts5 is single-file but has no ann and no media; webdataset, ffcv and tfrecord have no search at all. so the `.nest` is a retrieval-ready archive, and the cost of that property measured here is 3.0%: 39.4 MB of indexes, text and vectors over a 1.317 GB media blob on the still build.

## the results in five lines

lossless has a ceiling of 1.12x. jpeg is already entropy coded, so tar plus zstd-19 gives 1.00x and the only real lossless gain is the byte-reversible repack of jpeg xl (`cjxl --lossless_jpeg=1`), which returns the original jpeg bit for bit and saves 10.3% at effort 7 (11.0% at effort 9). lossless video with semantic ordering, the "invented" path, loses by 3.3 to 3.8x against the source. this became the archive profile: 3.606 GB, 38,627 sha256 round-trips verified.

lossy gains come from two independent levers. the encoder mode: `tune=still` in svt-av1 gives +10.9 ssimulacra2 points over the v0.2 build for +10% bytes at the same crf, and the forge had been falling back to a lower tune in silence. and inter-frame redundancy: inter prediction with gop 16 and scene-cut detection off saves 29% on a corpus of same-artwork reprints, but on unique cards it trades 16 quality points for 11% of bytes, so the gop probe now vetoes it per segment and records why.

retrieval does not fall where the eye falls. raising crf from 35 to 50 takes the file from 1.374 GB to 533 MB and text-to-image search through clip loses nothing we can measure on 100 queries. the cosine drift gate that would have vetoed that file measures signal stability, not utility.

quality matched, avif from libaom beats the svt-av1 all-intra stream by 12.4% on the sample and 13.0% on the full `.nest`, at the price of a 4 to 10x slower embed at build time.

single-file costs 3%, and the sidecar and embedded twins share the same content_hash, so citations survive a re-encode and a backend swap.

## what the literature calls this

the thing experiment 09 exploits has a classic name. karadimitriou (lsu, 1996) called it set redundancy: the information shared across a collection of similar images that no single-image codec can see. the practical form of exploiting it is to lay the images out as frames of a pseudo-video and let a video encoder's inter prediction do the work, which is the photo-album coding line of 2010 to 2016 (minimum spanning tree ordering, hevc-based album coders). `order=cluster` plus `gop=inter` in the nest forge is that lever, and the 29% on corpus B is its measurement here. two honest caveats: the corpus B matrix compares bytes at a fixed crf, not at matched quality, and part of the inter gain comes from the chrome every card shares (frame, text box), not the repeated art, since grouped and shuffled orderings differ by only 1.8 MB. on the lossless side, wu, sun, yang, zeng and wu (ieee tip 2016) report more than 31% lossless savings on jpeg photo collections via pseudo-video in the dct domain, which is well past the 1.12x ceiling of experiment 08. there is no open implementation of that method, so what this repository states is the ceiling with available tools, and that paper is the reference anyone has to beat or reproduce before calling the ceiling general. see `docs/references.md`.

experiment 13 keeps three measurements apart that are usually collapsed into one: fidelity (ssimulacra2), signal stability (cosine drift of the embedding between source and decoded frame) and task utility (hit@k of text-to-image search). the standards world calls this image and video coding for machines (icm and vcm), or task-aware compression, and the observation that feature-space distance is a poor predictor of downstream task accuracy is a recurring one in that literature. so the finding that drift does not predict utility is reported here as a confirmation on this corpus, not as something we discovered. what it changes for the product is concrete: a retrieval-only gate needs a hit@k floor, not a cosine one.

## layout

```
profiles/                 the four product recipes (stills, neardup, archive, retrieval)
benchmark/experiments/    NN-slug/{README.md, results.json, table.md, specs/, samples/}
benchmark/corpora/        the six id lists (which cards each sample contains)
benchmark/tools/          render_report, export_corpora, measure_variants, lossless_battery, gen_specs, promote, sanitize_sidecars
release/v0.3/<profile>/   build.lock.json, stripped manifest, SHA256SUMS, CITATION_KEY (the .nest itself is not in git)
docs/                     methodology, hypotheses, references, roadmap, glossary, changelog, archive/
RESULTS.md                generated, do not edit by hand
```

the `.nest` files, the loose media and the embed caches are gitignored. `candidates/` holds unpromoted full-corpus builds and `benchmark/runs/` the fifteen sample builds; both stay outside git.

## reproducing

two environment variables and the nest cli. `MTG_DATA` points at the spellbook data root (`mtg.sqlite` plus `images/normal/front/`), `NEST_REPO` at a checkout of hoffresearch/nest. the forge expands `${VAR}` in spec paths since nest pull request #131 (merged 2026-09-12), and keeps its embed cache under `${XDG_CACHE_HOME:-~/.cache}/nest` since #133; use a checkout at or after commit 7dc3cc78.

```
export MTG_DATA=/path/to/Spellbook/data
export NEST_REPO=/path/to/nest
nest build --spec profiles/stills.toml          # or neardup, archive, retrieval
python3 benchmark/tools/render_report.py --check
```

a build lands in `candidates/<profile>/`; `benchmark/tools/promote.py` copies a validated one into `release/<version>/<profile>/` with the stripped manifest, the sums and the citation key. the sample experiments are `nest build --spec benchmark/experiments/02-av1-variants/specs/<variant>.toml --sample 2048`, then `measure_variants.py` over `benchmark/runs/`. `render_report.py --check` is the ci gate: it fails when `RESULTS.md` or any `table.md` is stale against the json.

the source data is scryfall bulk data (https://scryfall.com/docs/api/bulk-data), fetched by the spellbook app into its local cache; nothing was downloaded for the benchmark itself.

## the corpora are id lists

no image bytes are tracked. each file in `benchmark/corpora/` is a list of forge item keys (`img_id|oracle_id`) with the rule that produced it, so anyone with the sqlite can rebuild the exact sample. the 2048-card sample is evenly spaced over the rows sorted by (img_id, oracle_id), not seeded; the 96 quality frames and the 100 utility queries are `numpy.random.default_rng(7)` draws; the 2787 reprints are the printings whose illustration_id occurs more than once among the files on disk. `benchmark/corpora/README.md` has the details.

## artifacts

the five full-corpus `.nest` files and the sample runs are hosted on the hugging face dataset `hoffresearch/mtg-nest-benchmark`, private for now. `release/v0.3/<profile>/SHA256SUMS` pins the bytes and `CITATION_KEY` pins the identity read from inside the file with `nest inspect --json`.

## citing

`CITATION.cff` has the metadata. the citation key of a specific file is its content_hash: the two v0.3 releases share `sha256:c993ceda5b42...` (they are twins, same text and vectors, different media), the three candidates of experiment 13 share `sha256:cb8fdf8f13fa...` (the rename of the chunker changed it, as identity n3 says it should). a zenodo doi comes when the repository goes public, since zenodo's github integration needs a public repository.

## license

license: to be decided by the maintainer. the card images belong to wizards of the coast and are served by scryfall under their terms; this repository tracks no image bytes.

## status

v0.3, 2026-09-12. two profiles released (neardup, archive), three candidates measured and not promoted (av1 crf40, av1 crf50, avif q48), the roadmap in `docs/roadmap.md`.
