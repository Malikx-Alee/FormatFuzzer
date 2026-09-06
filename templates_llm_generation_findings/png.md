# PNG — generative template findings

| | |
|---|---|
| **Output** | `templates_llm/png-llm.bt` (949 lines, from a 388-line original) |
| **Inputs** | `templates_originals/png-orig.bt` + `llm_learned_specification/llm_reterived_constraints_png-llm_opus5.json` |
| **Model** | claude-opus-5 |
| **Spec** | PNG 1.2, APNG 1.0, RFC 1950/1951, CRC-32/ISO-HDLC |

References of the form `Dnn` / `Snn` point at the `dependencies` and `structure`
entries of the constraints JSON, and appear as comments in the template itself.

> **Provenance note.** `templates_llm/png-llm.bt` already existed as a committed
> file (18,131 bytes, commit `de56181`). The task named that exact path as the
> destination, so it was overwritten. The prior version is recoverable with
> `git show HEAD:templates_llm/png-llm.bt`. It was never read, so the
> independence requirement holds.

---

## Verification results

| Command | Result |
|---|---|
| `./ffcompile templates_llm/png-llm.bt /tmp/png-llm-check.cpp` | **exit 0**, `Finished creating cpp generator` |
| `./build_new.sh png-llm` | **exit 0** → `build/png-llm-fuzzer` (532,992 B), `build/png-llm.so` (532,936 B) |
| `./build/png-llm-fuzzer fuzz /tmp/png-llm-out/f{1..200}.png` | **exit 0**, 200/200 files, no assertion retries (stable across 3 runs) |
| `./build/png-llm-fuzzer parse /tmp/png-llm-out/f1.png` | **exit 0** — and 200/200 of its own output round-trips |
| `bash checkers/png.sh` | **58/60 PASS** (96.7%) |

The four `*ERROR:` / `*WARNING:` lines `ffcompile` prints are the template's own
`error_message()` calls firing against empty dummy input, as expected. All
parser-side validation from the original is retained.

**Largest generated file: 25,363 bytes.** min 101 B · median 1,498 B · mean 3,121 B.

### Parse direction — no regression on real files

The original template was compiled as a baseline and both binaries were run over
**234 real PNGs** (the repo's `testcases/png/`, `docs/assets/`, and macOS system
PNGs under 64 KB):

```
n=234   original parses=234   llm parses=234   differences: none
```

### Validity and coverage over the 200 generated files

```
valid = 193/200 (96.5%)
  invalid because the evil bit landed on an IHDR field = 7
  invalid for any other reason                         = 0

colour types : {0: 44, 2: 35, 3: 39, 4: 47, 6: 35}          all five
bit depths   : {1: 14, 2: 22, 4: 18, 8: 77, 16: 69}         all five
interlace    : {0: 90, 1: 107, +3 evil}                     both methods
chunks/file  : 3–15
chunk types  : IHDR 200, IDAT 201, IEND 200, zTXt 70, iTXt 67, fcTL 66,
               fdAT 66, tEXt 62, PLTE 52, sRGB 37, sBIT 32, gAMA 32,
               tIME 31, cHRM 28, acTL 27, bKGD 26, pHYs 24, sPLT 21,
               tRNS 3, hIST 1                               20 of 21 registered
```

The 107 interlaced files are the meaningful number here: they confirm the Adam7
pass-geometry arithmetic (D52) produces a decompressed stream of exactly the
right length, since ImageMagick accepts them.

---

## What I implemented

**Signature (S00).** `uint16 btPngSignature[4]` became
`char btPngSignature[8] = { "\x89PNG\r\n\x1a\n" }` — the same eight bytes and the
same identifier. `ffcompile` emits no `generate(size, values)` overload for a
non-char array, so a `uint16[4]` initialiser compiles under `ffcompile` but not
under `g++`; the char form is the only way to pin it. Bracketed by
`SetEvilBit(false)`, and the signature check became a `Memcmp`.

