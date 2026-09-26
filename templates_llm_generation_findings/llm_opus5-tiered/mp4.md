# MP4 — tiered generative template findings

| | |
|---|---|
| **Output** | `templates_llm/llm_opus5-tiered/mp4-llm.bt` — **1185 lines** from an 807-line original, **1.4684×** |
| **Inputs** | `templates_originals/mp4-orig.bt` + `llm_reterived_constraints_mp4-llm_opus5-tiered.json` |
| **JSON** | 126 constraints (A 18 / B 25 / C 83), 25 dependencies, 16 structure rules, 18 diversity axes |
| **Target** | FFmpeg 6.1, `ffmpeg -i FILE -c:v mpeg4 -c:a copy out.mp4` |

## Verification

| step | result |
|---|---|
| 1 `ffcompile` | exit 0 |
| 2 `build_new.sh` | exit 0 |
| 3 generate 200 | **0 generation errors**; **198/200 distinct sizes**, largest bucket 2 files, min 912, p25 2380, median 3510, p75 7246, p95 16657, max 19683 |
| 4 round-trip `parse` | **200/200**; an independent box-tree validator finds **0 structural defects across 200 files** |
| 5 gate | **no regression** — the first corpus that generated cleanly already measured 6.2% on 200 files |

**Coverage: 4.1% (21527/521084) → 6.9% (36213/521084), +2.8 points / +14686 lines
/ +744 functions.** 536 source files touched against the baseline's 422.

Decoder outcome on 200 files: 200 demuxed, 167 transcoded with exit 0, **101
decoded real frames** (31,507 frames), average 0.11 s/file, no timeouts.

---

## The one thing that decides this format

Measurement came before any template code. A **single** hand-built MP4 with one
uncompressed-video track = **22,562 lines** — already above the entire 2000-file
baseline. Adding an AAC track took one file to 25,375. `-c:v mpeg4` is a full
transcode, so a file whose frames actually decode drags in `mpegvideo_enc`,
`mpeg4videoenc`, `motion_est`, `ratecontrol`, all of swscale and the filter
graph. A file that merely demuxes gets ~12k; a garbage file gets 4.5k.

So the design goal became: *most generated files must contain a video track
FFmpeg can really decode*, without pinning a single dimension. The answer is the
**uncompressed sample entries** — `raw `, `2vuy`, `b16g`, `BGRA` — where the
payload is exactly what the free geometry implies. That is the payload rule
working in the template's favour rather than against it.

```
+1156  libavcodec/mpegvideo_enc.c      0 -> 1156     +390  libswscale/swscale.c        0 -> 390
 +702  libavcodec/h264_slice.c       122 -> 824      +379  libavcodec/mpegvideo.c      0 -> 379
 +634  libswscale/utils.c              0 -> 634      +367  libavcodec/motion_est.c     0 -> 367
 +590  fftools/ffmpeg_filter.c       293 -> 883      +335  libavfilter/vf_scale.c      0 -> 335
 +521  libavcodec/error_resilience.c   0 -> 521      +265  libavcodec/ratecontrol.c    0 -> 265
 +474  libavcodec/mpeg4videoenc.c      0 -> 474      +261  libavformat/mov.c        2254 -> 2515
```

---

## Structural rewrite

MP4 is a length-prefixed tree: `boxheader.size` (Tier A) must be known *before*
the header it measures, and every container's child walk is bounded by it.
**Nothing is backpatched.** Instead the whole file is planned once and every box
size is arithmetic:

- The plan is 80 free byte draws plus four free `uint32` draws, taken by
  lookahead from the body of a `free`/`skip` box at the head of the file
  (structure[7]). Those bytes stay in the file as that box's content, so the
  entropy costs nothing and the draws keep the engine's own distribution.
- `PlantBox(type, body)` plants `size` with `ReadUInt` and `type` with
  `ReadBytes` at the header's own position; the bare declarations in `boxheader`
  then pick them up via the bitmap, in both directions.
