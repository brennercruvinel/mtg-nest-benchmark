# roadmap

the open items after v0.3, each with what is missing and why it matters. the order is roughly the order I would do them in. every item ends with an issue line that the publish step fills.

## a hit@k floor for the retrieval-only gate

the `crf=auto` gate has a drift floor (cosine p10 0.98) and two visual floors. experiment 13 showed that drift measures signal stability and not search utility: crf50 has drift 0.942 and the same txt@1 as crf35. a retrieval-only profile therefore needs a utility floor, hit@k on a fixed query set, either inside the gate or in the sweep that picks the crf. crf55 and crf60 were never measured on utility, only on drift, and n=100 does not prove equality. this needs the bench output saved as an artifact, n well above 100, and a stronger ruler than clip on "artwork of the card {name}".

issue: (to be linked)

## wemm and jina over crf50 media

the utility table of experiment 13 is clip only. the models that read the printed card name (wemm-2b@256, jina-v5-omni-nano@256) had drift 0.990 and 0.989 at crf35 on the 1500 sample, but text rendering degrades faster than art under heavy quantization (the gate's text buckets at crf50 sit at ssim2 p10 16 to 34), so their utility at crf50 is an open question and the answer decides whether the retrieval profile is usable with a text-reading model.

issue: (to be linked)

## avif q48 as the stills backend

quality matched, avif from libaom is 12.4% smaller than the svt-av1 all-intra stream on the sample and 13.0% smaller on the full `.nest`, with o(1) access per image and no video decode. the cost is on the build side: the clip embed over per-image avif ran 4 to 10x slower than over the mp4 (12.5 to 37 items/s against about 140). switching the stills profile means accepting that or fixing the decode path first.

issue: (to be linked)

## recalibrate the dual-gate floors, or extend the ladder below 30

the default floors (ssim2 p10 85, min 72, drift 0.98) are unreachable for 488x680 yuv420 card scans at any crf of the ladder; the recorded ladder shows the drift floor failing already at crf30. the gate therefore always falls back to the smallest crf with a warning, which makes `crf=auto` a no-op on this corpus class. either the floors get calibrated per corpus class or the ladder extends below 30 so the gate can pass somewhere.

issue: (to be linked)

## rebuild the v0.3 releases under the mtgdataset name

the two release files carry `chunker_version = spellbook/1`, the title "Spellbook MTG corpus" and `media://spellbook-*` uris inside, while the sidecars beside them say mtgdataset/1 because they were renamed after the build. this is why the releases have content_hash c993ceda and the candidates cb8fdf8f, and it means the release build lock no longer reproduces the file it describes. the fix is a rebuild from `profiles/neardup.toml` and `profiles/archive.toml` (about 30 and 20 minutes), which will produce the cb8fdf8f identity; the alternative is to document the twins as they are and freeze them.

issue: (to be linked)

## the avif source_bytes fix and the candidate manifest

the avif backend of the nest forge sums its letterboxed png intermediates as source_bytes, so the avif candidate manifest records 21,450,566,470 bytes of source and a ratio of 18.61 for a 3,975,063,106-byte jpeg corpus. a pull request in nest passes the real source size into encode_avif; once it lands the candidate manifest must be regenerated (or patched) so that anything reading `media.compression_ratio` stops seeing a 5.4x inflation.

issue: (to be linked)

## the five-model full build and the model pins

the 38,627-card build with all five models (potion, clip, siglip2, jina, wemm-2b) was never run; wemm-2b alone was estimated at 18 to 20 hours on the benchmark machine. wemm-4b and wemm-9b are registered in the model registry and were never executed. the remote-code allowlist still needs pinned revisions, and jina's `image_max_side` default needs a decision, since it was set by hand during the 1500 build to keep the embed at 0.5 s per image instead of 23 s.

issue: (to be linked)

## research notes

five things worth a spike, none started. a template frame per cluster, the av1 golden-frame mechanism, so a group of reprints predicts from one shared reference instead of a chain. binary hnsw traversal with int8 rescoring, a 32x reduction of the index band. a dedup cascade from phash to a cnn embedding (imagededup, fastdup), since byte dedup found 38 groups and near-duplicate detection is what corpus B needs. crf search by a metric target in the style of ab-av1, with hit@k as the target once the floor above exists. av2, whose 1.0 specification came out in may 2026 with about 30% over av1 and no practical encoder yet; the versioned codec field in the container covers the migration. and cool-chic as a neural codec spike, the one with a c decoder on cpu.

issue: (to be linked)

## hygiene

three candidates sit in `candidates/` and should be promoted or discarded. making `tune=still` the schema default invalidates every embed cache keyed on the media recipe, so it needs a deliberate cut. the full-corpus manifest is 13 MB of `items[]` and provenance `minimal` would drop most of it; the release sidecars already strip `items[]` into `items.jsonl.gz`, the candidates do not.

issue: (to be linked)
