# roadmap

the open items after v0.3, each with what is missing and why it matters. the order is roughly the order I would do them in. every item ends with an issue line that the publish step fills.

## a hit@k floor for the retrieval-only gate

the `crf=auto` gate has a drift floor (cosine p10 0.98) and two visual floors. experiment 13 showed that drift measures signal stability and not search utility: crf50 has drift 0.942 and the same txt@1 as crf35. a retrieval-only profile therefore needs a utility floor, hit@k on a fixed query set, either inside the gate or in the sweep that picks the crf. crf55 and crf60 were never measured on utility, only on drift, and n=100 does not prove equality. this needs the bench output saved as an artifact, n well above 100, and a stronger ruler than clip on "artwork of the card {name}".

issue: https://github.com/hoffresearch/mtg-nest-benchmark/issues/1

## wemm and jina over crf50 media

the utility table of experiment 13 is clip only. the models that read the printed card name (wemm-2b@256, jina-v5-omni-nano@256) had drift 0.990 and 0.989 at crf35 on the 1500 sample, but text rendering degrades faster than art under heavy quantization (the gate's text buckets at crf50 sit at ssim2 p10 16 to 34), so their utility at crf50 is an open question and the answer decides whether the retrieval profile is usable with a text-reading model.

issue: https://github.com/hoffresearch/mtg-nest-benchmark/issues/2

## avif q48 as the stills backend

quality matched, avif from libaom is 12.4% smaller than the svt-av1 all-intra stream on the sample and 13.0% smaller on the full `.nest`, with o(1) access per image and no video decode. the cost is on the build side: the clip embed over per-image avif ran 4 to 10x slower than over the mp4 (12.5 to 37 items/s against about 140). switching the stills profile means accepting that or fixing the decode path first.

issue: https://github.com/hoffresearch/mtg-nest-benchmark/issues/3

## recalibrate the dual-gate floors, or extend the ladder below 30

the default floors (ssim2 p10 85, min 72, drift 0.98) are unreachable for 488x680 yuv420 card scans at any crf of the ladder; the recorded ladder shows the drift floor failing already at crf30. the gate therefore always falls back to the smallest crf with a warning, which makes `crf=auto` a no-op on this corpus class. either the floors get calibrated per corpus class or the ladder extends below 30 so the gate can pass somewhere.

issue: https://github.com/hoffresearch/mtg-nest-benchmark/issues/4

## rebuild the v0.3 releases under the mtgdataset name

done on 2026-09-12. the two release files carried `chunker_version = spellbook/1`, the title "Spellbook MTG corpus" and `media://spellbook-*` uris inside, while the sidecars beside them said mtgdataset/1 because they were renamed after the build; that is why the releases had content_hash c993ceda against cb8fdf8f for the candidates, and why the release build lock did not reproduce the file it described. both were rebuilt from `profiles/archive.toml` and `profiles/neardup.toml` with the forge at main: archive 3,606,342,844 bytes, file_hash `sha256:882427094aa6035aa1ddf6abd26444f1598345fb9be3a66612f50b99be377eeb`; neardup 1,374,447,548 bytes, file_hash `sha256:071233c549f45644a3ce9a3bc581e0fe564ed30f70a01b30f726efb3b5c50132`; both content_hash `sha256:cb8fdf8f13fa50f93969de7603386f1c2b117a5e4946c60ac9894a3c5a1f062b` and chunker mtgdataset/1, media bytes identical to the old builds. the c993ceda twins were replaced on disk and on hugging face.

issue: https://github.com/hoffresearch/mtg-nest-benchmark/issues/5

## the avif source_bytes fix and the candidate manifest

done on 2026-09-12. the avif backend of the nest forge summed its letterboxed png intermediates as source_bytes, so the avif candidate manifest recorded 21,450,566,470 bytes of source and a ratio of 18.61 for a 3,975,063,106-byte jpeg corpus. nest pull request #132 passes the real source size into encode_avif and records the png sum as `letterboxed_input_bytes`; the candidate manifest on disk and on hugging face was patched by hand the same day (source_bytes 3,975,063,106, ratio 3.45, a `patched` note in the media block). what remains is cosmetic: a rebuild of the avif candidate with the fixed forge would make its lock reproduce the manifest without the hand patch.

issue: https://github.com/hoffresearch/mtg-nest-benchmark/issues/6

## the five-model full build and the model pins

the 38,627-card build with all five models (potion, clip, siglip2, jina, wemm-2b) was never run; wemm-2b alone was estimated at 18 to 20 hours on the benchmark machine. wemm-4b and wemm-9b are registered in the model registry and were never executed. the remote-code allowlist still needs pinned revisions, and jina's `image_max_side` default needs a decision, since it was set by hand during the 1500 build to keep the embed at 0.5 s per image instead of 23 s.

issue: https://github.com/hoffresearch/mtg-nest-benchmark/issues/7

## research notes

five things worth a spike, none started. a template frame per cluster, the av1 golden-frame mechanism, so a group of reprints predicts from one shared reference instead of a chain. binary hnsw traversal with int8 rescoring, a 32x reduction of the index band. a dedup cascade from phash to a cnn embedding (imagededup, fastdup), since byte dedup found 38 groups and near-duplicate detection is what corpus B needs. crf search by a metric target in the style of ab-av1, with hit@k as the target once the floor above exists. av2, whose 1.0 specification came out in may 2026 with about 30% over av1 and no practical encoder yet; the versioned codec field in the container covers the migration. and cool-chic as a neural codec spike, the one with a c decoder on cpu.

issue: https://github.com/hoffresearch/mtg-nest-benchmark/issues/8

## hygiene

three candidates sit in `candidates/` and should be promoted or discarded. making `tune=still` the schema default invalidates every embed cache keyed on the media recipe, so it needs a deliberate cut. the full-corpus manifest is 13 MB of `items[]` and provenance `minimal` would drop most of it; the release sidecars already strip `items[]` into `items.jsonl.gz`, the candidates do not.

issue: https://github.com/hoffresearch/mtg-nest-benchmark/issues/9
