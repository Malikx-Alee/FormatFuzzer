# WAV — `templates_originals/wav-orig.bt` → `templates_llm/wav-llm.bt`

Inputs: the original template and
`llm_learned_specification/llm_reterived_constraints_wav-llm_opus5.json`
(68 constraints, 46 dependencies, 19 structure rules, 14 template deviations,
7 schema extensions). `templates/wav.bt` was never opened; the original under
`templates_originals/` is byte-identical to HEAD.

## Shape of the diff

574 → 1381 lines: **53 removals, 860 additions**. All 104 declared identifiers
(structs, typedefs, fields, functions, read-function names, switch case labels)
survive. Of the 53 removed lines, 51 are field declarations that come back with
a value set, a range attribute or a comment. **Only two statements changed**:

```
-while( !FEof() )
+while( !FEof( wavEofP ) )

-    ReadBytes( tag, FTell(), 4 );
+    ReadBytes( tag, FTell(), 4, wavTagValues, wavTagValues, 1.0 );
```

Everything else is additive: a 631-line generation-plan block inserted between
the `haveValidFormat` local and the first struct, 301 comment lines, 23 value
lists on field declarations, 26 range attributes, and nine one-line plant calls —
one at the top of each chunk struct plus two for the RIFF header.

## The central problem: sizes before content, and a loop with no terminator

RIFF is a flat stream of self-delimiting chunks. Every chunk states its byte
count before its content exists, the container size at offset 4 states the file's
own extent, and there is **no terminator at all** — the original walks the stream
with `while( !FEof() )` and never consults `hsize`. Left alone, the generate
direction draws four random tag bytes at every chunk boundary and a random 32-bit
size after them: the baseline built from the unmodified original fails to
generate 151 files out of 200 and the 49 that survive have a 20 KB median and a
65 KB maximum.

The rewrite turns the walk into a state machine over chunk boundaries.
`wavPlantHead()` plants the eight header bytes — identifier and size — picked
from a menu of **exactly the headers legal at this point in the stream**, which is
the preferred/possible idiom applied to a whole chunk envelope rather than to the
tag alone. `wavPlantBody()` then plants the fields inside that chunk which have
to agree with it. Because the header goes down before it is read, every size,
count and cross-reference is already right the first time the template looks at
it, and there is **no `FSeek` backpatch anywhere**.

A plant is a lookahead `ReadBytes` whose preferred and possible sets are the same
computed menu with `p = 1.0`: 255 times in 256 an entry is written with the evil
bit suppressed for that call, and the remaining time the same set is redrawn with
evil restored — a net escape near 1/32768 per plant. A one-entry menu is an exact
write; a multi-entry menu picks uniformly **and** plants the choice, which is
where the generator's structural entropy comes from.

### The plan runs in both directions

Gating the plan on `IsParsing()` would make the two directions draw different
numbers of decisions, and FormatFuzzer's round trip — generate, parse,
re-generate from the parsed decisions, compare — only holds when the streams line
up. So the plan runs unconditionally. In the parse direction a plant reads the
bytes that are there; for a file this template generated they are the ones the
plan expected, so the reads cost exactly what the writes did. For any other file
the first header that does not match clears `wavPlanOK` and no further plant is
attempted.

**Every plant lands inside bytes the template is about to read anyway** — the
twelve-byte RIFF header, or the eight-byte chunk header, or a body whose size the
plan has already confirmed — so no plant can reach past the end of a short file.
That is what keeps parse parity exact on truncated input: a bare twelve-byte
`RIFF????WAVE` file still parses under both templates, as do five truncations of
a real file and a non-WAV blob, with identical exit codes.

Result: **10,000 generate/parse/re-generate cycles, 0 round-trip failures.**

### The one field written backwards

`WAVRIFFHEADER.hsize` is the file's total size minus 8, and the data chunk is the
last thing in the file, so the total is known the moment the data chunk's header
is chosen. That is where it is planted — backwards, at offset 4. It is the only
backwards write in the file, and it is safe in both directions: in the parse
direction the bytes already there are the ones the plan computes, so the write
confirms rather than contradicts them.

### Why no `SetEvilBit(false)` on the signatures

The prompt's idiom would wrap `groupID` and `riffType`. It is not used here, on
purpose. Both are planted, and **a planted byte beats the evil bit outright** —
`file_integer` and `file_string` copy the buffer back wherever the bitmap is set,
on every path — so the generation-side protection is already stronger than
suppression. Suppressing the bit would instead break the parse direction: a
non-RIFF file needs an evil decision to be read at all, and with the bit disabled
`file_accessor` asserts "Evil bit is disabled, but an evil decision is required
to parse this file" *before* the template's own
`Warning( "File is not a valid wave file. Template stopped." )` can fire. Keeping
the bit live preserves the original's diagnostic exactly.

