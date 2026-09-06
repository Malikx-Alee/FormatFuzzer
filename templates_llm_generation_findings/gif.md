# GIF — `templates_originals/gif-orig.bt` → `templates_llm/gif-llm.bt`

Generative rewrite of the 010 Editor GIF template for FormatFuzzer, driven by
`llm_learned_specification/llm_reterived_constraints_gif-llm_opus5.json`
(57 constraints, 34 dependencies, 20 structure rules, 9 template deviations).

Inputs were exactly the two files named above. `templates/gif.bt` was not read;
`templates_originals/gif-orig.bt` is unmodified (`git diff --quiet` confirms it).

204 lines in, 664 out. The diff is 49 removals and 495 additions: every removal is
a field declaration replaced by the same declaration carrying a value set, and all
93 struct/field identifiers of the original are still present.

---

## Verification results

| Command | Result |
|---|---|
| `./ffcompile templates_llm/gif-llm.bt /tmp/gif-llm-check.cpp` | **exit 0**, "Finished creating cpp generator" |
| `./build_new.sh gif-llm` | **exit 0** → `build/gif-llm-fuzzer` (507 KB), `build/gif-llm.so` (507 KB); 22 warnings, all `-Wparentheses-equality` from ffcompile's own output |
| `./build/gif-llm-fuzzer fuzz /tmp/gif-llm-out/f{1..200}.gif` | **exit 0**, 200/200 files |
| `./build/gif-llm-fuzzer parse /tmp/gif-llm-out/f1.gif` | **exit 0**; **200/200** of its own output round-trips |
| `bash checkers/gif.sh` over all 200 | **200/200 PASS** |

**Largest generated file: 2131 bytes** — min 209, median 883, mean 965. Nothing
approaches the "few hundred KB" threshold: the file is bounded by construction at
768 (global table) + 3 × (10 + 768 + 68) + a handful of extensions.

Beyond the required commands:

* **ImageMagick: 200/200 valid, and zero warnings on stderr across all 200 files.**
  `checkers/gif.sh` only greps `identify -verbose` for `Elapsed`, which a file with
  an out-of-range colormap index still passes; the stronger stderr-empty check is
  what says the files are actually clean.
* **426 / 426 generated images carry an LZW code stream whose literal count is
  exactly `ImageWidth × ImageHeight`.** Every image in every file decodes.
* **Real-file parse parity: 368 real GIFs, original parses 253, rewrite parses
  253, zero differences** (the original was compiled as a baseline for this). Of the 115 both reject, 111 exceed `MAX_FILE_SIZE`
  (65536) and 4 carry bytes after the trailer, which `finish()` rejects in both.
* Feature census over the 200 files: all eight global-table exponents (0–7)
  appear; both versions appear (148 × `89a`, 52 × `87a`); all five block branches
  appear (426 images, 44 Graphic Control, 39 Comment, 28 Plain Text, 16
  Application, 30 undefined-label); 2–7 blocks and 1–3 frames per file; 348 local
  colour tables; trailer present and final in 200/200; zero desynchronisation.

---

## What I implemented

### The block state machine (S06, S07, S10, S11, S14–S19, D24, D26, D32, D33, DEV03)

The original's `while (ReadUByte(FTell()) != 0x3B)` has no value set and no
end-of-file guard, so generating it writes a random introducer at every block
boundary and only stops when it randomly rolls `0x3B`. It is now a menu that
`gifNextBlockMenu()` recomputes after every block:

* the trailer is off the menu until at least one Table-Based Image exists and at
  least two data blocks have been written (S07 + S06's lower bound);
* once 8 blocks or 3 images have been written, `0x3B` is the *only* thing on the
  menu — that is what makes the loop terminate;
* after a Graphic Control Extension the menu is `{0x2C}` alone, which is D26/S10
  ("its scope is exactly the graphic-rendering block that follows it") expressed
  as a branch rather than a check;
* an `87a` header removes every extension from the menu (S16, D11–D14).

The extension label menu is grown the same way: comments are always legal (S15),
a Graphic Control Extension only while an image can still follow (S11), NETSCAPE
only ahead of the first image (S14), Plain Text only when a Global Color Table
exists (S17/D24), and the undefined-label branch at most once (S18).

### The LZW code stream (D19, D28, DEV07)

The template says nothing about sub-block contents — `char Data[size]` is all
five chains, so the LZW structure had to come from GIF89a Appendix F. The
generated stream is the Clear code, one literal code per pixel, then
End-of-Information. Setting `LZWMinimumCodeSize` to 7 makes every code exactly
8 bits, so the whole stream is byte-aligned and can be written as a plain string
literal; the literals are drawn from `0x20`–`0x3F` so the payload is printable
and needs no escape sequences. `ImageWidth` and `ImageHeight` are restricted to
powers of two up to 8 so the pixel count is always one of the seven the payloads
cover, and the payload is selected from the geometry actually generated.

### The two colour tables (D00–D08, D18, S02, S03, S09)

The doubling loops that turn the 3-bit exponent into an entry count are already
the calculated_value and needed no change. What is new is the dependency: an
image resolves against the Global Color Table only when that table holds at least
64 entries (the largest index the code stream uses); otherwise the image is forced
to carry a local table, whose exponent is then constrained to 5–7. That is D08
("an image with neither table is undecodable") and D18 ("the code width must
cover every index of the active table") as one rule, and it is why 319 of the 411
generated images carry a local table.

### Fields, one by one

Every `fixed_value` is pinned (signature, the three introducer bytes, the three
block sizes 4 / 12 / 11, both terminators). Every `enumerated_values` entry became
a value set on its declaration, with `preferred_value` expressed as a repeated
entry — `{ "89a", "89a", "89a", "87a" }` is a 3:1 weighting, since the list is
sampled uniformly. Every `range_constraint` uses its `generation_range`, not its
spec bound: the canvas is 8–64 rather than 0–65535 (a decoder allocates
`Width × Height` the moment it reads the descriptor), `DelayTime` is 0–100 rather
than 0–65535 (the unit is 1/100 s, so the spec maximum stalls a player for eleven
minutes), and every colour index is 0 or 1 because the active table may hold as
few as two entries.

D25 is implemented as a real dependency rather than a constant: the application
identifier is drawn from `{ NETSCAPE, ANIMEXTS }` and the authentication code
branches on what was drawn, so the pair can never disagree.

---

## Two design decisions worth your attention

### 1. The lookahead bitmap beats the evil bit, and that is what makes a pin exact

`file_integer` consults `evil()` on every field, so a value set alone is only
127/128 reliable — fine for a colour sample, fatal for a block introducer. But
`file_integer(size, bits)` ends with

```c
if (has_bitmap) { ... p[index] = file_buffer[file_pos + i]; }
```

so a byte already planted by a lookahead is copied back **even on the evil path**.
`ReadBytes(peek, pos, n, pref, pref, 1.0)` plants with the evil bit switched off
255 times out of 256, and the 1-in-256 fallback re-rolls from the same set, so the
compound error rate is about 1 in 32768. Parsing is untouched: a real file whose
bytes differ leaves no compatible candidate and `file_integer` short-circuits on
`(match && compatible.empty())` *before* `evil()` is ever called.

Measuring this mattered more than reasoning about it. The first working version
scored 192/200 with a plain value set on the header, the geometry and the
sub-block size byte. Pinning those three took it to 200/200 with zero ImageMagick
warnings, and the failures it removed were exactly the ones the arithmetic
predicts: 4 corrupted version strings, 4 dimension escapes, and — after the block
bound was raised — 3 corrupted sub-block size bytes, each of which cost a whole
frame.

### 2. Byte-aligning the LZW stream is what made a real one expressible at all

pfp's lexer is exponential in the number of escape sequences in a single string
literal (measured on JPG: 16 escapes instant, 24 take 18 s, 28 never finish), so a
binary blob cannot simply be written down. Choosing `LZWMinimumCodeSize = 7` sets
the code width to 8 bits, which makes the stream byte-aligned; choosing literal
codes in `0x20`–`0x3F` makes every one of those bytes printable. The 66-byte
payload for an 8×8 image is then a literal with **two** escapes — the Clear and
End-of-Information codes at its ends — and compiles instantly.

The cost is the coupling this creates: the code width fixes the alphabet, the
alphabet fixes the minimum palette size, and the palette size is what forces most
images onto a local colour table (348 of the 426 generated here). It is a genuine
constraint of the format (D18 states it), not an artefact — but it is why
`SizeOfLocalColorTable` generates only 5, 6 and 7 while `SizeOfGlobalColorTable`
generates the full 0–7 range.

---

## What I could not express

**Bitfields cannot be lookahead-pinned.** `file_integer` asserts
`"bitfield lookahead not implemented"` the moment the bitmap covers a bitfield, so
the three packed-fields bytes keep a 1-in-128 evil escape per member. This is the
entire residual error in the output: 4 of 348 local colour tables came out with an
exponent below 5 (1.1%, matching 1/128), which is an out-of-range colour index
rather than a broken file. Every pin in the template is placed to avoid a
bitfield: the Graphic Control pin covers offsets +4…+7 and skips the packed byte
at +3, the image geometry pin covers +5…+8 and stops before the packed byte at +9.

**A wrong `possible` set is a pure generation hazard.** The peeks that resolve the
dispatch chain (`ReadUShort(FTell(), gifLblGce)` and the three after it) keep
narrow, single-value sets. A wide set would not help parsing — anything outside it
resolves through the evil escape anyway — but it would let generation plant a
label the branch it selects does not expect.

**The interlaced row order (D28) is expressed but never exercised.** Interlacing
changes the order rows are delivered in, not the number of indices in the stream,
so the same payload is correct either way; `InterlaceFlag` is nonetheless pinned
to 0, because a four-pass image is harder for a checker to reason about and adds
no structural coverage.

**Three constraints are honoured by suppression rather than by construction.**
`SortFlag` (D29) claims the colour table is ordered by decreasing importance,
which a randomly generated table will not satisfy; `TransparentColorFlag` (D09)
makes `TransparentColorIndex` load-bearing against a table whose length the
generator does not track; and `PixelAspectRatio` (D30) is interpreted through
`(n + 15) / 64`. All three are generated as 0 — the value that makes the
constraint vacuous — rather than being satisfied.

**The NETSCAPE loop count is fixed at 0** (loop forever). D25 permits any
little-endian ushort there, but the payload is pinned as a single three-byte
string, and varying the count would mean one string literal per value.

**Trailing-byte tolerance (S05) is inherited, not fixed.** Four of the 368 real
GIFs carry bytes after the `0x3B` trailer; `finish()` asserts
`file_size == final_file_size`, so both the original template and this rewrite
reject them. The rewrite is not worse here, but the rule "a conforming GIF ends at
the trailer" is enforced by the runtime rather than by anything in the template,
and there is no `FEof`-style construct that would let the parse consume a trailer
plus slack.

---

## Incidental finding

`checkers/gif.sh` is `identify -verbose - <out.gif | grep -q Elapsed`, which
passes as long as ImageMagick produces output at all. A GIF whose pixel indices
exceed its colour table prints `invalid colormap index` on stderr and still
passes. Judging validity by an empty stderr is strictly stronger, and is what the
200/200 figure above is measured against; on this output the two agree, but they
would not on a template that got the palette sizing wrong.