- `MoovSize()` → `TrakSize()` → `MdiaSize()` → `MinfSize()` → `StblSize()` →
  `EntrySize()`/`CfgSize()` compute the subtree exactly, so `G_mdatBody` is known
  before `moov` is written and chunk offsets need no second pass. This is what
  lets **both** layout orders (structure[5]) work: 317 mdat-first / 283 moov-first
  over 600 files.
- Each container's `while (FTell() < endOffset)` loop calls
  `PlanChild(containerType, index)` before each child. A forward-progress guard
  and a trailing `FSkip(endOffset - FTell())` at the end of `mp4box` make a box
  exactly as long as its header says, so an arithmetic slip can never
  desynchronise the file.

---

## Expressed

### Structure — all 16

[0] ftyp first · [1] moov with mvhd + 1–4 trak · [2] the full
trak▸mdia▸minf▸stbl chain · [3] stsd sized from its entries · [4] mdat ·
[5] both orders · [6] top-level sequence under `B_FILE` · [7] free/skip/invented
codes under `B_FREE` · [8] moof▸mfhd/traf▸tfhd/trun under `B_MOOF` ·
[9] stco XOR co64 · [10] mvhd first · [11] multi-track · [12] dinf▸dref▸`url `
(the `dref`/`url ` arms were added; the original skipped dref, which meant a
garbage body) · [13] conventional stbl order with an occasional legal stsz/stco
swap · [14] sizes 2–7 never emitted (minimum body 0 → size 8) · [15] no trailer.

### Dependencies — all 25 appear

Notable: [0]/[3] the 64-bit header and every version-1 width (100 extended
headers per 600 files; version bytes 0 and 1 both appear on every full box —
10,674 zeros / 6,489 ones); [4] pssh KID list; [6] `default_per_sample_IV_size`
0 bringing the constant IV into existence (all three of {0, 8, 16} observed);
[7] senc subsample table; [8] stsz constant vs table (1359 table / 167 constant);
[10]–[13] handler type selecting vmhd/smhd/nmhd and the visual vs audio entry
shape; [17] mvex forced whenever a moof follows; [21] `first_chunk` 1 then
strictly increasing.

**dependencies[15] was the single biggest find.**
`str_stsc.sample_description_index` is Tier C, but the dependency says it "should
be between 1 and the stsd entry_count". Left free, **every generated file decoded
zero frames**: `mov.c:4363` adds a sample to the index only when
`stsc.id - 1 == sc->pseudo_stream_id`; a non-resolving index silently drops every
sample of the track. Implementing the dependency (mostly resolving, ~7%
deliberately dangling — the JSON asks for both) took the corpus from **0 → 47 of
120** files decoding. The JSON's claim that out-of-range values "are accepted and
reach a reader's fallback" does not hold for FFmpeg 6.1.

### `payload_wellformedness`

**1. `mp4box.entries` — the sample entries.** Framing per `must_produce`: six
zero reserved bytes, `data_reference_index` = 1, `frame_count` = 1, and the
configuration box nested inside the entry's declared size. Free and varying: the
declared geometry, the 32-byte compressorname, depth, and the
profile/compatibility/level bytes.

| entry | size | configuration box |
|---|---|---|
| visual (`raw `/`2vuy`/`b16g`/`BGRA`/`jpeg`) | 86 | none |
| `avc1` | 86 + 46 | `avcC` = 8 + 11 + 22 SPS + 5 PPS |
| `mp4v` | 86 + 64 | `esds` = 8 + 4 + 52 (MPEG-4 Visual VOS/VOL) |
| `hvc1` | 86 + 31 | `hvcC` = 8 + 23 |
| `encv` | 86 + 80 + 9·aux | `sinf` ▸ frma, schm, schi ▸ tenc |
| audio (`sowt`/`twos`) | 36 | none |
| `mp4a` | 36 + 39 | `esds` = 8 + 4 + 27 (AAC LC) |
| generic (`tx3g`/`tmcd`/`mp4s`) | 24 | none |