## What was implemented, and how

### Constraints

* **`fixed_value` (13 entries)** — the two RIFF signatures and the six chunk
  identifiers get `= { "RIFF" }`, `= { "fmt " }`, `= { "data" }`, `= { "fact" }`,
  `= { "cue " }`, `= { "smpl" }`, `= { "LIST" }`. The trailing space in `fmt `
  and `cue ` is written explicitly: template deviation 11 records that the
  top-level switch compares four raw bytes, so `fmt` with any other fourth byte
  falls to `UNKNOWNCHUNK` and the file is then rejected for having no format
  chunk. `FACTCHUNK.chunkSize = { 4 }`, `wcbsize = { 2 }`,
  `SMPLCHUNK.Sampler_Data = { 0 }`, `dwChunkStart = { 0 }`, `dwBlockStart = { 0 }`
  and `SMPTE_Offset = { 0 }` likewise. The six `padding` entries are covered
  below.
* **`enumerated_values` (8 entries)** — `wFormatTag` gets all twelve registry
  codes, `wBitsPerSample` all six depths, `fccChunk` its two, `LISTCHUNK.chunkType`
  its three, `LISTSUBCHUNK.chunkID` all 28, `SMPLLOOPS.Type` its four,
  `SMPLCHUNK.SMPTE` its five and `SMPLCHUNK.Manufacturer` all 56 MIDI codes the
  display switch names. `wFormatTag` is declared `short`, which is signed, so
  WAVE_FORMAT_EXTENSIBLE has to be written `-2` — template deviation 2.
* **`range_constraint` (26 attributes)** — always the `generation_range` rather
  than the spec bound: `wChannels` 1..2, `dwSamplesPerSec` 8000..48000,
  `dwAvgBytesPerSec` 8000..384000, `wBlockAlign` 1..512 (spec 65535),
  `wSamplesPerBlock` 1..4096, `hsize` 36..262144, `dwCuePoints` 0..16,
  `dwIdentifier` 1..16, `dwPosition`/`dwSampleOffset` 0..65536,
  `Num_Sample_Loops` 0..16, `Cue_Point` 0..16, `Start`/`End` 0..65536,
  `Play_Count` 0..16, `MIDI_Unity_Note` 36..96, `Product` 0..255,
  `Sample_Period` 20833..125000, and every `chunkSize`: 16..40 for `fmt `,
  0..131072 for `data`, 4..388 for `cue `, 36..420 for `smpl`, 4..4096 for
  `LIST`, 1..256 for a subchunk and 0..1024 for an unknown chunk.
* **`calculated_value` (25 entries)** — none is left free. `hsize`, every
  `chunkSize`, `dwAvgBytesPerSec`, `wBlockAlign`, `wSamplesPerBlock`,
  `uncompressedSize`, `dwCuePoints`, `Num_Sample_Loops`, `Sample_Period`, the cue
  positions, the loop bounds and the `listData` payloads are all derived from the
  layout and planted.
* **`pattern_constraint` with `excluded_values`** — `UNKNOWNCHUNK.chunkID` gets
  the JSON's fourteen preferred codes as its value list, and the plan only ever
  plants `JUNK`, `PAD `, `bext` and `id3 `: never one of the six the dispatch
  claims, which would produce a chunk the template's own grammar re-parses with a
  different, fixed-shape layout.
* **`bitmask_constraint`** — `SMPTE_Offset` is hours, minutes, seconds and frames
  packed one per byte, with the frames byte bounded by the rate in a *different*
  field of the same chunk (dependency 33); `= { 0 }` is the one value legal under
  every rate.
* **`lookahead` (7 entries)** — the six chunk-identifier entries share one call
  site, and it now carries the per-call-site set the JSON records:
  `ReadBytes( tag, FTell(), 4, wavTagValues, wavTagValues, 1.0 )`, with
  `const local string ReadBytesInitValues[0]` at the top so it beats the mined
  globals. The seventh, `LISTCHUNK.subchunk`, is the `ReadUInt` peek whose
  `comparison` is `bounds_test` — it has no value set by construction, and the
  constraint it carries is the arithmetic bound at the line below it, which the
  plan satisfies by making every LIST size decompose into whole subchunks.

