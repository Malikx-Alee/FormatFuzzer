# AVI — `templates_originals/avi-orig.bt` → `templates_llm/avi-llm.bt`

Inputs: `templates_originals/avi-orig.bt` and
`llm_learned_specification/llm_reterived_constraints_avi-llm_opus5.json`.
`templates/avi.bt` was not opened. The original is unmodified.

Diff shape: 304 → 738 lines, 70 removals / 504 additions. All 189 identifiers from the
original survive. Almost every "removal" is a field declaration that gained a trailing
comment or an init list on the same line; the only two genuine statement changes are
`} while (pointer != stop);` → `} while (pointer < stop);` and
`while (!FEof())` → `while (!FEof(aviEofP))`.

## Verification

| Command | Result |
|---|---|
| `./ffcompile templates_llm/avi-llm.bt /tmp/avi-llm-check.cpp` | exit 0, "Finished creating cpp generator" (the `Motorola format` / `Intel format` lines are the template's own Printfs firing against ffcompile's empty dummy input) |
| `./build_new.sh avi-llm` | exit 0 → `build/avi-llm-fuzzer` (502,288 B), `build/avi-llm.so` (502,232 B); 22 warnings, all `-Wparentheses-equality` and one `-Wbraced-scalar-init` from ffcompile's own mining output |
| `./build/avi-llm-fuzzer fuzz /tmp/avi-llm-out/f{1..200}.avi` | exit 0, 200/200 created, no failures |
| `./build/avi-llm-fuzzer parse /tmp/avi-llm-out/f1.avi` | exit 0; 200/200 of the batch round-trips |
| `bash checkers/avi.sh` | exit 0 on f1; **200/200 PASS** — ffmpeg demuxes and re-encodes every file |

**Largest generated file: 19,792 bytes** — min 594, median 3,782, mean 5,510. The ceiling
is about 20 KB: eight frames of at most 2,304 bytes plus an interleaved PCM track.

Beyond the required commands:

* **The original template parses all 200 generated files.** That is the sharpest available
  check that the rewrite still speaks the grammar it was derived from.

* **An independent AVI conformance walker finds 0 violations in the 200 files.** It
  re-derives every quantity from the specifications rather than trusting the generator:
  `ROOT.datalen == filesize - 8` and the top-level walk landing exactly on the end; hdrl
  first, opening with a 56-byte avih, and its size covering the avih *and* the strl lists
  nested inside it; `dwStreams` equal to the strl count; `dwReserved1`, `dwInitialFrames`
  and `dwReserved[4]` zero; AVIF_HASINDEX set exactly when an idx1 exists, and idx1 last;
  per stream a 56-byte strh with zero `dwReserved1`/`dwInitialFrames`/`dwStart`/`rcFrame`
  and `dwQuality <= 10000`; for video `dwSampleSize == 0`, a 40- or 44-byte strf,
  `biSize == 40`, `biPlanes == 1`, BI_RGB, `biWidth`/`biHeight` matching the main header,
  `biSizeImage` equal to the padded row stride times the height, `biClrUsed == 0` at every
  direct-colour depth, a 44-byte strf only at a palettised depth and with `rgbReserved`
  zero, `dwMicroSecPerFrame == 1000000 * dwScale / dwRate`, and `dwLength == dwTotalFrames`;
  for audio an 18-byte strf, PCM tag, `cbSize == 0`, `nBlockAlign == nChannels *
  wBitsPerSample / 8`, `nAvgBytesPerSec == nSamplesPerSec * nBlockAlign`, and
  `dwSampleSize`/`dwScale`/`dwRate` echoing them; a strn closing each strl exactly at the
  list end; the movi children summing exactly to the list size, every chunk identifier
  `NNxx` with `NN` below `dwStreams`, the `##db` count equal to `dwTotalFrames`, every
  frame chunk exactly one frame long and every audio chunk a whole number of blocks; and an
  idx1 whose length is a multiple of 16 with one entry per chunk, each entry's ckid, offset
  and length matching the chunk it points at.

* **Parse parity is exact.** Over 23 real AVIs (`testcases/avi`, `testcases_4_learn/avi`,
  `coverage_targets`) and 300 sampled from `output/avi*/…/valid/`, the rewrite accepts and
  rejects **the identical set** as a baseline built from the untouched original: 20/23 and
  300/300, **0 files differing** in either direction.

