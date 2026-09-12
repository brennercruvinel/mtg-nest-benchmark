# changelog

the format follows keep a changelog. versions are those of the `.nest` releases under `release/`.

## [unreleased]

nothing yet. the open items are in `docs/roadmap.md`; the next entry is expected to carry the mtgdataset rebuild of the two releases and the avif source_bytes fix.

## [0.3.0] - 2026-09-12

the first version of the benchmark as a repository. the measurements are those of 2026-08-31 to 2026-09-03; what changed on 2026-09-12 is the structure and the numbers that were wrong.

### added

- numbered experiment directories under `benchmark/experiments/`, each with a `results.json` (exact bytes, provenance status measured or transcribed) and a readme with hypothesis, method and verdict.
- `benchmark/tools/render_report.py`, which renders `RESULTS.md` and every `table.md` from the json; `--check` is the ci gate.
- the six corpus id lists in `benchmark/corpora/` and `export_corpora.py` to regenerate them from the sqlite.
- four product profiles in `profiles/` (stills, neardup, archive, retrieval) with `${MTG_DATA}` sources.
- `release/v0.3/{neardup,archive}/` with the build lock, the stripped manifest, `SHA256SUMS` and `CITATION_KEY`; `promote.py` produces them from a candidate.
- `sanitize_sidecars.py`, which rewrites the data root and the nest checkout in every sidecar to `${MTG_DATA}` and `${NEST_REPO}` so no tracked file names a machine.
- `docs/`: methodology, hypotheses, references, roadmap, glossary, this changelog, and the 2026-09-03 report archived verbatim with a supersession note.
- `CITATION.cff` and `.zenodo.json`. the doi is issued when the repository goes public, since zenodo's github integration needs a public repository.

### changed

- units. bytes are stored exact and MB and GB are decimal (1e6, 1e9). the 2026-09-03 report used `du` output in binary units labelled as GB.
- every full-corpus row shows two ratios, on the `.nest` and on the media blob; the old report mixed the two bases.
- the three self-contained sample variants that measurements.json carried and the old table omitted (selfcontained-neardup, selfcontained-jxl-transcode, selfcontained-avif) are in experiment 02.
- experiment 11 carries all 19 encoder rows, the old table showed 12.

### fixed

unit errors corrected against the 2026-09-11 audit, all in the old report and its tables:

- jxl-transcode e7 is 1.115x (211,018,809 / 189,231,744), not 1.124x; 1.124x is e9. the prose "-11.1%" was e9 at -11.0%; e7 is -10.3%.
- the lossless video rows lose 3.3 to 3.8x against the source jpeg; against jxl-transcode e9 the loss is 3.7 to 4.3x.
- retrieval crf40 is 980,715,452 bytes = 0.981 GB (the report said 0.935 GB, which is MiB), 4.05x on the `.nest` and 4.22x on the media; "-31% vs still" is -27.7% and "-74% vs source" was against the archive.
- retrieval crf50 is 532,671,548 bytes = 0.533 GB (not 0.508), 7.46x on the `.nest` and 8.06x on the media.
- avif q48 is 1,195,973,116 bytes = 1.196 GB (not 1.101, which was the media blob in MiB), 3.32x on the `.nest` and 3.45x on the media; against neardup it is -13.0% on the `.nest`, so the i-frame prediction of -12.4% held and did not "materialize larger".
- the raw cache is 7,201,468,217 bytes (7.201 GB) of images, not "6.9 GB" (GiB from du); art_crop/front is 3.015 GB, not 3.0 GiB.
- "about 2800 orphan images per class" was wrong: those are the 2824 back faces referenced by cards.image_uri_back; the true front orphans are 3 (38,630 stems for 38,627 cards).
- "grouped vs shuffled differ by 1.8 points" in the inter matrix is 1.8 MB; in percentage points against intra it is 1.5.
- the same still build was quoted at 3.02x (media) and 2.93x (nest) in two sections; both are now shown with their base.

seed provenance correction:

- the 2048-card sample is evenly spaced, `rows[int(i * 38627 / 2048)]` over rows sorted by (img_id, oracle_id), and seed independent; the old report said "seed 42". verified 2048 of 2048 keys against the control manifest. the only seeded draws are the 96 quality frames and the 100 utility queries, both `default_rng(7)`.

avif manifest error:

- the avif backend of the nest forge sums its letterboxed png intermediates as source_bytes. the avif candidate manifest therefore says source 21,450,566,470 and ratio 18.61; the sample avif rows say 1,138,810,355. every ratio in the rendered tables uses the jpeg source (3,975,063,106 on the full corpus, 211,018,809 on the sample). the backend fix is a pending pull request in nest and the manifest is regenerated once it lands.

### known

- the two release files carry `chunker_version spellbook/1` inside while the sidecars say mtgdataset/1 (renamed after the build); content_hash c993ceda for the releases, cb8fdf8f for the candidates. see the roadmap.
- experiments 03, 09 and 10 and the utility table of 13 are transcribed: their artifacts were not kept.