**IHDR bit-depth / colour-type coupling (D00–D04).** The textbook forward-lookahead
case: `bits` is written *before* `color_type`, so the template reads the upcoming
colour-type byte with `ReadByte(FTell() + 1, pngColorTypeValues)` and selects the
legal depth set from it. Without this, four draws in five are an illegal pair.

**Chunk lengths (D21–D34).** A chunk-type lookahead at `FTell() + 4` pins the type
before the length field is written, so all fourteen "when the type is X, length
must be Y" rules are applied up front — including the ones derived from state:
`sBIT`/`bKGD` from the colour type, `PLTE`/`hIST`/`tRNS` from the palette size,
`IDAT` from the image geometry.

**Length and CRC back-patching (S26).** Payload first, then rewrite `length` with
what was actually written, then `Checksum(CHECKSUM_CRC32, pos_start, data_size)`
into `crc`. Both wrapped in `SetEvilBit(false)`. The original computed the CRC
*after* reading the field; generation needs it before.

**A genuinely valid IDAT (D35, D52, S03).** The one substantial addition:
`PNG_ZLIB_ZERO_STREAM`, a real zlib datastream — `78 01`, one stored DEFLATE block
of zero bytes, Adler-32 trailer. Zero data is what makes this expressible at all:
`Checksum()` implements no `CHECKSUM_ADLER32`, but the Adler-32 of *n* zero bytes
is exactly `(n << 16) | 1`, because `s1` never leaves 1 and `s2` accumulates 1 per
byte. Filter type 0 plus zero samples decodes to a black image.
`png_raw_length()` computes the decompressed size, including the seven Adam7
passes for D52, so interlaced files are valid too.

**At-most-one-of-each (S14).** The optional chunks are split into three disjoint
groups offered exactly once each, in spec order, with the group counter carrying
across the PLTE boundary. That makes S14 exact rather than probabilistic, and
yields S11 (colour-space chunks before PLTE) and S12 (bKGD/hIST/tRNS after it)
for free.

**Numeric ranges.** Every `range_constraint` with a `generation_range` uses the
generation bound in the attribute and carries the true spec bound in a trailing
comment: `width`/`height` `<min=1, max=64>` (spec 2³¹−1), `PNG_POINT` `<max=100000>`,
`pHYs` `<max=20000>`, the six `tIME` fields to real calendar ranges, `sBIT` to
1..8, `bKGD` samples to 0..255.

**APNG (D40–D47, S20–S23).** `acTL.num_frames` is drawn from `{1,2,3,4}` first and
the state machine then emits exactly that many `fcTL`/`fdAT` pairs, so D46's
count identity holds by construction. Sequence numbers come from one shared
counter (S21). Frame rectangles are the canvas clipped to 8×8 at offset 0, which
satisfies D45 containment unconditionally and keeps each frame's payload small.

**The main loop.** `while(!FEof())` became a six-phase state machine over
`preferred`/`possible` value sets (S01–S25), replacing a passive scan with the
format's actual grammar. What bounds the chunk count is the three-group walk, not
the loop guard — once the groups are spent, only the phase-advancing chunk is on
offer, so the stream runs to IEND in a handful of steps.

---

## Two design decisions worth your attention

### 1. `p = 1.0` on the chunk-type lookaheads

`CTYPE.cname` is `evil_bit_safe: false`, and the brief says markers always get
`SetEvilBit(false)`. But disabling the evil bit outright breaks parsing of any
real PNG carrying a chunk the state machine does not expect at that point — a
second `IDAT`, an `iCCP`, a vendor chunk like `iDOT`.

`ReadBytes()` resolves this on its own: it disables the evil bit for its
*preferred* set and restores it for its *possible* set. Passing the phase's list
as `preferred`, the full registered list (`pngAny`) as `possible`, and `p = 1.0`
buys both properties at once — generation draws a registered type from the
phase's list 255 times in 256 with no evil escape at all, while the parse
direction still resolves anything a real file carries.

The same gate selects the structured-IDAT branch: a three-byte lookahead for the
stored-block header `78 01 01`. On generation it proposes that value and the
structured stream is written; on parsing, a real dynamic-Huffman IDAT does not
match and falls through to the generic byte array exactly as in the original.
This measurably mattered — before the `p = 1.0` change, ~3% of files carried a
garbage four-byte chunk type, and libpng rejects an unknown *critical* chunk.