`derives_from` is honoured literally: the entry's `uint16` width/height are the
track's free geometry draws, and `T_cfg` leaves the parameter sets themselves
free on a quarter of tracks so the "SPS and PPS payloads should vary" note is not
lost while the other three quarters keep the verified pair and a real stream.

**2. `meta.unnamed_payloads` — the mdat.** An `mdat` arm was added (the original
skipped it). For an `avc1` track `WriteMedia()` plants, per sample, a 4-byte
big-endian length = `SampSize(t,i) − 4` followed by a NAL header byte with the
forbidden-zero bit clear; the remaining bytes are free. For every other codec the
sample *is* the payload:

```
uncompressed:  w · h · bpp          bpp = 3 (rgb24, depth 24), 4 (argb, 32),
                                          2 (rgb555be, 16), 1 (pal8, 8), 4 (bgra), 2 (gray16be)
uyvy422:       ceil(w/2)·2 · h · 2  — a 4:2:2 row is an even number of columns
PCM audio:     channels · 2 · k
avc1/mp4v/…:   base + ((i·37 + seed) mod span)   — deliberately uneven per diversity_axes[4]
```

The bpp table and the uyvy422 rounding are **measured, not assumed**: a 60-cell
grid of (fourcc, depth, w, h) was run through the decoder. `rgba` produces
`pix_fmt none` and was dropped; `2vuy`/`yuv2` fail at odd widths without the
rounding.

Chunk offsets are `G_mdatBody + T_off[t] + Σ SampSize(t, j)` — absolute,
computed after the layout is settled, exactly as dependencies[19] requires.

**3. `str_stsd.content`** is left untouched. The JSON marks it
`declared_but_unreferenced` and says to build entries through `mp4box.entries`
instead — line 667 of the original supersedes the commented-out line 666.

### `diversity_axes` — all 18 confirmed

An automated audit over all 83 Tier C constraint keys found **145 declarations,
100% bare** — zero carry `= { }`, `<min=>`, `<max=>` or `<values=>`.

| # | field | how it stands |
|---|---|---|
| 0/1 | `mp4box.width`, `.height` | `fp32` **bare**, full 32-bit (165 distinct values / 600 files) |
| 2–6 | `entry_count`, `sample_count`, `entry_size`, `chunk_offset`, `entries` | Tier A: planted from the records written; counts free (116 distinct sample counts, max 231; 51 distinct chunk counts, max 156) |
| 7 | `boxheader.type` | Tier B: **55 distinct box types** emitted |
| 8 | `mp4box.subtype` | Tier B: **all 21** handler types |
| 9 | `mp4box.version` | Tier B: `= { 0, 1 }` on all 29 declarations **and** planted |
| 10 | `mp4box.flag` | Tier A bitmask: tfhd/trun bit combinations free, sizes follow the bits |
| 11/12 | `time_scale`, `duration` | **bare** in both mvhd and mdhd |
| 13 | `str_stts.sample_delta` | **bare** |
| 14 | `str_stsc.samples_per_chunk` | **bare declaration**; value from a whole free `uint32` draw (see below) |
| 15 | `elst_entry.media_time` | **bare** |
| 16 | `mp4box.track_id` | **bare**; read back by a value-less lookahead so trex/tfhd can match it (158 distinct) |
| 17 | `mp4box.graphics_mode` | Tier B enum: **all 9** values |

Other Tier B sets added after auditing: `mp4lang.value` (111 distinct values
including the packed-ISO half and `qtlUnspecified`), `codingName`, `scheme_type`
(all 4 cenc schemes), `aux_info_type` (all 4), `default_is_protected`, `systemID`
(all 6 registered DRM UUIDs + the unregistered case). `fourcc.value` stays bare
at the leaf — its three context sets are disjoint
(`meta.context_value_sets`), so the set is applied at each instantiation site as
the `lookahead` constraint form.

---

