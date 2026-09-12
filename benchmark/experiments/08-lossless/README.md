# 08 lossless

2026-08-31. the answer to "the compression cannot lose anything, even if we have to invent it".

hypothesis: some lossless path compresses jpeg sources beyond the jpeg xl transcode, and in particular a lossless video codec over semantically ordered frames exploits the redundancy between cards that no per-image method sees.
method: lossless_battery.py over the same 2048 jpegs (211,018,809 bytes): cjxl --lossless_jpeg=1 at effort 9 with djxl sha256 round-trip on 64 items, jpegtran -optimize and -progressive and jpegoptim --strip-all with pixel checks on 32 items, cwebp -lossless, zstd-19 over the jxl-transcode output, ffv1 in source order and in the av1-cluster-crf35 order_permutation, and x264 qp0 yuv444 in cluster order; the effort 7 row is the forge default from experiment 02.
verdict: refuted. the ceiling for jpeg sources is the byte-reversible transcode, 1.115x at effort 7 and 1.124x at effort 9 (0.8% more for 6.6x the time); pixel-exact re-saves yield under 1% because scryfall's jpegs are already optimized; every pixel-domain path loses, and the ordered lossless video loses by 3.3 to 3.8x against the source, with semantic ordering moving ffv1 by 137 kB, since decoded jpeg pixels do not recompress below the jpeg they came from.

the three classes in the table must never be conflated: byte-reversible returns the original bytes, pixel-exact returns the same pixels from different bytes, pixel-domain recompresses decoded pixels. this experiment became the archive profile. the published challenger to the 1.12x ceiling, wu et al. 2016 (more than 31% lossless on jpeg collections via dct-domain pseudo-video), has no open implementation; the ceiling in this table is the one reachable with available tools. see `docs/references.md`.

provenance: measured; `battery.json` is the surviving record. the encoded generations (jxl-e9/, jpegtran-*/, webp-lossless/, video-*.mkv, jxl-plus-zstd.tar.zst) were deleted after measurement. the old report credited effort 7 with 1.124x; that ratio belongs to effort 9.
