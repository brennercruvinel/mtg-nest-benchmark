# 06 raw data

2026-09-12. what the spellbook cache holds, counted rather than estimated.

hypothesis: the raw cache is larger than the benchmark source because it holds derived classes and back faces, not because of orphans or duplicates, and the benchmark corpus is exactly the 38,627 cards with an image_uri.
method: os.walk over ${MTG_DATA}/images summing st_size with dotfiles excluded, and read-only queries on ${MTG_DATA}/mtg.sqlite; stems on disk joined against cards.image_uri and cards.image_uri_back.
verdict: confirmed. 82,905 jpegs, 7.201 GB; normal/front holds 38,630 files for 38,627 cards, so 3 true orphans, and the 2,824 files per back class are the back faces referenced by image_uri_back, not orphans; art_crop/front (3.015 GB) is a second class, not derivable from normal without crop coordinates the app does not store; the old report's "6.9 GB" and "3.0 GB" were binary units from du and its "about 2800 orphans per class" was the back faces.

the 38 md5 duplicate groups of the old report were not re-verified; no hash list survives. the jsonl.gz bulk files that duplicated the sqlite no longer exist.

provenance: measured 2026-09-12. bytes are the sum of file sizes; du reports allocated blocks (7,199,764 KiB for images/), which is why the two earlier figures disagree with each other and with this table.