## Not expressed

- **`output_budget` figures are scaled.** The JSON asks for 1 MiB per file /
  768 KiB media / 256 KiB moov. `MAX_FILE_SIZE` is 65,536 and `MAX_RAND_SIZE`
  131,072, so the budget is `B_FILE` 32,000, `B_MEDIA` 16,000, `B_MOOF` 3,000,
  `B_FREE` 1,200. Spent the sanctioned way — by ending the sample sequence.
- **`str_stsc.samples_per_chunk` is planted, not drawn in place.** The declaration
  is bare and the value is a whole free `uint32` lookahead draw, so it keeps the
  engine's full-width distribution (30 distinct values, max 200). Planting was
  necessary because `chunk_offset` (Tier A) derives from it and the two boxes can
  appear in either order. Clamped to the samples that exist, because a chunk
  declaring more samples than the track has makes `mov.c` abort the index with
  "wrong sample count"; zero stays legal and reaches the index-loop guard.
- **`boxheader.size == 0`** (dependencies[1], structure[15]) is not emitted. The
  JSON's own `template_parse_requirement` says the original's `BoxSize` helper
  returns 0 for it, collapsing `endOffset` onto `startOffset`, and that "a
  generator targeting this template should write real sizes".
- **`version` stays 0 in mvhd, tkhd and mdhd.** The original implements only the
  v0 layout for those three — there is no version branch to write a v1 body into.
  Both values are emitted on the other 24 arms the JSON lists.
- **dependencies[22]**: the template hard-codes senc's per-sample IV at 8 bytes,
  so a `tenc` declaring 16 disagrees with it. That is the template limitation the
  JSON records, not a format rule; all three widths are emitted and the mismatch
  is left visible.
- **Where the baseline still leads:** AAC decoding — `aacdec_template.c` −147,
  `aacsbr_template.c` −138. The `mp4a` samples are free bytes, so the decoder's
  deep SBR paths are not reached. Everything else is ahead.

Two formatting changes to the original were forced by the 1.5× limit and are
purely mechanical: the 114-line `qtlang` enum is reflowed four enumerators per
line, and `BoxComment`'s cases two per line. Every identifier, value and comment
is preserved. The added code is compressed K&R-style; after each pass ffcompile's
generated C++ was verified **byte-identical**, so the compression changed nothing
semantically.

## Bugs verification caught

- **ffcompile merges same-named anonymous structs.** `trun`'s `entry` and `senc`'s
  `entry` compile to one class — `trun` was writing 8-byte per-sample-IV records
  instead of its flag-selected fields. Renamed to `run_entry`.
- **Mined equality comparisons pin fields.** `if (sample_size == 0)` in `stsz`
  made ffcompile mine `{0}` for the whole `sample_size` class, shared with
  `trun`'s per-sample size — every fragment sample was zero-length and
  `mov_read_trun` rejects that outright. Fixed with a local copy; same fix on
  `boxheader.size == 1`, which was pinning every box size to 1.
- **A plant that lands past its box poisons the next header.** The `stsc` entry
  plants ran unconditionally, so a zero-entry `stsc` wrote into the following
  box's size field; the bitmap then refused the real plant and a garbage size
  followed.
- **`vmhd`'s flags byte is a bitfield** — `ReadUByte` lookaheads there assert.
- **Fatal gates found by probe:** `hdlr` shorter than 24 body bytes → "overread
  end of atom"; `saio` with more than one entry → `AVERROR_PATCHWELCOME`; a `moof`
  without a `trex` → "error reading header"; a `uuid` box with arbitrary content →
  fatal (and not in the JSON's set either).
- **Seed-draw skew.** FormatFuzzer draws a bare byte in 1..16 seven eighths of the
  time, so selectors written as `(S[i] / 64) % 2` were almost always zero — the
  verified codec configuration was being planted on ~12% of tracks instead of
  75%, and the `stsz` table variant never appeared. Every selector now uses a
  modulus of its own free byte.
