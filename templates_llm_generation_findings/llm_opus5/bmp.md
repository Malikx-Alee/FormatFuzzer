# BMP — `templates_originals/bmp-orig.bt` → `templates_llm/bmp-llm.bt`

Inputs: `templates_originals/bmp-orig.bt` and
`llm_learned_specification/llm_reterived_constraints_bmp-llm_opus5.json`.
`templates/bmp.bt` was not opened. The original is unmodified.

Diff shape: 138 → 375 lines, 18 removals / 255 additions. All 152 identifiers from
the original survive. The only structural removals are the 16 header field
declarations that gained an attribute or an init list on the same line, the
`rgbReserved` declaration that became a two-branch one, and the `if( padding != 0 )`
statement that became a block.

## Verification

| Command | Result |
|---|---|
| `./ffcompile templates_llm/bmp-llm.bt /tmp/bmp-llm-check.cpp` | exit 0, "Finished creating cpp generator" |
| `./build_new.sh bmp-llm` | exit 0 → `build/bmp-llm-fuzzer` (433,776 B), `build/bmp-llm.so` (433,720 B); 24 warnings, all `-Wparentheses-equality` |
| `./build/bmp-llm-fuzzer fuzz /tmp/bmp-llm-out/f{1..200}.bmp` | exit 0, 200/200 created, no failures |
| `./build/bmp-llm-fuzzer parse /tmp/bmp-llm-out/f1.bmp` | exit 0; 200/200 of the batch round-trips |
| `bash checkers/bmp.sh` | exit 0 on f1; **200/200 PASS**, and zero ImageMagick stderr on all 200 |

**Largest generated file: 14,390 bytes** — min 70, median 1,338, mean 2,569.
The theoretical ceiling is 16,438 (32 bpp, 64 × 64, no palette).

Beyond the required commands:

* **An independent BMP conformance walker finds 0 violations in the 200 files.** It
  recomputes every derived quantity from the specification: `bfSize` equals the
  real file length, `bfOffBits` equals `54 + 4 ×` palette entries, `biSize` is 40,
  `biPlanes` is 1, both reserved words are zero, `biClrUsed` is `1 << biBitCount`
  at palettised depths and 0 above them, `biClrImportant` is 0, `biSizeImage` is
  either the sentinel 0 or exactly `abs(biHeight) × (bytesPerLine + padding)`, the
  pixel region is exactly that many bytes with nothing trailing, every pad byte is
  zero, and every RLE stream decodes to exactly `biWidth × biHeight` pixels and
  ends with the end-of-bitmap marker `00 01`.

