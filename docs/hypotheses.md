# hypotheses and verdicts

every hypothesis the benchmark tested between 2026-08-31 and 2026-09-05, where it came from, how it was tested, and what the data said. the experiment id points at the directory under `benchmark/experiments/` whose `results.json` carries the numbers; "transcribed" means the artifacts are gone and the verdict rests on the 2026-09-03 report.

| # | hypothesis | origin | how tested | verdict | experiment |
| ---: | --- | --- | --- | --- | --- |
| 1 | av1 video compresses better than loose jpeg | premise of the v0.2 build | full build of 38,627 cards | confirmed, with loss: 3.34x on the normal class, 4.45x on art_crop | 05 (legacy row, transcribed) |
| 2 | the stream duplicates frames, each card sits about 1 s on screen | user | ffprobe count_frames on the v0.2 stream | refuted: one frame per card, fps=1 is only a timestamp | 02 (the fps variants) |
| 3 | speeding the video up or lowering fps halves the bytes (the capcut observation) | user | fps30 intra vs still-s6; programmatic reproduction of the capcut export | refuted: fps alone is byte-identical; capcut's -57% comes from dropping 993 of 2048 cards and re-encoding h.264 | 02, 10 |
| 4 | more visual similarity, more compression through inter prediction | user | corpus B, 2787 same-artwork reprints via illustration_id, gop 8/16/32, grouped vs shuffled | confirmed: -29% with inter gop 16 grouped vs intra, bytes at fixed crf | 09 (transcribed) |
| 5 | inter prediction also helps on unique cards | derived from 4 | 2048 sample, scd=0, semantic order, ssimulacra2 on both arms | refuted: ties tune=still on bytes but ssim2 p50 falls from 62.7 to 46.8; the probe now vetoes it | 09, 02 (selfcontained-neardup pre-fix), 05 (19 segments, all vetoed) |
| 6 | tune iq and inter prediction stack | assistant | tune=3 with gop 9999 | refuted: svt-av1 accepts iq only in all-intra or low-delay, and low-delay costs +21% | 09 |
| 7 | a lossless path better than jpeg exists, "even if we have to invent it" | user | ten-generation battery: jxl e7/e9, jxl plus zstd, jpegtran, jpegoptim, webp, ffv1 in two orders, x264 qp0 | refuted: the ceiling is jxl-transcode at 1.12x; ordered lossless video loses 3.3 to 3.8x | 08 |
| 8 | tar plus zstd compresses jpeg | ruler | tar --zstd at level 19 over the 2048 files | refuted: 1.00x | 01 |
| 9 | art_crop is derivable from normal, saving 3 GB of raw cache | assistant | an agent read the app code and schemas | refuted: no crop coordinates are stored, and the app uses art_crop in its deck tiles | 06 (no experiment, transcribed) |
| 10 | equal bytes at equal crf mean equal quality | implicit in the first gop probe | ssimulacra2 on both arms plus mad alignment against the source | refuted: svt quantizes p-frames coarser; the probe became quality-aware with a 2-point tolerance | 05 (per-segment records), 02 |
| 11 | clip cosine drift is a good proxy of search utility | premise of the dual gate | retrieval crf 40 to 60, hit@k on 100 queries | refuted: drift falls fast (0.932 at crf40, 0.829 at crf60) while txt@1 stays flat up to crf50 | 13 |
| 12 | avif from libaom beats svt-av1 all-intra | i-frame battery | 19 encoders calibrated to ssimulacra2 mean 61.96 | confirmed: -12.4% on the sample, -13.0% on the full .nest | 11, 13 |
| 13 | models that read the printed text win text-to-image search | model bench | t3 with "artwork of the card {name}", 60 queries on the 1500 sample | confirmed: wemm-2b@256 hits 0.933 at rank 1 against clip's 0.233 | 03 (transcribed) |

two notes on reading the table. hypothesis 4 is confirmed on bytes and the quality cost of that confirmation is what refutes hypothesis 5 on unique cards; the two are the same lever seen from two corpora. hypothesis 11 is the one that changed the product contract: the drift floor stays as a stability gate, and a retrieval-only profile needs a utility floor that does not exist yet (see `docs/roadmap.md`).