### The format chunk: dependencies 0–12 hold by construction

The `fmt ` header menu picks one of the four layouts the specification defines —
16, 18, 20 or 40 bytes — and the body menu for that size holds **only internally
consistent combinations**, built in a loop rather than written out:

| size | tag | menu |
|---|---|---|
| 16 | 1 PCM | 2 channels × depths 8/16/24/32 × rates 8000/11025/22050/44100 = 32 entries |
| 18 | 3, 6, 7 | float at 32 bits, both G.711 companders at 8, × 2 channels × 4 rates |
| 20 | 17 DVI ADPCM | depth 4, `wcbsize` 2, `wSamplesPerBlock` from the block formula |
| 40 | 65534 EXTENSIBLE | depths 16/32, cbSize 22, valid-bits, channel mask, the PCM sub-format GUID |

`wBlockAlign` is computed as `wChannels * wBitsPerSample / 8` and
`dwAvgBytesPerSec` as `dwSamplesPerSec * wBlockAlign` inside the loop that builds
each entry, so dependencies 8, 9 and 10 cannot be violated. Dependency 11's
formula — `((wBlockAlign - 4 * wChannels) * 8) / (wBitsPerSample * wChannels) + 1`
— is evaluated for real in the ADPCM builder. Dependencies 4 through 7 pin the
depth per tag, and 0, 1 and 2 pin the size per tag. Over 2,000 files the four
layouts appear 1244 / 252 / 249 / 255 times.

### Dependencies

All 46 appear. The branch-shaped ones were already branches and gained a comment
plus, where useful, a value set: the ADPCM extension (1, 3, 11, 12), the three
mono fast paths and the interleaved case (13–20), the sample sign convention at
the 8-bit boundary (19, 20), the odd-size padding rule (42) and the two structs
that lack it (43). The cross-record ones are enforced by the plan: the data size
is `frames * wBlockAlign` so dependency 21 holds; the fact chunk's
`uncompressedSize` is the decoded frame count (25); every `SMPLLOOPS.Cue_Point`
names an identifier the cue chunk actually wrote (26); `Sample_Period` is
`1000000000 / dwSamplesPerSec` (34); loop `End` is at or after `Start` and both
lie inside the stream (35); `dwChunkStart` and `dwBlockStart` are 0 because there
is no wavl playlist and no block-compressed format (27, 28); and `hsize` is the
file size minus 8 (44).

Dependency 26 is the one implemented as **a value set that grows when its
precondition is met**: the `smpl` header menu offers only the loop-free 36-byte
form until a cue chunk has been written, and the two looped forms appear in the
menu only from then on.

### Structure rules

| rule | how |
|---|---|
| 0 RIFF header first | the two signatures are planted at offsets 0 and 8 before the struct is read |
| 1, 3, 4 one `fmt `, before `data` | stage 0 of the state machine, reachable once |
| 2, 5 exactly one `data` | the only header that ends the stream; always in the menu, forced after four optional chunks |
| 6 `fact` when the tag is not PCM | stage 1, entered only when `wavNeedFact` is set by the body just chosen |
| 7 bound the top-level walk | `FEof( wavEofP )` in place of `FEof()`, plus a cap of four optional chunks |
| 8, 9 at most one `cue `/`smpl` | removed from the menu once written |
| 10 loops require cue points | the growing menu above |
| 11 at most two LIST chunks | counted, removed from the menu at two |
| 12 bound the subchunk loop | 1–3 subchunks per LIST, every one a non-zero even size |
| 13 form type then subchunks | one planted image covering both |
| 14 identifier, size, data, pad | the header menu is the envelope; sizes are measured before they are written |
| 15 a chunk identifier at every boundary | the header menu is a tagged union over the six known ids plus an unknown case |
| 16, 17 no terminator, no trailing bytes | nothing is written after the data chunk, and `hsize` is back-planted from the measured total |
| 18 little-endian | `LittleEndian()` untouched; every image is built little-endian |

### Template deviations

