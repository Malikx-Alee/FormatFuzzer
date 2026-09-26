# PNG — tiered generative template findings

| | |
|---|---|
| **Output** | `templates_llm/llm_opus5-tiered/png-llm.bt` — **582 lines** from a 388-line original, **1.5000×** (at the limit) |
| **Inputs** | `templates_originals/png-orig.bt` + `llm_reterived_constraints_png-llm_opus5-tiered.json` |
| **JSON** | 76 constraints (A 15 / B 17 / C 44), 31 dependencies, 21 structure rules, 16 diversity axes |
| **Target** | libpng 1.6.57, `pngtest -m` |

## Verification

| step | result |
|---|---|
| 1 `ffcompile` | exit 0 |
| 2 `build_new.sh` | exit 0 → fuzzer + `.so` |
| 3 generate 200 | 0 errors; **194/200 distinct sizes**, most common twice (1%), min 8, median 1534, p95 15481, max 44931 |
| 4 round-trip `parse` | **200/200** |
| 5 gate | **no regression — the first measured attempt was the final one** |

**Coverage: 21.6% (2687/12424) → 38.1% (4735/12424), +16.5 points / +2048 lines / +78 functions.**
A strict function superset: there is no function the baseline reaches that this
template does not. The largest relative gain of all ten formats.

Gains are spread across the whole library, including the **write** side the
baseline never reaches because reaching it requires a file that survives a full
read: `pngwutil.c` 266→844, `pngrutil.c` 803→1324, `pngtest.c` 234→425,
`pngwrite.c` 144→276, `pngtrans.c` 6→49, `pngwtran.c` 0→18.

---

## Expressed

### Constraints

**All 15 Tier A entries.** The signature, both IHDR method bytes, the three
`PNG_COMPR_METHOD` bytes, the shared `fcTL`/`fdAT` sequence counter,
`PNG_CHUNK.length` (backpatched from the bytes actually emitted) and
`PNG_CHUNK.crc` — `Checksum(CHECKSUM_CRC32, pos_start, data_size)` moved above
the declaration so it can pin it.

**All 17 Tier B entries** with their complete `valid_values`.

### Dependencies — 29 of 31

- **#0–4, the bit-depth family**, use the prompt's forward-lookahead form:
  `color_type` sits one byte *after* `bits`, so it is drawn first by
  `ReadByte(FTell()+1, colorTypes)` and the depth branch follows.
- **#5, #6, #24** (PLTE/tRNS/hIST presence) are implemented by *building the
  chunk-type set* from the colour type, so an illegal chunk is never offered
  rather than filtered afterwards.
- **#10–17** (bKGD and sBIT lengths) fall out of the original's
  `switch (colorType)` unchanged.
- **#27**, frame confinement, is the sanctioned Tier C exception — see below.

### Structure

Signature and IHDR are a fixed head, IEND a fixed tail. The chunk loop is a
**four-phase state machine** (IHDR → pre-IDAT → IDAT run → post-IDAT) whose
`ReadBytes` set is the legal type list for the current phase, with the
preferred/possible split biasing toward the repeatable types. The IDAT run
splits one zlib stream across chunks at scanline boundaries, carrying the Adler
accumulator in file scope — a measured +11 to +27 lines over a single IDAT.

### `payload_wellformedness` — four emitters through one struct

All four route through a parameterised `PNG_ZLIB`: a zlib (RFC 1950) stream of
stored DEFLATE (RFC 1951) blocks, **one stored block per scanline**, which is
also why `zLen`/`zNlen` never need the 65535 split.

| field | codec | size derived from |
|---|---|---|
| `PNG_CHUNK.data` (IDAT) | zlib/deflate over filtered scanlines | `ceil(width × channels(color_type) × bits / 8)` per row over `height` rows, or the seven Adam7 passes when `interlace_method == 1` |
| `PNG_CHUNK_ZTXT.ztxtValChunkData` | zlib/deflate | `length − Strlen(keyword) − 2 − 11` |
| `PNG_CHUNK_ITXT.itxtValChunkData` | zlib/deflate when `itxtCompressionFlag == 1`, raw UTF-8 when 0 | the same identity minus the three strings and their NULs |
| `PNG_CHUNK_FDAT.frame_data` | zlib/deflate | `fcTL.height × (1 + ceil(fcTL.width × channels × bits / 8))` |

`PNG_CHUNK_SPLT.spltData` is a stride contract rather than a codec: 6-byte
entries at `sampleDepth` 8 and 10-byte at 16, so the array is rounded down to a
whole multiple of the size the depth selects.

