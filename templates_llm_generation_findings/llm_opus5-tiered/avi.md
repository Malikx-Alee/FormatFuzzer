# AVI — tiered generative template findings

| | |
|---|---|
| **Output** | `templates_llm/llm_opus5-tiered/avi-llm.bt` — **456 lines** from a 304-line original, **1.5000×** (at the limit) |
| **Inputs** | `templates_originals/avi-orig.bt` + `llm_reterived_constraints_avi-llm_opus5-tiered.json` |
| **JSON** | 86 constraints (A 30 / B 8 / C 48), 16 dependencies, 14 structure rules, 16 diversity axes |
| **Target** | FFmpeg 6.1, `ffmpeg -y -f avi -i FILE out.avi` |

## Verification

| step | result |
|---|---|
| 1 `ffcompile` | exit 0 |
| 2 `build_new.sh` | exit 0 |
| 3 generate 200 | 0 errors; **195/200 distinct sizes**, most common **twice** (1%), min 354, p25 783, median 1621, p75 3205, p95 33055, max 34753 |
| 4 round-trip `parse` | **200/200** |
| 5 gate | **three separate regressions, all diagnosed and fixed** (below) |

**Coverage: 4.4% (22682/521084) → 6.5% (34111/521084), +2.1 points / +11429
lines / +790 functions.** 11624 mine-only against 195 baseline-only. Both runs
used the same instrumented FFmpeg tree, minutes apart.

Almost entirely decoders and encoders the baseline never instantiates:

| file | Δ | file | Δ |
|---|---|---|---|
| `libavcodec/ac3enc.c` | +753 | `libavcodec/wma.c` | +177 |
| `libavformat/demux.c` | +461 | `libavcodec/wmadec.c` | +166 |
| `libavcodec/motion_est.c` | +303 | `libavcodec/huffyuvdec.c` | +160 |
| `libavcodec/mpegvideo_enc.c` | +269 | `libavcodec/msvideo1.c` | +148 |
| `libavcodec/h264dec.c` | +224 | `libavcodec/mjpegdec.c` | +147 |
| `libavcodec/rawdec.c` | +182 | `libavcodec/ffv1dec.c` | +128 |

---

## What had to be measured, and what it overturned

The JSON carries a `measured_gate` on nearly every entry, taken against **ffmpeg
7.1.1**. The harness here is **6.1**. Two of its conclusions do not hold, and
both were worth thousands of lines.

**1. `genericblock.id` is not free.** The JSON records it Tier C with "measured
completely free — even 'xxxx' decoded". In 6.1, `avidec.c:1273` calls
`get_stream_idx(d)`, which returns **100** for any non-digit prefix, and
`if (n < s->nb_streams)` then fails, so every media chunk is skipped and no
packet is ever produced:

| chunk id | lines |
|---|---|
| `00db` | **17028** |
| `xxxx` | 12150 |

