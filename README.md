# mtg-nest-benchmark

compression and retrieval benchmark of the 38627-card magic: the gathering image corpus packed into
single-file [nest](https://github.com/hoffresearch/nest) archives: av1, avif and jpeg xl media
variants, lossless batteries, inter-frame ordering, and retrieval-only profiles measured against a
3.975 GB jpeg source. the product recipes live in `profiles/`, every experiment under
`benchmark/experiments/NN-slug/` with its `results.json`, and `RESULTS.md` is generated from those
files by `benchmark/tools/render_report.py`. the `.nest` artifacts are not in git. this readme is a
placeholder; the full one is being written.