All 14 are annotated on the code they describe and acted on where they change
what may be generated: `Sampler_Data` is always 0 (#0, the one field where a
legal value is unparseable), `hsize` is back-planted (#1), the signed 32-bit
fields are kept well inside the positive range (#2), the `fact` and `cue ` sizes
stay even so their missing padding branches are never needed (#3), `fact` is
exactly 4 bytes (#4), the extensible extension is planted rather than left to
`unknown[]` (#6), every subchunk has a non-zero size and every LIST decomposes
exactly (#7), the format chunk's size is always even so its unguarded padding
read is unreachable (#8), the loop points are frame indices not byte offsets
(#12), and every 'spec'-sourced constraint is treated as binding despite the
template checking almost nothing (#13).

## What could not be expressed, and why

1. **The six `padding` entries are `present_when`-false by construction, and this
   was forced.** Five of the six padding branches read
   `if( (chunkSize & 1) && (FTell() < FileSize()) )`. In the generate direction
   `FileSize()` is not a query — with `has_size` still false it *draws* a uniform
   file length of up to `MAX_FILE_SIZE` and pads the whole of it with random
   bytes before seeking back, then pins `file_size` so every later write must fit
   inside it. One odd chunk size would turn a 2 KB file into a 40 KB one with a
   garbage tail. C++ short-circuit evaluation means the call never happens when
   the size is even, so **every size the plan writes is even** and the pad byte is
   never emitted. That is exactly what the JSON's own rationale says holds for a
   conforming `fmt `, `fact`, `cue ` and `smpl` chunk; for LIST subchunks it costs
   one extra NUL inside a declared ZSTR length, which is legal and common.
2. **`WAVE_FORMAT_ADPCM` (2), `G723` (20), `GSM610` (49), `G721` (64), `MPEG` (80)
   and `MPEGLAYER3` (85) are declared but not generated.** They are in
   `wFormatTag`'s value list and reachable by the evil bit, but each needs a
   format-chunk extension and a real compressed bitstream whose shape the JSON
   does not give — unlike DVI ADPCM, whose extension the template itself reads
   and whose `wSamplesPerBlock` formula the JSON states in full.
3. **`LISTCHUNK.chunkType` `wavl` is declared but not generated.** A wavl playlist
   replaces the data chunk's play order with `data` and `slnt` segments, and
   dependency 28 then makes `CUEPOINT.fccChunk` `slnt` and `dwChunkStart` an
   offset into the playlist. The template has no handling for any of it — the
   JSON says so twice — so a generated wavl would be a structure whose
   cross-references point into something this grammar cannot describe. `INFO` and
   `adtl` are both generated.
4. **`LISTSUBCHUNK.chunkID`'s `ltxt` and `note` are declared but not generated.**
   `ltxt` needs a 20-byte header the JSON describes only in prose, and `note`
   duplicates `labl`'s shape; `labl` is generated and carries the cue-point
   cross-reference dependency 38 requires.
5. **24-bit and 64-bit samples get no typed layout, and that is deliberate.**
   Template deviation 5: the data chunk's guard admits only 8, 16 and 32, so
   24-bit PCM — legal and widely used — lands in the opaque `waveformData` array.
   The generator emits 24-bit anyway, because the file is still structurally
   correct and every real decoder handles it; it simply exercises the opaque
   branch rather than the typed one. 64-bit float is not generated: it needs
   `wFormatTag` 3 with `wBitsPerSample` 64, which dependency 5 allows but which
   nothing downstream here reads.
6. **`SMPLCHUNK.Sampler_Data` can only ever be 0.** Dependency 31 and template
   deviation 0: the template declares the field, displays it as "Sample Data
   (number of bytes)", and then never reads the bytes it counts. Any non-zero
   value leaves that many bytes unconsumed and desynchronises the chunk walk from
   there on. It is the one place where the format permits something this grammar
   cannot parse.
7. **The data chunk's size is derived from the format chunk rather than drawn
   independently.** Every byte of the RIFF header is either a fixed signature or
   the computed container size, and the format chunk is the first thing after it,
   so there is no free byte range left to plant a second structural menu on. The
   frame count is a function of the format body just chosen — 32 distinct sizes,
   multiplied by the optional-chunk choices — and the sample values themselves are
   entirely free, so no two files are alike. The same correlation limit applied to
   ZIP and MP4.
8. **`ReadBytes( tag, ... )`'s preferred set is not split from its possible set.**
   The JSON's six lookahead entries share one call site four bytes wide, but the
   state machine needs the *size* as well as the identifier to know what comes
   next. The split therefore lives in the eight-byte header menu one line above,
   which is strictly stronger: it carries the same ordering information plus the
   envelope. The four-byte call site keeps the JSON's value set so the constraint
   is still declared where the JSON puts it.
9. **`WAVRIFFHEADER.hsize` carries a `<min=36, max=262144>` that no `SetEvilBit`
   may span.** With the evil bit suppressed, a ranged field whose parsed value
   falls outside the range needs an evil decision that the suppression forbids,
   and `file_accessor` asserts. That is why the signature protection is the plant
   rather than `SetEvilBit(false)` — see above.

## Verification

| command | result |
|---|---|
| `./ffcompile templates_llm/wav-llm.bt /tmp/wav-llm-check.cpp` | **exit 0**, "Finished creating cpp generator", no `*ERROR:`/`*WARNING:` lines |
| `./build_new.sh wav-llm` | **exit 0** → `build/wav-llm-fuzzer` 525,440 B, `build/wav-llm.so` 525,384 B; 34 warnings per unit, all `-Wparentheses-equality` |
| `./build/wav-llm-fuzzer fuzz /tmp/wav-llm-out/f{1..200}.wav` | **200/200 created, 0 failed** |
| `./build/wav-llm-fuzzer parse /tmp/wav-llm-out/f1.wav` | **exit 0**; 200/200 round-trip |
| `bash checkers/wav.sh` | **exit 0** on f1; **168/200** encode under `wavpack` |

Sizes over the 200: min 140, median 2,298, mean 2,439, **largest 6,720 bytes**.

Beyond the required commands:

* **The original template parses all 200 generated files.**
* **Parse parity is exact.** Over 25 real files — the 12 in `testcases/wav` plus
  13 built with ffmpeg covering u8, s16, s24, s32, f32, f64, stereo, 6-channel,
  A-law, mu-law, IMA ADPCM, MS ADPCM and a bext-tagged file — the original and
  the rewrite accept the identical set (23 each, 0 differing; the two both reject
  are the 6-channel and 64-bit-float files, which exceed `MAX_FILE_SIZE` in
  either template). Parity also holds on seven degenerate inputs: a bare 12-byte
  `RIFF????WAVE`, five truncations and a non-WAV blob all give identical exit
  codes.
* **Round trip: `./build/wav-llm-fuzzer test` — 9,995 files from 10,000 attempts,
  0 re-generation mismatches.** The baseline built from the original manages
  2,263 from 10,000, failing to generate the other 7,737.
* **An independent conformance walker finds 0 structural violations in 200 and
  0 in 2,000**, recomputing `hsize` against the file length, checking that the
  chunks tile the file exactly, re-deriving `wBlockAlign` and `dwAvgBytesPerSec`
  from the channel count, depth and rate, checking the tag/size and tag/depth
  pairings, the ADPCM `wSamplesPerBlock` formula, the extensible cbSize, valid
  bits, channel mask and sub-format GUID, the data size against the block
  alignment, the fact frame count, the cue size formula and identifier
  uniqueness, the smpl size formula, `Sampler_Data`, `Sample_Period` and every
  loop's cue reference and bounds, and each LIST's decomposition into whole
  NUL-terminated subchunks.
* **Stress, 2,000 files: 2,000 generated, 0 failures, 0 structural violations.**
  The only value-level deviations are 38 evil-bit draws on unplanted declared
  fields the JSON marks `evil_bit_safe` — MIDI pitch fraction, SMPTE, SMPTE
  offset and unity note — which is the evil bit doing its job.
* **Checker rate is entirely a codec question.** Over the 2,000, `wavpack`
  accepts **1,624 and rejects 376**, and the split is exact: every file whose
  `wFormatTag` is 1, 3 or 65534 passes (1,244 + 125 + 255 = 1,624) and every
  A-law, mu-law and DVI ADPCM file fails (60 + 67 + 249 = 376). `wavpack`
  implements no companded or ADPCM codec — it rejects the repo's own
  `test-8000Hz-le-1ch-1byte-ulaw.wav` for the same reason, along with the 20-bit
  and 64-bit files, so 9 of the 12 supplied real WAVs pass it too.
* **Census over the 2,000**: all four format-chunk layouts (1244 / 252 / 249 /
  255), all six generated tags, all five depths, both channel counts, and the
  optional chunks at 154 LIST, 142 cue, 93 smpl, 70 fact and 152 unknown chunks
  spread over `JUNK`, `PAD `, `bext` and `id3 ` — per 200; proportionally the same
  over the full corpus.

### Baseline, for comparison

Built from the unmodified original as `wav-orig-baseline`: it parses 12/12 real
files, but of 200 generation attempts **151 fail outright**, only **49 of its own
files parse**, **0 pass the checker**, and the median size is 20 KB against a
65 KB maximum — it draws a random four-byte tag and a random 32-bit size at every
chunk boundary and lets `FEof`'s default 1-in-8 decide when to stop.
