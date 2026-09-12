# 11 intra codecs

2026-08-31. nineteen all-intra encodes of the same 2048 cards, calibrated to the same fidelity, then compared on bytes and wall time.

hypothesis: at matched quality the av1 stream of the forge is neither the most compact nor the fastest all-intra option, and the gap to the best of each axis is worth knowing before choosing the stills backend.
method: every encoder consumes the same decoded pixels (pil decode plus letterbox to 488x680, the forge pipeline); quality is ssimulacra2 on the fixed 96-frame sample against the source png; each encoder's quality knob is calibrated until the mean lands at 61.96 with a tolerance of 2, the value of the svt-av1 preset 6 crf 35 tune still baseline, which was reproduced byte-identically first (70,092,669 bytes); wall clock on a 10-core apple silicon machine with the svt ladder pinned to lp=2 like the forge and per-image codecs on 10 single-threaded workers.
verdict: confirmed on both axes. most compact at matched quality is avif from libaom at speed 6 q48, 61.4 MB, -12.4% against the svt baseline, so libaom still out-compresses svt-av1 all-intra; fastest inside the window is x264 at crf 31, 4.8 s; the best balance is svt preset 6 with lp=8, 17 s for the same bytes and quality as the baseline; vvenc intra costs 100x the x264 time for a mid-table size; cjxl lossy competes only at high fidelity (distance 1 to 2, ssim2 76 to 90), outside this profile's window; svt presets 10 and 12 emit byte-identical streams.

the product fix that fell out of the battery: probe_tune_still probed without keyint=1, svt rejected the still-picture tune and the forge fell back in silence to tune 4 (ms-ssim). tune 3 measures +1.26 ssim2 for +1.4% bytes; manifests now record tune_resolved. the jxl distance 1 and 2 rows are fixed-distance and sit far above the target, so their sizes are not comparable to the calibrated rows.

provenance: measured; `battery.json` holds the 19 experiments plus _meta (tool versions: ffmpeg 9 with libsvtav1 4.2.0, avifenc 1.4.2 with aom 3.14.1, cjxl 0.12.0, cwebp 1.6.0, vvencapp 1.14.0) and `samples/` one encoded sample per experiment. the battery script itself was not kept.