**The prompt's all-zero recipe was deliberately not used, and the reason was
measured.** The closed-form Adler `((n % 65521) << 16) | 1` only works for
all-zero data, which forces filter type 0 on every scanline — so
`png_read_filter_row_sub/up/avg/paeth` never run. On a 120-file probe:

| payload | lines |
|---|---|
| filter 0 + all-zero data | 2517 |
| filters 0–4 + all-zero data | 2604 (+87) |
| filters 0–4 + random data | **2651 (+134)** |

`PNG_ZLIB` therefore accumulates Adler-32 a byte at a time
(`s1 = (s1+b) % 65521; s2 = (s2+s1) % 65521`) by reading each emitted byte back
out of the declared array. Two lines, and it buys back the whole content freedom
`content_is_free: true` grants.

### `diversity_axes` — all 16 confirmed

**Tier C, declared bare** (no value set, no `<min=>`, no `<max=>`):
`PNG_CHUNK_IHDR.width`, `.height`, `PNG_CHUNK_PLTE.plteChunkData`,
`PNG_CHUNK_FCTL.width`, `.height`, `PNG_CHUNK_ACTL.num_frames`,
`PNG_CHUNK_TEXT.data`, `PNG_CHUNK_PHYS.physPixelPerUnitX`.

**Tier B, complete set:** `PNG_CHUNK_IHDR.bits` (all five, split across the
three colour-type-conditioned branches), `.color_type` (all five, a bare enum
pinned by a guarded lookahead), `.interlace_method` (both), `CTYPE.cname` (bare —
the per-phase lookahead offers all 33 registered names),
`PNG_CHUNK_SPLT.sampleDepth` `{8,16}`, `PNG_CHUNK_ITXT.itxtCompressionFlag`
`{0,1}`.

`PNG_CHUNK_FCTL.x_offset`/`.y_offset` are the **only** Tier C fields carrying a
value set, and that is the sanctioned `dependencies` exception (#27, frame
confinement): they are derived *from* the free frame size, which is untouched.

A grep for `<min=`, `<max=`, `generation_range`, `practical` and `sensible`
returns **zero**.

---

## Not expressed

- **`preferred_value` on `string` fields** (tEXt/zTXt/iTXt/sPLT keywords).
  ffcompile rejects `string x = { "Title", … }` — value sets exist for numeric
  and `char` arrays only. Left bare, which generates free printable ASCII:
  satisfies the pattern's character class most of the time and reaches libpng's
  invalid-keyword branch otherwise.
- **Per-index value sets on a numeric array.**
  `uint16 btPngSignature[4] = { 0x8950, … }` builds the correct constructor but
  ffcompile *also* passes the set to `generate()`, which takes none, so the C++
  will not compile. Worked around with a guarded `ReadBytes` lookahead — strictly
  better, since the declaration stays byte-identical to the original.
- **Parsing a foreign PNG's compressed payloads.** The zlib framing bytes are
  pinned under `SetEvilBit(false)`, so a Huffman-coded IDAT/zTXt/iCCP will not
  parse. Inherent to the prompt's own `ZLIB_ZERO_STREAM` recipe.
- **`cardinality` and `mutually_exclusive`** (iCCP vs sRGB; the once-only
  ancillaries). ffcompile's `local` arrays grow with `+=` but cannot shrink, so a
  type set cannot be narrowed mid-file. Enforced only probabilistically by set
  weighting — and the duplicates that slip through are themselves libpng
  branches now covered.
- **`excluded_values: [0]` on width/height/num_frames.** A bare `uint32` cannot
  express "anything but 0" without a value set, so 0 stays reachable. It lands in
  libpng's "Invalid IHDR data" branch, which is worth having.
- **fdAT block splitting** — emitted as one stored block of exactly the right raw
  size rather than one per scanline. libpng 1.6 has no APNG support, so fdAT is
  an unknown chunk either way; the size derivation is honoured in full.
- **The 77 baseline-only lines** are all malformed-input error paths: CRC errors,
  unknown IHDR compression/filter methods, bad chunk-type names, invalid zlib
  window size. These are precisely what Tier A pinning removes. 77 given up to
  gain 2125.

## Notes

Against real `pngtest -m`: **90 PASS** (full read + write + re-read + compare)
and 110 failures spread over **35 distinct libpng diagnostics** — duplicate-chunk,
out-of-place, invalid-length and out-of-range paths across a dozen chunk
handlers.

210 combinations of colour type × depth × interlace × dimensions were verified to
decode in libpng before any template code was written.

Getting to exactly 1.50× cost the original's two-line `else if (…)` /
`PNG_CHUNK_X x;` dispatch pairs, now one line each. That is the only place
original code was reformatted, and the line limit required it.