### 2. Which fields keep the evil bit

`compr_method` and `filter_method` are pinned with `SetEvilBit(false)`: they are
`fixed_value` with `corruption_risk: high`, PNG defines exactly one of each, and
a decoder rejects the whole IHDR on any other value.

`width`, `height`, `bits` and `interlace_method` are **not** pinned — the JSON
marks all four `evil_bit_safe: true`, and an out-of-range dimension is a
genuinely interesting input. That choice accounts for **all 7 invalid files** in
the 200-file run. The non-evil defect rate is 0/200.

The evil bit is contained rather than removed: `png_w`, `png_h`, `png_bits` and
`png_interlace` are clamped before the IDAT payload length is computed from them,
so a single evil draw cannot ask for a multi-gigabyte array. The file stays small
and merely declares a dimension its image data does not match.

`PNG_CHUNK.length` is a third case, split by whether a real file would agree:
lengths that are spec constants or fixed by the colour type (IHDR, IEND, cHRM,
gAMA, sRGB, tIME, pHYs, acTL, fcTL, sBIT, bKGD, and IDAT once the zlib lookahead
has matched) are pinned; `PLTE`, `tRNS`, `hIST` and `fdAT` are derived from *this*
file's state and would need an evil decision to parse someone else's file, so
they keep the escape.

---

## What I could not express

**Known values on `string` fields.** `ffcompile` emits `std::string generate()`
with no `possible_values` overload, so the registered keyword lists for
`PNG_CHUNK_TEXT.label`, `itxtIdChunkData`, `ztxtIdChunkData` and `paletteName`
cannot be declared. They fall back to the runtime's own generator, which is
bounded (≤80 characters) but unconstrained in content. The keyword pattern
constraints — printable Latin-1, no leading or trailing space, no two consecutive
spaces — are therefore unenforced.

**zlib payloads for zTXt and iTXt (D36).** A zlib stream necessarily contains NUL
bytes, and char-array known values are built from NUL-terminated C strings, so
the 11-byte empty stream is unrepresentable there. `itxtCompressionFlag` is
pinned to `{ 0 }`, which selects D37 (raw UTF-8) instead — the branch the
generator actually satisfies. zTXt payloads remain opaque bytes, which is the one
recurring source of a non-fatal `zTXt: truncated` warning.

**tRNS content for greyscale and truecolour (D34).** Its payload is a sample that
must stay below 2^bit_depth, which the generic `ubyte data[length]` path cannot
honour. tRNS is offered only for indexed images, where every payload byte is a
legal alpha value. The *length* rule (D34) is still implemented for all colour
types.

**iCCP** appears only in the parse-tolerance set, never generated. D51/S18 make it
mutually exclusive with sRGB, and the original has no iCCP branch — the JSON flags
`PNG_ICCP_CHUNK_DATA` as dead code whose second field, named `red`, is really the
compression-method byte.

**D44** (an fcTL preceding the first IDAT must cover the whole canvas and blend
with SOURCE) is unreachable by construction: S23's own `generation_note`
recommends keeping every fcTL after the IDAT run, which this template does, so
the default image is never an animation frame.

**Multiple IDATs (S03/S04 cardinality 1–3).** One IDAT carries the complete zlib
stream, which is what S03's `generation_note` recommends; splitting a stored
block across chunk boundaries while keeping a single valid stream is not
expressible here. The parse direction still handles multi-IDAT files, which is
what the 234-file real-PNG comparison confirms.

---

## Incidental finding: the checker under-reports

`checkers/png.sh` uses plain `grep -q Elapsed`, and `identify -verbose` echoes
text-chunk bytes verbatim. A **valid** PNG whose tEXt payload contains non-UTF-8
bytes makes grep treat the whole output as binary and report failure. `grep -a`
fixes it. This is worth knowing before comparing checker pass rates across
formats — it penalises any format that embeds free-form text.