* **Parse parity is exact.** Over 140 real BMPs (`testcases/bmp`,
  `testcases_4_learn/bmp`, `coverage_targets`) and 300 sampled from
  `output/bmp*/…/valid/`, the rewrite accepts and rejects **the identical set** as a
  baseline built from the untouched original: 32/140 and 294/300, **0 files
  differing** in either direction. Of the 108 real files both reject, 102 are larger
  than FormatFuzzer's `MAX_FILE_SIZE` of 65,536 and 2 carry a DIB header size other
  than 40, which the original cannot parse either (template_deviations #0).

* **Census over 200 files:** all five generated bit depths (1 bpp ×15, 4 ×41,
  8 ×60, 24 ×43, 32 ×41); all three compression methods (BI_RGB ×165, BI_RLE8 ×18,
  BI_RLE4 ×17); 25 top-down and 175 bottom-up; all four row paddings
  (0 ×70, 1 ×29, 2 ×32, 3 ×34); 66 files using the `biSizeImage` sentinel and 134
  the exact byte count.

## What I implemented

### The problem this format poses

BMP has no markers at all. `meta.structure_note` puts it plainly: four regions
located purely by position, no terminator, and the file simply ends when the pixel
data does. That makes every constraint a *forward* one. `bfSize` at offset 2 is the
length of a file whose last byte does not exist yet; `bfOffBits` at offset 10 points
past a colour table whose size comes from `biBitCount` at offset 28; and `biWidth`
at offset 18 has to be chosen before `biCompression` at offset 30 has said whether
the pixel region is rows or an RLE stream.

The rewrite resolves all of it with one mechanism: **`bmpPlan()` plants the whole
54-byte header region through ffcompile's lookahead before any of it is emitted.**
A planted byte is copied back into the value on every write path in
`file_accessor.h` — including the evil-bit one — so each plant is exact during
generation. During parsing the same `ReadBytes` call only reads, and marks the
bitmap with whatever the file actually holds, so the field declarations keep the
original's parse behaviour unchanged. That is why parity is 0 files differing:
**not one `SetEvilBit(false)` and not one backpatch appears in this template.**

Six plants cover the header. Two of them carry values that have no small constant
set — `bfSize` and `bfOffBits`, and `biSizeImage` and `biClrUsed` — so they are
built at runtime by `bmpLE32()`, which sidesteps `SPrintf`'s truncation at the first
NUL by substituting a literal for the zero byte.

### Constraints

* **`bfType` (fixed_value, `evil_bit_safe: false`)** — planted as part of the
  18-byte offsets-0..17 image and declared `= { "BM" }`. The plant, not
  `SetEvilBit(false)`, is what makes it exact; the init list documents the rule and
  feeds the mutator.
* **`bfSize` (calculated_value, depends on bfOffBits / biSizeImage / biSize)** —
  computed as `bfOffBits + pixel byte count` and planted. Dependency 28 and
  structure rule 13 (nothing after the pixel data) hold by construction.
* **`bfReserved1` / `bfReserved2` (fixed_value 0)** — zero bytes inside the same
  plant, plus `= { 0 }` on each declaration.
* **`bfOffBits` (calculated_value)** — `54 + 4 ×` palette entries, planted.
  Dependency 27. The original never reads this field back
  (template_deviations #8), so a wrong value would have been invisible here and
  fatal to a real decoder, which seeks to it.
* **`biSize` (calculated_value, fixed_result 40)** — planted as 40 and declared
  `= { 40 }`. `valid_values_spec` lists eight header sizes, but the template reads
  the 40-byte layout whatever the field says, so 40 is the only self-consistent
  choice (dependency 29, template_deviations #0).
* **`biWidth` (range_constraint, generation_range 1–64)** — planted from a 64-entry
  menu and declared `<min=1, max=64>`. It is a signed `LONG` used as a raw array
  bound three times with no check (template_deviations #5), so leaving it free —
  even ranged — was not an option: the evil path escapes a `<min>/<max>` pair to a
  full 32-bit draw.
* **`biHeight` (range_constraint, sign-carrying)** — planted, magnitude 1–64.
* **`biPlanes` (fixed_value 1)** — the first two bytes of the depth/compression
  plant, plus `= { 1 }` (dependency 33).
* **`biBitCount` (enumerated_values, preferred 24)** — planted; see the pairs table
  below. 24 is weighted 3/11.
* **`biCompression` (enumerated_values, preferred 0)** — planted; BI_RGB weighted
  9/11.
* **`biSizeImage` (calculated_value)** — planted; see dependencies 11/12/26 below.
* **`biXPelsPerMeter` / `biYPelsPerMeter` (range_constraint 0–20000)** — the only
  two header fields left free, carrying `<min=0, max=20000>`. Nothing reads them
  and their corruption risk is low, so they keep a real 1-in-128 escape and are the
  format's cheapest source of genuine header variety.
* **`biClrUsed` (calculated_value)** — planted; see structure rule 5 below.
* **`biClrImportant` (calculated_value, preferred 0)** — planted as 0 in the same
  call, the sentinel meaning "all entries are important" (dependency 5).
* **`RGBQUAD.rgbReserved` (fixed_value 0)** — see dependencies 31/32.
* **`BITMAPLINE.padBytes` (fixed_value 0)** — planted per row.
* **`imageData` / `colorIndex` / `colors` / `aColors` / `rleData` / `lines`
  (calculated_value)** — all sized from the planted geometry; see the structure
  rules.

### Dependencies

The bit-depth/compression dependency cluster — 6, 7, 8, 9, 10 — is not expressed as
nested `if`s but as **a table of legal pairs**, planted as the eight bytes at
offsets 26..33 in one call:

```
local string bmpDepthComp[] = {
    "\x01\x00\x18\x00\x00\x00\x00\x00",   // 24 bpp, BI_RGB
    ...
    "\x01\x00\x08\x00\x01\x00\x00\x00",   //  8 bpp, BI_RLE8  (dependency 6)
    "\x01\x00\x04\x00\x02\x00\x00\x00" }; //  4 bpp, BI_RLE4  (dependency 7)
```

Every row is a combination the format actually defines; a combination that is not a
row cannot be generated. `biPlanes` rides along in the same eight bytes, which is
why dependency 33 needs no code of its own.

* **1, 2, 4 / structure 3, 4, 5 (colour table presence and size)** — `bmpClrUsed` is
  `1 << biBitCount` at 1, 4 and 8 bpp and 0 at 24 and 32, planted explicitly so the
  template's `1 << biBitCount` fallback at line 99 is never the thing that decides.
* **3 (`biClrUsed` ≤ `1 << biBitCount`)** — holds by equality.
* **5 (`biClrImportant` ≤ entry count)** — the sentinel 0.
* **11 (compressed ⇒ `biSizeImage` ≠ 0)** — the compressed branch always plants 16,
  the exact length of the fixed RLE stream, so the template's
  `bfSize - FTell()` fallback at line 110 is unreachable during generation
  (template_deviations #6).
* **12 and 26 (BI_RGB ⇒ `biSizeImage` is 0 or exactly the row geometry)** — the two
  are the only legal values, so the planner alternates between them on the parity of
  the height rather than drawing an independent third number.
* **13, 14 / structure 6 (rows and RLE stream are mutually exclusive)** — already the
  original's shape; the planner simply never produces a compression value that
  contradicts the branch it planned for.
* **15 and 16 (top-down ⇔ uncompressed)** — the negative-height menu is offered only
  when the planted compression is BI_RGB, so an RLE bitmap is never top-down and a
  top-down bitmap is never RLE.
* **17 / structure 11 (RLE stream shape)** — the payload is planted whole, not left
  as random bytes: four encoded runs, three closed by an end-of-line escape
  `00 00`, then the mandatory end-of-bitmap marker `00 01`. The geometry is pinned
  to 8 × 4 so the stream decodes to exactly `biWidth × biHeight` pixels.
* **19, 20, 21, 22 (which row layout each depth uses)** — the original's four-way
  chain, unchanged; the planted depth guarantees one of them is always taken.
* **23 (16 bpp has no `BITMAPLINE`)** — expressed as the absence of a 16-bpp row from
  the pairs table.
* **24 (every pixel index must address an entry that exists)** — solved
  structurally rather than by constraining pixel bytes: the **full** palette is
  always emitted, so at 1 bpp every bit, at 4 bpp every nibble and at 8 bpp every
  byte is a valid index. No pixel byte the generator can produce can overrun it.
* **25 (padding is a pure function of width and depth)** — the planner recomputes it
  with exactly the arithmetic the template uses at file scope.
* **27, 28, 29** — the three header-consistency rules, covered above.
* **30 (BI_BITFIELDS masks occupy the colour table's position)** — expressed by the
  absence of compression 3 from the pairs table.
* **31 and 32 (`rgbReserved` is reserved in the palette and alpha in a pixel)** — a
  `bmpInPalette` flag set to 1 before the colour table and 0 before the pixel
  region, selecting between `UBYTE rgbReserved = { 0 };` and a free
  `UBYTE rgbReserved;`. This is the one place the rewrite changes a struct body,
  and it is unavoidable: the rule follows the position, not the type
  (template_deviations #10).
* **33 (`biPlanes` is 1)**, **34 (`biWidth` ≥ 1)** — covered above.

### Structure rules

* **0, 1, 2 (fixed head, fixed order)** — already the original's shape; the planner
  makes the head's contents describe what follows.
* **3, 4, 5 (colour table)** — above.
* **6 (two-way union tagged by `biCompression`)** — above.
* **7 (`lines` cardinality)** — `abs(biHeight)`, bounded at 64 by the plant. The
  original's expression is untouched.
* **8 (pixels then padding, contiguous)** — the original's shape; the padding is now
  planted as zeros immediately before `padBytes` is declared.
* **9 (bottom-up row order)** — see below.
* **10 (`rleData` present iff compressed)** — sized from `biSizeImage`, never from
  the `bfSize - FTell()` fallback.
* **11 (RLE termination and pixel count)** — above.
* **12 (bit-field masks)** — its own `generation_note` says to avoid BI_BITFIELDS
  unless the masks are generated, and the template has no field for them, so
  compression 3 and 6 are excluded.
* **13 (no trailing bytes)** — `bfSize` is the measured total; the walker confirms
  the file ends with the last pixel byte in all 200.
* **14 (no terminator)** — nothing is emitted at the end.
* **15 (little-endian throughout)** — `LittleEndian()` kept; every planted literal is
  written low byte first.

## What I could not express, and why

* **A computed value cannot be planted directly.** `ReadBytes` needs a byte string
  and `SPrintf` assigns through `s = res`, which stops at the first NUL — so
  formatting a DWORD whose low byte is zero silently produces a shorter string.
  `bmpChr()` works around it by substituting the literal `"\x00"` for that one case,
  and `bmpLE32()` builds the four bytes by concatenation. Without this the length
  fields would have needed the backpatch idiom, which costs parse robustness on
  every real file whose `bfSize` disagrees with its own length.

* **ffcompile mines array value sets only from `==` comparisons.** An init list on a
  `UBYTE` array (`UBYTE padBytes[ padding ] = { 0 };`) compiles to
  `padBytes.generate(padding, { 0 })` and fails: the array class has no such
  overload, and `element_known_values` is populated in the generated *constructor*
  from mined comparisons, not from a declaration. `padBytes` therefore gets its
  fixed_value by being planted, in three branches for the three possible lengths.

* **`<min=>`/`<max=>` do not bound the evil path.** In
  `file_integer(size, bits, small)` the range branch calls `evil()` first and a
  positive result draws uniformly from the field's whole width. So `biWidth`,
  `biHeight`, `biClrUsed` and `biSizeImage` carry their generation ranges as
  documentation and for the mutator, but the plant is what actually bounds them.
  Leaving any of them to the attribute alone would have produced a multi-gigabyte
  file roughly once in 128.

* **16 bpp is not generated at all.** template_deviations #2 and #3 and dependency 23
  are unanimous: there is no pixel-row branch for it, so its rows would be pure
  padding, and it falls into the colour table branch where `1 << 16` allocates
  65,536 entries. Adding a two-byte-per-pixel branch would have meant a new field
  name and a new layout the original never had, so the deviation's other option —
  avoid the depth — is the one taken.

* **BI_BITFIELDS (3), BI_ALPHABITFIELDS (6), BI_JPEG (4) and BI_PNG (5) are not
  generated.** The first two need three or four DWORD channel masks between the DIB
  header and the colour table and the template has no field for them, so such a file
  would not round-trip through its own parser. The last two need a complete embedded
  JPEG or PNG datastream, which is a different format's generator.

* **A partial palette is not generated.** `biClrUsed` is always the full
  `1 << biBitCount`. A smaller table is legal and would be worth covering, but
  dependency 24 then requires every packed index to be below the entry count, and
  the only way to constrain the bytes of `UBYTE colorIndex[ biWidth ]` is the array
  mining described above — which reaches one element index at a time. Correctness
  won over that particular slice of coverage.

* **Structure rule 9 (bottom-up row order) is vacuous here.** Pixel content is
  uniformly random, so there is no image to store upside down. The sign of
  `biHeight` is generated and its consequences (dependencies 15 and 16) are
  enforced; the row *ordering* it selects has nothing to order.

* **The RLE geometry is fixed at 8 × 4.** The stream is a compile-time literal, and
  dependency 17 requires it to decode to exactly `biWidth × biHeight` pixels, so the
  two are pinned together. Generating a variable-length RLE stream would mean
  building it byte by byte at runtime, which `bmpLE32`'s machinery could do but which
  would need a new repeating structure the original does not have.

* **Two of `biXPelsPerMeter`'s `preferred_value` and the `biSizeImage` sentinel
  preference are only partly honoured.** The resolutions are left free inside their
  range rather than pinned to 2835, because they are the only unconstrained header
  bytes left and their corruption risk is low; `biSizeImage` alternates between the
  preferred 0 and the exact byte count instead of favouring 0, because dependency 26
  makes those the only two legal values and the exact one is the more informative.

## The one residual failure mode

`ReadBytes(…, preferred, preferred, 1.0)` is exact 255 times in 256; the remaining
1/256 re-rolls from the same set with the evil bit *restored*, which is a further
1/128 — about 1 in 32,768 per plant. That fallback is not a defect to be removed: it
is exactly what lets the parse direction stay tolerant, because with the evil bit
suppressed a parse of any file whose header bytes differ from the menu would assert.

Over a 3,000-file stress run the effect was measurable: **2,999/3,000 created and
2,999/3,000 accepted by ImageMagick.** One file lost the `biClrUsed` plant, asked for
a garbage-sized palette and was caught by FormatFuzzer's own
"Array length too large" guard — reported as `failed`, no crash and no large file.
One further file had a single non-zero pad byte, which decoders ignore. Merging the
header into six plants instead of fourteen roughly halved this rate; driving it to
zero would require `SetEvilBit(false)` around the lookahead, which would trade a
1-in-3,000 generation blemish for a wholesale loss of parse parity.

## Incidental finding

`checkers/bmp.sh` reads `out.bmp` from the working directory over stdin
(`identify -verbose - <out.bmp`) rather than taking a path argument, and passes when
ImageMagick prints an `Elapsed` line. It is a real decode test — ImageMagick rejects
a file whose `bfSize` disagrees with its length, which is how the one stressed
failure above was caught — but it says nothing about whether `bfOffBits` points where
the palette actually ends, or whether the pad bytes are zero. The independent walker
described above checks both.
