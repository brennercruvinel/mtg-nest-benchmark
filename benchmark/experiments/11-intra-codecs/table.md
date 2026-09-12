# i-frame battery: 2048 MTG cards (488x680)

Source: 211.0 MB of JPEG. Baseline: svt-av1 all-intra preset 6 crf 35 tune=still
(= av1-still-s6-crf35 in measurements.json, reproduced byte-identically).
Quality: SSIMULACRA2 on the fixed 96-item sample (seed 7), decoded frame vs
PIL-decoded source. Calibrated rows target ssim2 mean 61.96 +-2; cjxl d1/d2
rows are fixed-distance per spec and sit far ABOVE that quality — their sizes
are not comparable to the calibrated rows. Wall-clock encode seconds, threads
as noted per row (svt ladder pinned to lp=2 like the forge production path).

| experiment | codec | params | MB | ratio | encode_s | threads | ssim2 mean | p50 | p10 | min |
|---|---|---|---|---|---|---|---|---|---|---|
| avif-s6-q48 | avifenc (aom) | -q 48 --speed 6 --yuv 420 -j 1 | 61.4 | 3.44x | 50.8 | 10 workers x 1 thread | 60.72 | 61.79 | 53.22 | 40.85 |
| svt-p4-crf35 | svt-av1 all-intra | crf=35 preset=4 tune=4(MS_SSIM(forge 'still')) lp=2 keyint=1 yuv420p | 69.0 | 3.06x | 167.3 | lp=2 | 62.54 | 63.3 | 56.12 | 47.48 |
| svt-p6-crf35 | svt-av1 all-intra | crf=35 preset=6 tune=4(MS_SSIM(forge 'still')) lp=2 keyint=1 yuv420p | 70.1 | 3.01x | 74.1 | lp=2 | 61.96 | 62.69 | 55.68 | 45.3 |
| svt-p6-crf35-lp8 | svt-av1 all-intra | crf=35 preset=6 tune=4 lp=8 keyint=1 yuv420p | 70.1 | 3.01x | 17.0 | lp=8 | 61.96 | 62.69 | 55.68 | 45.3 |
| svt-p6-crf35-tune3 | svt-av1 all-intra | crf=35 preset=6 tune=3(still/IQ) lp=2 keyint=1 yuv420p | 71.0 | 2.97x | 71.6 | lp=2 | 63.22 | 64.05 | 56.9 | 46.31 |
| svt-p8-crf35 | svt-av1 all-intra | crf=35 preset=8 tune=4(MS_SSIM(forge 'still')) lp=2 keyint=1 yuv420p | 72.5 | 2.91x | 12.6 | lp=2 | 60.12 | 60.9 | 53.54 | 42.02 |
| jxl-d4.0-e7 | cjxl lossy (VarDCT) | -d 4.0 -e 7 --lossless_jpeg=0 | 73.0 | 2.89x | 71.1 | 10 workers x 1 thread | 60.91 | 61.25 | 52.88 | 41.76 |
| svt-p10-crf35 | svt-av1 all-intra | crf=35 preset=10 tune=4(MS_SSIM(forge 'still')) lp=2 keyint=1 yuv420p | 74.7 | 2.83x | 7.0 | lp=2 | 59.03 | 59.94 | 52.7 | 41.69 |
| svt-p12-crf35 | svt-av1 all-intra | crf=35 preset=12 tune=4(MS_SSIM(forge 'still')) lp=2 keyint=1 yuv420p | 74.7 | 2.83x | 7.6 | lp=2 | 59.03 | 59.94 | 52.7 | 41.69 |
| svt-p10-crf35-lp8 | svt-av1 all-intra | crf=35 preset=10 tune=4 lp=8 keyint=1 yuv420p | 74.7 | 2.83x | 3.3 | lp=8 | 59.03 | 59.94 | 52.7 | 41.69 |
| x264-crf31 | libx264 all-intra | crf=31 preset=medium keyint=1 yuv420p | 76.0 | 2.78x | 4.8 | default (10 logical) | 60.77 | 61.05 | 55.63 | 48.44 |
| vvenc-fast-qp22 | vvenc (VVC intra) | qp=22 preset=fast ip=1 idr 10bit-internal yuv420 | 76.2 | 2.77x | 463.4 | 8 | 62.71 | 63.12 | 55.95 | 47.04 |
| avif-s9-q52 | avifenc (aom) | -q 52 --speed 9 --yuv 420 -j 1 | 79.7 | 2.65x | 7.2 | 10 workers x 1 thread | 62.54 | 63.68 | 55.79 | 44.71 |
| x265-crf32 | libx265 all-intra | crf=32 preset=medium keyint=1 yuv420p | 80.9 | 2.61x | 61.9 | default (10 logical) | 61.21 | 61.55 | 56.35 | 50.6 |
| webp-q45 | cwebp | -q 45 (yuv420) | 85.1 | 2.48x | 9.5 | 10 workers x 1 thread | 62.2 | 62.29 | 57.02 | 50.37 |
| jxl-d2.0-e7 | cjxl lossy (VarDCT) | -d 2.0 -e 7 --lossless_jpeg=0 | 123.6 | 1.71x | 62.0 | 10 workers x 1 thread | 75.92 | 76.36 | 70.75 | 63.1 |
| jxl-d2.0-e4 | cjxl lossy (VarDCT) | -d 2.0 -e 4 --lossless_jpeg=0 | 142.1 | 1.49x | 10.2 | 10 workers x 1 thread | 81.2 | 81.64 | 78.54 | 74.29 |
| jxl-d1.0-e7 | cjxl lossy (VarDCT) | -d 1.0 -e 7 --lossless_jpeg=0 | 184.0 | 1.15x | 63.4 | 10 workers x 1 thread | 86.61 | 86.92 | 84.28 | 81.38 |
| jxl-d1.0-e4 | cjxl lossy (VarDCT) | -d 1.0 -e 4 --lossless_jpeg=0 | 194.9 | 1.08x | 11.6 | 10 workers x 1 thread | 89.62 | 89.83 | 88.65 | 85.92 |

Notes
- svt presets 10 and 12 emit byte-identical streams: SVT-AV1 4.2 maps both to M9
  for all-intra ("Preset M10/M12 is mapped to M9" in the encoder log).
- verdicts: most compact at equivalent quality = avif-s6-q48 (61.4 MB, -12.4% vs
  the svt-p6 baseline); fastest within the +-2 quality window = x264-crf31
  (4.8 s wall). svt-p10-lp8 is faster (3.3 s) but sits 2.9 points below target.
- svt tune=3 is SVT-AV1 4.2's real still-picture tune (Tune IQ, all-intra only);
  the forge probe resolves tune=still to 4 (MS_SSIM) because it probes without
  keyint=1.
- vvenc uses 10-bit internal coding (VVC default); decoded with ffmpeg 9's
  native vvc decoder.
- jpeg-xl operates in XYB (no 4:2:0 chroma subsampling); every other lossy row
  here is 4:2:0.