* **Census over 200 files:** all four generated pixel depths (8 bpp ×38, 16 ×55, 24 ×59,
  32 ×48); 122 single-stream and 78 with an interleaved PCM track, covering all eight
  channel/rate/depth audio combinations; 1 to 8 frames, roughly uniform; 91 files carrying
  a JUNK chunk and 164 an index; all four top-level sequences
  (`hdrl movi`, `hdrl movi idx1`, `hdrl JUNK movi`, `hdrl JUNK movi idx1`); and both the
  odd and the even strn length, so the RIFF pad-byte branch is exercised in every file.

## What I implemented

### The problem this format poses

RIFF is nested length-prefixed chunks with no terminator, so **every size is written before
the bytes it measures**: `ROOT.datalen` is the whole file, the hdrl list's size covers strl
lists that have not been laid out yet, the movi list's size must equal the summed padded
sizes of its children, and the idx1 offsets are measured from a list that does not exist
when the header is written. On top of that the movi walk is the template's
most dangerous construct: `while (pointer != stop)` is an exact equality with no end-of-file
guard, so overshooting by one byte makes it read chunks off the end of the file forever.

The rewrite answers all of it with one mechanism: **`aviPlanMain()` chooses one complete
layout up front and every header byte is PLANTED through ffcompile's lookahead**, so each
size is correct the first time it is written. A planted byte is copied back over every write
path in `file_accessor.h`, the evil-bit one included, so the plants are exact. There is no
`FSeek`-and-rewrite backpatch anywhere in the file — the two sizes that genuinely cannot be
known in time (`ROOT.datalen` at offset 4 and the hdrl size at offset 16) are planted
*backwards* from the planner instead, which needs no `SetEvilBit(false)` and therefore
cannot make the parse direction reject anything.

### Constraints

* **`ROOT.id` and `ROOT.form` (fixed_value, `evil_bit_safe: false`)** — the only two fields
  in the template protected by `SetEvilBit(false)` rather than by a plant, so that a
  lookahead escape can never cost a file its signature. Everything else keeps the evil bit
  on and relies on the plant.
* **`ROOT.datalen`, `LISTHEADER.datalen`, `avihHEADER.datalen` (56), `strhHEADER.datalen`
  (56), `strfHEADER_BIH.datalen` (40/44), `strfHEADER_WAVE.datalen` (18),
  `strnHEADER.datalen`, `genericblock.datalen`, `idx1HEADER.datalen` (calculated_value)** —
  all computed by the planner and planted; none is ever drawn.
* **The nine four-character codes** (`avih`, `strh`, `strf` ×2, `strn`, `LIST`, `JUNK`,
  `idx1`, and `LISTHEADER.type`) carry `= { "…" }` init lists as documentation; the plants
  are what make them exact.