A non-digit prefix costs **4878 lines** — the entire decode and re-encode
pipeline. Dependency[14] ("the two leading digits are the zero-based index of the
stream") is a real format rule, so this is the sanctioned Tier C exception: the
digits are derived, the suffix (`db`/`dc`/`wb`/`pc`/`tx`) varies freely.

**2. `AVIINDEXENTRY.ckid` is the same trap.** `avi_read_idx1` derives the stream
index from the same two ASCII digits (`avidec.c:1647`) and `continue`s past every
out-of-range entry. With a bare `ckid` the index is read and entirely discarded,
losing the entry loop, the non-interleaved detection and the index-driven seek
path.

**3. A correct codec payload is worth almost nothing; the codec *field* is worth
everything.** Each `biCompression` value measured against a BI_RGB base, all with
an uncompressed payload:

```
HFYU +2003   H264 +1536   XVID/DIVX/DX50/FMP4/MP4V ~+1360   MSVC/CRAM +1316
BI_BITFIELDS +1116   VP80 +924   cvid +811   RGBA +778   FFV1 +757   MJPG +675
IV50 +431   IV41 +359   ULRG +314   IV32 +260   BI_RLE8 +201   BI_RLE4 +190
```

And a *real* Microsoft RLE8 stream measured **1300** against **1307** for random
bytes of the same length — the same result found on BMP. So no lines were spent
on an RLE or JPEG emitter.

**4. An audio-only file is the single largest lever in the format** — **+4739
lines** over a video-only base, more than any video codec. That is why `fccType`
is emitted across all four kinds rather than pinned to `vids`: whichever stream
is index 0 is the one the chunks feed.

---

## Expressed

### Constraints

**All 30 Tier A entries.** Fixed values (`RIFF`, `AVI `, `avih`, `strh`, `strf`
×3, `strn`, and `56` for both header lengths) each sit inside a
`SetEvilBit(false)` guard with a distinct local name. Every calculated length is
backpatched from the bytes actually written, **innermost first** per
structure[13]: `genericblock.datalen` → the movi `LISTHEADER.datalen` → the hdrl
length (written when the movi list starts, because it spans every strl list) →
`ROOT.datalen` at end of file. `biSize` = 40; `biSizeImage`,
`nAvgBytesPerSec`/`nBlockAlign`/`cbSize` are computed from their inputs; each
`AVIINDEXENTRY`'s offset and length are computed as `4 + i * chunkstride` and the
payload size.

**All 8 Tier B entries** with their complete `valid_values`, `preferred_value`
applied as repetition weighting and nothing filtered: `biCompression` (29),
`wFormatTag` (25), `biBitCount` (8), `fccType` (4), `LISTHEADER.type` (5), and
the three bitmask fields as sets of single bits and combinations.

### Dependencies — all 16

[0]–[2] select the strf variant from `fccType`, which is what the template's own
if/else already does; [3]–[7] size the payload and the format-chunk tail from the
codec and depth; [8]–[9] derive `nBlockAlign`/`cbSize` from the format tag (with
a lookahead, because `nBlockAlign` is declared *before* the `wBitsPerSample` it
derives from); [10] is the movi list's exact-equality requirement; [13] pairs
`AVIF_MUSTUSEINDEX` with a real idx1; [14] is the chunk-id routing above.

### Structure — all 14

`first_element`/`last_element` are the RIFF head and idx1 tail; `ordering` is a
state-driven lookahead that offers only the legal list type at each point
(`hdrl` → `strl`+ → `movi` → `INFO`/`odml`); `required` means the loop cannot end
before a movi list exists; `forbidden` (structure[6], an empty movi list) is
honoured by the do/while; structure[11] is why the top-level tag lookahead is
evil-guarded — anything but LIST/JUNK/idx1 makes the template abandon the parse.

**The movi list is the delicate one.** The template's
`do { genericblock gb; pointer += sizeof(gb); } while (pointer != stop)`
terminates on **exact equality**, so the frame count is derived from the free
`datalen` (`nfr = (datalen - 4) / chunkstride`), `stop = nfr * chunkstride`, and
`datalen = stop + 4` is backpatched. That is idempotent, so the parse direction
recomputes the same `nfr`.

### `payload_wellformedness` — one entry, three constructions

`genericblock.data` is the only entry, and `applies_when` makes it three
contracts:

| stream 0 is | codec | size derivation |
|---|---|---|
| `vids` | BI_RGB and every other `biCompression` | `((biWidth * biBitCount + 31) / 32) * 4 * abs(biHeight)` — the exact DIB frame length, a product of three free fields |
| `auds` | the `wFormatTag` in force | `nBlockAlign * 64`, and `nBlockAlign` is itself `nChannels * wBitsPerSample / 8` (or the codec's fixed block for tags 2 and 17) |
| `txts` / `mids` | none | the opaque `strf` payload length, which the template reads as free bytes |

`abs(biHeight)` is computed from the unsigned field so a negative height
(top-down rows) sizes the frame identically while still reaching the other
row-indexing path. None of `biWidth`, `biHeight`, `biBitCount`, `nChannels` or
`wBitsPerSample` is ever adjusted to fit a payload.

### `diversity_axes` — all 16 confirmed

**Tier C, declared bare:** `BITMAPINFOHEADER.biWidth`, `.biHeight`, `.biClrUsed`,
`WAVEFORMATEX.nChannels`, `.nSamplesPerSec`, `.wBitsPerSample`,
`MainAVIHeader.dwStreams`, `.dwTotalFrames`, `AVIStreamHeader.dwScale`, `.dwRate`,
`JUNKHEADER.data`.

**Tier B, whole set** (the `tier_note` says emit every member, not the convenient
one): `biBitCount`, `biCompression`, `wFormatTag`, `MainAVIHeader.dwFlags`.

**The one axis deliberately constrained:** `genericblock.id`, under
dependency[14], for the measured reason above. Its `why` asks for `db`, `dc`,
`wb`, `pc` and multi-stream routing — all five suffixes and four stream indices
are emitted, which is more of that axis than a bare field reaches.

A grep for `<min=`, `<max=`, `generation_range`, `practical` and `sensible`
returns **zero**.

Confirmed in the 2000-file corpus: **31 distinct `biCompression` values** (all 29
legal plus evil-bit extras), **all 25 `wFormatTag` values**, all 8 `biBitCount`
values, all four `fccType` kinds (auds 768, vids 733, txts 244, mids 232), all
five LIST types, 1–6 strl lists per file, 5 files with a negative `biHeight`,
JUNK in 1745 files and idx1 in 1388.

---

## Not expressed

- **RIFX, or any form type other than `AVI `.** Tier A pins both, and the
  template's own `Strcmp` guard aborts on anything else. The JSON records that
  ffmpeg's AVI demuxer rejects RIFX outright, so the template's big-endian branch
  is unreachable by construction — kept as parser-side code.
- **A real 256-entry palette parsed *as* a palette.** `strfHEADER_BIH` reads an
  `RGBQUAD` only when `datalen == 44` exactly, so a 1064-byte video `strf` is
  parsed as a 40-byte header plus 1024 opaque bytes. The JSON flags this as a
  `template_parse_requirement`; the table is emitted into `exData`, which is where
  the template puts it and where ffmpeg reads it from anyway.
- **The 16-byte legacy WAVEFORMAT.** `exData` is sized `datalen - 18`
  unconditionally, so anything shorter than 18 gives a negative length. Another
  `template_parse_requirement`, honoured.
- **An empty movi list**, and **any top-level chunk other than LIST, JUNK or
  idx1** — structure[6] and structure[11] forbid both, and the template cannot
  parse them.
- **`indx` OpenDML super-index chunks** (`avidec.c:991–1017`). The template's strl
  branch is strh/strf/strn positionally and the JSON does not model `indx`.
- **Frames larger than the output budget.** structure[5] says to "redraw the
  dimension and depth triple rather than clamping any of them"; a `.bt` field is
  written once, so it cannot be redrawn. The *payload* is truncated at 32768 bytes
  instead, which reaches `AVERROR_INVALIDDATA` (measured +99). `biWidth`,
  `biHeight` and `biBitCount` keep their full free span — the trade the prompt
  prescribes when a payload cannot be built for arbitrary sizes.
- **Audio format tags outside the JSON's 25-value set** — WMA Voice (`0x000A`) and
  MetaSound (`0x0075`) account for 41 of the 195 baseline-only lines, along with
  24 lines of `msrledec.c` that need a genuinely well-formed RLE stream.

None of these was worked around by constraining a Tier C field.

## Three regressions, three separate bugs

**Attempt 1 measured 2807 lines against the baseline's 22682.** The nested Tier A
chunk identifiers (`avih`, `strh`, `strf`, `strn`) had been left as bare
`char id[4]` on the assumption that a lookahead pinned them, as it does for the
top-level `LIST`/`JUNK`/`idx1`. Nothing looks ahead at them, so they were four
random bytes and ffmpeg found no streams at all. Fixed with a guarded value set
on each.

**Attempt 2 parsed 0/200.** `if (datalen == 44)` in `strfHEADER_BIH` made
ffcompile mine `44` into the **shared** `datalen` class — every bare length field
in the file, including `ROOT.datalen`, was pinned to 44, and the parse side
demanded it. Comparing a local copy fixed it. (The same mechanism, via
`root.id[3] == 'X'`, was poisoning the RIFF magic with `'X'`.)

**Attempt 3 lost every chunk header.** The hdrl backpatch restored with
`FSeek(lp)`, but `lp` is recorded *before* the list's `type[4]`, so each movi
chunk's id and length were written over the `movi` FOURCC. Worth 486 lines and,
more importantly, every digit-prefixed chunk id.

**Ladder: 2807 → 31730 → 32216 → 34111.**
