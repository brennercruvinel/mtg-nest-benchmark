# 01 baselines

2026-08-31. the ruler every later ratio is read against.

hypothesis: a generic archiver over the 2048 source jpegs yields something, and whatever it yields is the floor a codec has to beat.
method: tar and tar --zstd with ZSTD_CLEVEL=19 over the same 2048 files the variants encode (211,018,809 bytes), sizes read from the archives; recorded by measure_variants.py under the _baselines key of measurements.json.
verdict: refuted, 1.00x. tar adds 2.7% of headers, zstd-19 takes it back and nothing more; jpeg is already entropy coded, so every gain in the other experiments comes from an image or video codec, never from the container.

provenance: measured on 2026-08-31; the numbers were read from `02-av1-variants/measurements.json`.