* **`MainAVIHeader.dwReserved1`, `dwInitialFrames`, and `dwScale`/`dwRate`/`dwStart`/
  `dwLength` (fixed_value 0)** — the last four are AVIMAINHEADER's `dwReserved[4]`, not
  timing fields (template_deviations #5); the real scale and rate live in the stream header
  and the generator emits zeros here, as the deviation's action asks.
* **`AVIStreamHeader.dwReserved1`, `dwInitialFrames`, `dwStart`, `xdwQuality`,
  `xdwSampleSize` (fixed_value 0)** — the last two are really `RECT rcFrame`
  (template_deviations #6) and `dwReserved1` is really `wPriority` + `wLanguage`
  (template_deviations #7); zeros satisfy every reading.
* **`AVIStreamHeader.dwQuality`** — 10000, the preferred value and the top of its range.
* **`BITMAPINFOHEADER.biSize` (fixed_result 40), `biPlanes` (1), `biCompression` (BI_RGB),
  `biSizeImage` (calculated)** — planted; `biSizeImage` is the padded stride times the
  height, which is also exactly the size of every `##db` chunk written.
* **`RGBQUAD.rgbReserved` (fixed_value 0)** — zero in the single colour entry.
* **`WAVEFORMATEX.wFormatTag` (PCM), `cbSize` (0), `nBlockAlign`, `nAvgBytesPerSec`** — all
  fixed or derived; see dependencies 26–28.
* **`AVIINDEXENTRY.dwFlags`** — AVIIF_KEYFRAME, the preferred value.
* **Generation ranges** — `dwWidth`/`dwHeight` 1..64, `dwTotalFrames` 1..8, `dwStreams`
  1..2 are enforced by the menus *and* by explicit clamps after the read-back, so a
  lookahead escape yields a small inconsistent file rather than a runaway.

### Dependencies

* **0, 1 (byte order and the signature pair)** — `RIFF` is emitted, so the little-endian
  branch is taken; the form type is the paired fixed value the original already checks.
* **2, 3, 4, 5 (what each LIST form type contains)** — the original's four-way dispatch,
  unchanged; the planner only ever produces `hdrl`, `strl` and `movi`, and the `else` arm
  that swallows an unknown form whole is left in place for the parse direction.
* **6, 39 (a LIST below 4, and an empty movi)** — the movi list always holds at least one
  chunk and its size is always `4 + the summed children`, so neither underflow is reachable.
* **7, 8, 9 (fccType selects the strf layout)** — the original's if/else chain; the
  generator writes `vids` and `auds`, the two that reach a modelled layout.
* **10, 11, 12 (dwSampleSize and the audio scale/rate)** — video writes 0, audio writes
  `nBlockAlign`, `dwScale = nBlockAlign` and `dwRate = nAvgBytesPerSec`.
* **13 (dwMicroSecPerFrame == 1e6 · dwScale / dwRate)** — the video stream is fixed at
  1/25, so the main header carries exactly 40000, which is also the preferred value.
* **14 (the frame count appears three times)** — `dwTotalFrames`, the video stream's
  `dwLength` and the `##db` chunk count are all the same planner variable.
* **15 (handler and compression name the same codec)** — `DIB ` with BI_RGB.
* **16 (biSize 40)**, **17 (BI_RGB needs a real depth)**, **19 (direct colour has no
  palette)**, **20 (biSizeImage from the geometry)**, **21 (the geometry is declared
  twice)** — all planted from one arithmetic.
* **18, 22 (the palettised depth and the 44-byte trigger)** — the one place the template's
  own quirk is turned into coverage: at 8 bpp the generator writes `biClrUsed = 1`, a
  44-byte format chunk and exactly one RGBQUAD, which is simultaneously self-consistent and
  exactly what `if (datalen == 44)` models. Dependency 22 is the only reachable path to
  `bmiColors`, and 38 of 200 files take it.
* **23, 24 (the two underflowing trailing arrays)** — `exData` is zero-length in both
  layouts by construction, because 40/44 and 18 are the only sizes emitted.
* **25, 26, 27, 28 (the WAVEFORMATEX arithmetic)** — `cbSize = 0` pins the chunk at 18;
  `nBlockAlign = nChannels · wBitsPerSample / 8` and `nAvgBytesPerSec = nSamplesPerSec ·
  nBlockAlign`; the depth is 8 or 16, both whole bytes.
* **29, 30, 31 (the index and the has-index flag)** — the flag menu decides, and the idx1
  chunk is emitted if and only if bit 0x10 is set, so the implication holds both ways.
* **32, 33, 34 (the index is a parallel table)** — `aviIdxImage()` rebuilds the entries from
  the same layout that produced the chunks: one entry per chunk, in order, ckid equal to the
  chunk's identifier, length equal to its `datalen`, offset measured from the `movi`
  four-character code, and a total that is a multiple of 16.
* **35, 36 (dwStreams and the chunk identifiers)** — the strl count is the planner's
  `aviStreams`, and each chunk's first two characters are its stream index.
* **37 (interleaving and dwInitialFrames)** — zero throughout, which is what a
  non-interleaved file requires.
* **38, 40 (the movi sum and the pad byte)** — the padded size of every chunk is summed into
  the list's `datalen`, so `pointer` reaches `stop` exactly; audio chunks with a one-byte
  block alignment come out odd and exercise the pad-byte branch on both sides of the
  arithmetic.

### Structure rules

* **0, 1, 2, 3, 4, 6, 18 (the required regions and their order)** — the top-level sequence
  is always hdrl, then one strl per stream, then an optional JUNK, then movi, then an
  optional idx1, and the strl group is always strh/strf/strn.
* **5, 7, 8 (bounded repetition)** — the top-level walk is bounded by the planned chunk
  count, the movi list by 1–16 chunks, and the whole file by about 20 KB.
* **9 (the chunk envelope)** — every chunk's payload is decided before its size is written,
  which is the entire point of the planner.
* **10, 11 (the index)** and **12 (JUNK anywhere)** — covered above; JUNK is placed just
  before the movi list, where real writers put it.
* **13, 15 (no terminator, no trailing bytes)** — nothing is emitted after the last chunk
  and `ROOT.datalen` is the measured total.
* **14 (an unrecognised top-level identifier)** — the original's `Printf` + `return -1` arm
  is kept; it is what catches a corrupted identifier during generation too.
* **16 (byte order)** — `RIFF`, little-endian throughout.
* **17 (the three strf layouts are mutually exclusive)** — the original's if/else chain.

### The two statement changes

**`} while (pointer < stop);`** — template_deviations #0 calls the original's
`pointer != stop` the template's most dangerous construct, and it is: there is no `<`
comparison and no end-of-file guard, so one byte of overshoot means the walk never
terminates. `<` exits on the same iteration for every file whose chunk sizes sum exactly,
and terminates instead of running away when they do not. It is the one place the rewrite
changes what the parser accepts, and it strictly shrinks the set of inputs that hang.

**`while (!FEof(aviEofP))`** — `FEof`'s probability argument is the loop's only lever.
`feof()` returns 0 without consuming a decision whenever `file_pos < file_size`, and
consults randomness only at the true end. In parsing, `p = 0.0` makes it *exact*: the parse
lambda yields 255 at end of file and 0 elsewhere, and the threshold `255 * (1 - 0)` splits
them perfectly. In generation, `p = -1.0` puts the threshold at 510, out of `rand_int(256)`'s
reach, so the walk cannot end early; the planner then sets `p = 1.0` after the last planned
chunk, which puts the threshold at 0 and ends it exactly. The alternative — leaving the
default `p = 0.125` — is a one-in-eight chance of truncating the file at *every* chunk
boundary.

## What I could not express, and why

* **`strhHEADER.data` is 56 bytes, not the 64 the JSON states.** `fixed_result: 64`,
  `LISTHEADER.strh: fixed_result: 72` and template_deviations #12 ("A 56-byte strh — which
  some real files write — makes the template read eight bytes into the next chunk") all have
  this backwards. The template's `AVIStreamHeader` is fourteen DWORDs, and Microsoft's
  `AVISTREAMHEADER` is `4+4+4+2+2+4+4+4+4+4+4+4+4+8` — both exactly 56, and **all eleven
  real AVIs in `testcases/avi` write `strh` with a datalen of 56**. Emitting 64 desynchronises
  the parse by eight bytes, which is how I found it: the first hand-built layout I tried was
  rejected by the original template until I dropped it to 56. The rewrite emits 56 and treats
  the rest of that deviation entry — that declared sizes are never used to bound the
  fixed-shape structures — as correct.

* **The pixel depth rides on the frame width instead of being planted where it lives.**
  `AVIMAINHEADER` has no free field to carry it: every one of its fourteen words is either a
  fixed value or a calculated one, and the planner needs the depth before it can size
  anything. Planting `biBitCount` where it belongs would mean a forward plant 140 bytes into
  the format chunk, which reads past the end of a short file while parsing. So the geometry
  menu covers all four residues of the width mod 4 and the depth is derived from it. Every
  depth still occurs (38–59 files each of 200), but width and depth are correlated.

* **The WAVEFORMATEX parameters are derived, not planted, for the same reason** — the audio
  strl is emitted as one contiguous 122-byte image, and a decision plant inside it would
  have to split that image into three. Channels come from the frame count, sample depth from
  the width and sample rate from the height. All eight combinations appear across a corpus,
  but they are a function of the video geometry rather than independent draws.

* **A byte already marked in the lookahead bitmap can never be re-planted.** `file_string`
  filters the menu to entries compatible with the marked bytes and falls through to a plain
  read — which copies the *old* bytes back — when none match. This cost me a debugging pass:
  planting `"RIFF" + 0 + "AVI "` as one image and then trying to correct offsets 4..7 left
  `ROOT.datalen` at zero in every file. The fix is structural rather than clever: the two
  fields that must be planted late are deliberately left out of the early plants.

* **`SetEvilBit(false)` can only ever wrap a single field in this template.** ffcompile mines
  the `datalen == 44` test in `strfHEADER_BIH` into a known value for **every** field named
  `datalen`, since the generated code shares one object per field name. Leaving the evil bit
  suppressed across `ROOT.datalen` therefore made every container size other than 44
  unparseable — 200 of 200 of the generator's own files failed to round-trip until the
  suppression was lifted between `id` and `form`. The same sharing is why no `<min=>`/`<max=>`
  attribute appears on any `datalen`, `id` or `data` field: a range registered under one of
  those names would silently apply to all fourteen structs that use it.

* **The planner runs in generation only** (`IsParsing()`, used once). Its numbers describe a
  layout it chose; replaying them against a real AVI — whose frames are compressed and whose
  chunk sizes are its own — would be meaningless, and the two backwards plants would fail
  outright against bytes already parsed. Gating it is what makes parse parity exactly zero
  files differing. The cost is that a parse and a regeneration from the same decision buffer
  consume different numbers of decisions, which is the same asymmetry the documented
  backpatch idiom has.

* **Only `DIB `/BI_RGB video is generated.** `checkers/avi.sh` runs
  `ffmpeg -f avi -i - output.avi`, which *decodes* and re-encodes rather than merely
  demuxing, so a stream whose frames are not real codec bitstreams fails. I measured this: an
  `XVID` stream with a 64-byte frame is rejected, and so is a `DIB ` stream whose frame size
  does not equal the padded stride times the height. That fixes every `##db` chunk at exactly
  one frame and rules out `MJPG`, `H264`, `XVID` and the rest of the `fccHandler` enumeration,
  as well as the `txts`/`mids` stream types and the generic `strfHEADER` branch, which no
  player would accept either.

* **`rec ` and `odml` lists, the OpenDML `AVIX` form, multiple JUNK chunks and `INFO` lists
  are not generated.** Structure rule 14 makes `LIST`, `JUNK` and `idx1` the only identifiers
  the template accepts at the top level, and it swallows an unknown LIST form whole rather
  than descending into it — so emitting one would add bytes no reader of this template
  validates. They stay reachable in the parse direction, which is where real files need them:
  six of the eleven real AVIs carry an `INFO` list or a JUNK chunk between hdrl and movi, and
  all six still parse.

* **`BITMAPINFO` is left dead.** template_deviations #8 records that the struct is typedef'd
  and never instantiated, and its two constraints entries are flagged
  `unused_in_parse_flow`. Wiring it up would change what the template reads; it is kept
  verbatim, unused.

## The residual failure mode

`ReadBytes(…, preferred, preferred, 1.0)` is exact 255 times in 256; the remaining roll
re-draws from the same set with the evil bit *restored*, a further 1 in 128 — about 1 in
32,768 per plant. That fallback is not a defect to remove: it is exactly what lets the parse
direction stay tolerant, since with the evil bit suppressed a parse of any file whose bytes
differ from the menu would assert. A typical file carries about twenty-three plants.

Over a 2,000-file stress run: **1,998 of 2,000 generated and 2,000 of 2,000 accepted by
ffmpeg.** Two generations aborted through the template's own `return -1` arm when an escape
corrupted a chunk identifier — no crash, no large file, and the truncated results still
demux. Two further files carried a header field that disagrees with the layout around it;
the explicit clamps on width, height, frame count and stream count are what keep such a file
small and terminating instead of letting one bad draw ask for a multi-megabyte frame or a
billion stream lists.

## Incidental findings

* `checkers/avi.sh` reads `out.avi` from the working directory over stdin
  (`ffmpeg -y -f avi -i - output.avi <out.avi`) rather than taking a path argument. Because
  it re-encodes rather than remuxes, it is a much stronger test than a container walk — it
  rejects a raw-video stream whose frame size is wrong — but it says nothing about whether
  the hdrl list's size covers its children, whether the idx1 offsets point at the chunks they
  name, or whether `dwStreams` matches the number of stream lists. The independent walker
  described above checks all three.

* The original template parses 20 of the 23 corpus files and all 200 generated ones. The
  three it rejects are rejected by the rewrite too.
