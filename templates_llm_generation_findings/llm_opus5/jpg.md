# JPG — generative template findings

| | |
|---|---|
| **Output** | `templates_llm/jpg-llm.bt` (2157 lines, from a 1631-line original; 718 changed lines) |
| **Inputs** | `templates_originals/jpg-orig.bt` + `llm_learned_specification/llm_reterived_constraints_jpg-llm_opus5.json` |
| **Model** | claude-opus-5 |
| **Spec** | ITU-T T.81 Annex B, JFIF/T.871, Exif 2.2, TIFF 6.0, Adobe TN5116, CIFF V1R04, T.87 |

References of the form `Dnn` / `Snn` point at the `dependencies` and `structure`
entries of the constraints JSON, and appear as comments in the template itself.
`templates_llm/jpg-llm.bt` did not exist before, so nothing was overwritten.

---

## Verification results

| Command | Result |
|---|---|
| `./ffcompile templates_llm/jpg-llm.bt /tmp/jpg-llm-check.cpp` | **exit 0**, `Finished creating cpp generator` |
| `./build_new.sh jpg-llm` | **exit 0** → `build/jpg-llm-fuzzer` (780,048 B), `build/jpg-llm.so` (779,992 B) |
| `./build/jpg-llm-fuzzer fuzz /tmp/jpg-llm-out/f{1..200}.jpg` | **exit 0**, 200/200 files, no assertion retries |
| `./build/jpg-llm-fuzzer parse /tmp/jpg-llm-out/f1.jpg` | **exit 0**; 198/200 of its own output round-trips |
| `bash checkers/jpg.sh` | **50/60 PASS** |

**Largest generated file: 19,761 bytes.** min 171 B · median 229 B · mean 423 B ·
only 2 of 200 files above 4 KB.

For comparison, the unmodified original generates 3–65 KB files (median 27 KB)
that are mostly `0xFF` filler and contain no JPEG structure at all, because
`JpegFileEnd = FileSize()` invents a random file length and pads to it before a
single byte is written.

### Validity

ImageMagick `identify` over the 200 generated files: **180 valid (90%)**.
Of the 20 failures, **15 are nibble-bitfield evil escapes** — see the second
design note below — 1 is a deliberate out-of-range image dimension that makes
ImageMagick allocate for several seconds, and 4 are a segment length that
disagrees with its own payload after an escape.

### Parse direction — no regression on real files

The original template was compiled as a baseline and both binaries were run over
**126 real JPEGs** (the repo's `testcases/jpg/`, plus macOS system and
application JPEGs under 64 KB):

```
n=126   original parses=122   llm parses=122   differences: none
```

The four both binaries reject are rejected identically by the original.

---

## What I implemented

**The marker loop became the ordering state machine of T.81 Annex B (S00–S08,
S21, S34).** The original walks `while(FTell() < JpegFileEnd && !bEOI)` with a
`switch` on `ReadUShort(FTell())`, which during generation is a uniformly random
word: it lands in `default:` almost every time and emits garbage. The rewrite
drives the walk through five phases — SOI, a bounded header run, DQT, DHT, one
frame header, then the scan — with a `ReadBytes` lookahead pinning the two
marker bytes before anything is written.

**Table dependencies are satisfied by construction (S05, S06, D17, D18).** The
phase machine emits a DQT and a DHT before the frame header, the DHT segment is
sized to hold exactly the DC/AC pair a baseline scan needs, and every selector —
`COMPS.compNr`, `COMPSOS.AC`, `COMPSOS.DC`, `QuanTable.Tq` — is 0. The tables a
scan references are therefore always the tables that were installed.

**Component identity is threaded, not guessed (D00, D01, D04, D05).** `SOFx`
publishes its component count and numbers its components 1..Nf through a shared
counter; `SOS` reads that count back and repeats the same identifiers. Both
segment lengths are then back-patched from the payload actually written, so
`8 + 3*Nf` and `6 + 2*Ns` hold exactly.

**Process-dependent scan parameters (D06–D08, D10, D12).** `SOFx` records which
marker introduced the frame, and `SOS` branches on it: sequential frames get
`Ss=0, Se=63, Ah=Al=0`, a lossless frame gets a predictor selector in 1..7 with
`Se=0`. Sample precision likewise depends on the SOF marker.

**Real quantization and Huffman tables.** The 16 code counts, the 16 symbols and
the 64 quantization coefficients are pinned through the bitmap (see the first
design note). The BITS array is sixteen counts of one symbol each, which T.81
B.2.4.2 guarantees is never over-subscribed — the running code after *n* lengths
is 2ⁿ − 2 and never reaches 2ⁿ. Every quantization coefficient is 65, inside
D15's 1–255 and non-zero, which matters because a decoder divides by them.

**Segment identifiers are steered, and the length follows from them.** APP0 is
pinned to `JFIF\0` and sized to 16 bytes with the thumbnail suppressed (D23,
D25, S09); APP1 to `Exif\0\0` with the 8-byte TIFF header, `tagMark` 42 and
`offsetFirstIFD` 8 (D34, S27, S10); APP14 to `Adobe` and 14 bytes. The
identifier lookahead sits at `FTell()+2` — *past* the length field — which is
what lets the length be derived from the shape the identifier selects rather
than guessed and then contradicted.

**Bounds.** Every length and count that drives an array or a loop got a
generation range: the ICC chunk counters (D47), the Photoshop resource name and
data (D52, D53, S31), the Ducky record length (D51), the CIFF size/offset pair
and directory count (S28, S29), the Exif component count (D35, D37), the JFXX
thumbnail dimensions (D30), and every `szSection`.

**Two real bugs in the original, fixed because they are also generation
hazards.** `local WORD qtsz` and `local WORD huffsz` are unsigned: one table
larger than the remaining count makes the subtraction wrap to 65472 and the loop
writes a further 64 KB of tables. Making them signed removed the last class of
oversized files and took the fuzz exit code to 0. The three self-recursion sites
(JFXX 0x10, the Exif thumbnail, the Casio MakerNote thumbnail) are capped at
depth 1 (S22).

**`FileSize()` was removed from the top-level parse.** During generation it
invents a random target length of up to 64 KB and pads to it immediately. The
top-level datastream now leaves `JpegFileEnd` at 0, meaning "not known in
advance"; a nested thumbnail still sets it to the computed end of its region,
and every use of it is guarded. The trailing bytes after EOI are consumed one at
a time against `FEof(0.99)` instead — exact when parsing, and on generation it
reports end-of-file 253 times in 256, so almost nothing trails the terminator
(S18).

---

## Two design decisions worth your attention

### 1. The bitmap-pin idiom, and why `possible` sets should be narrow

Three separate limitations pushed toward one technique. A native (non-char)
array cannot carry known values, because ffcompile emits no
`generate(size, values)` overload for one — so the 16-byte BITS array, the
16 HUFFVALs and the 64 quantization coefficients cannot be written as
`= { ... }`. And a field declared with a value list still takes a 1-in-128 evil
escape, which for a segment length that *drives a loop* is not a mislabelled
field but a desynchronised stream.

Both are solved the same way: a `ReadBytes` lookahead with `p=1.0` writes the
value into the bitmap first, and the declaration that follows is wrapped in
`SetEvilBit(false)`. This is exact in **both** directions, which is the part
worth knowing:

- **Generating** — the bitmap already holds a value from the set, so the
  compatible list is non-empty and the evil bit is never consulted.
- **Parsing** — a real file's value leaves *no* compatible candidate, and
  `file_integer` short-circuits on `match && compatible.empty()` and returns the
  raw value **without calling `evil()` at all**. No assertion, no escape needed.

The corollary took several iterations to see: **a wide `possible` set is a
generation hazard with no parse benefit.** A value outside `possible` resolves
through the evil escape anyway, so widening the set only gives the 1-in-256 draw
that reaches it a chance to write something legal-but-wrong — a DQT length of
134 that the table loop cannot decompose, an arithmetic-coded SOF9 in the middle
of a baseline stream, a second SOI. Narrowing `mkAny` to the markers that
actually occur between segments, and setting `possible = preferred` on every
length and selector pin, removed four distinct failure classes.

### 2. Nibble bitfields cannot be protected, and that is the entire residual

`file_integer` asserts `"bitfield lookahead not implemented"` the moment the
bitmap covers a bitfield, so the pin above cannot be applied to
`QuanTable.Pq`/`Tq`, `COMPSOS.AC`/`DC`, `COMPS.Horz`/`Vert` or `SOS.Ah`/`Al`.
`SetEvilBit(false)` alone is not an option either: without a bitmap there is no
compatible-empty short-circuit, so parsing any real file whose sampling factor
is 2 would hit the assertion.

Each such field therefore keeps a 1-in-128 escape, and a generated file carries
8 to 14 of them — 2 for the quantization selectors, 2 per scan component for the
entropy selectors, 2 per frame component for the sampling factors, 2 for
successive approximation. That is a per-file failure probability of roughly
6–10%, and it accounts for **15 of the 20 invalid files**: "Bogus sampling
factors", "Bogus DQT index", "Huffman table 0x0N was not defined". Every one is
a single wrong nibble.

Where a field *is* a plain byte the pin was applied and the class disappeared:
the JFIF version pair (which meant declaring `short versionHigh:8` as the plain
byte it already is on disk), `htInfo`, `compId` in both the frame and the scan,
`precision`, and both component counts. Each of those was a measurable 2–3% of
files before it was pinned.

---

## What I could not express

**pfp's lexer is exponential in escape sequences per string literal.** Sixteen
`\xNN` escapes parse instantly, twenty-four take 18 seconds, twenty-eight never
finish. This is a property of the toolchain, not of JPEG, and it is worth
recording: it silently caps how much fixed binary content a template can pin.
The 64-byte quantization constant is written as printable characters (`'A'` =
65, a legal coefficient) for exactly this reason; a 64-character literal with no
escapes parses in 0.2 seconds.

**Real entropy-coded data.** The scan is a short printable-ASCII run — which
does satisfy D22 and S35 in the cheapest possible way, since a printable byte is
never `0xFF` and so nothing inside the scan can be mistaken for a marker — but
it is not Huffman-coded output. Consequently D21 and S16 (restart markers every
`Ri` MCUs) are honoured by pinning `DRI.Ri` to 0 rather than by synthesising
`RSTn` markers, and D11 (the progressive scan sequence, with each scan's `Ah`
matching the previous scan's `Al`) is expressed in `SOS` but never generated —
SOF2 is deliberately absent from the frame-marker set, because one scan cannot
satisfy it.

**The scan length is set by `FindFirst`, which has its own evil path.** In the
generation direction `FindFirst` plants the EOI 0–15 bytes ahead; with
probability 1/128 it instead widens the search to the whole address space and
plants it up to 64 KB away, padding the file on the way. That is the sole
remaining source of oversized output (2 files in 200). Wrapping the call in
`SetEvilBit(false)` fixes generation and breaks parsing of *every* real JPEG,
whose EOI is always more than 16 bytes ahead. Replacing `FindFirst` with a
per-byte terminator peek was also rejected: it would consume one evil decision
per scan byte, and a 60 KB scan would exhaust `MAX_RAND_SIZE` and fail the parse
outright. The four-byte scan lead in front of it is likewise a compromise — 32
bytes suits generation far better, but a solid-colour JPEG can have an
entropy-coded segment only seven bytes long, and reading past it fails the parse.

**The Exif directory is generated empty** (`nDirEntry = 0`, `nextIFDoffset = 0`).
That satisfies S24, S26 and S27 exactly, but entries with out-of-line values need
offset arithmetic against the TIFF base and seeks that would require generating
the value area before the directory that points into it. D38, D42, D43, D44 and
D46 are implemented as parse-side constraints only; D39 and D65 (the GPS and
Casio tag vocabularies, which switch the meaning of the same 16-bit field) are
reachable only when parsing a file that already contains them.

**CIFF is parse-only** (D31, D55–D59, S28, S29). The branch is guarded by two
literals at two different offsets simultaneously — `"II"`/`"MM"` at the segment
start *and* `"HEAPJPGM"` six bytes later — and the directory cannot be located
at all until a size field is read from the last four bytes of the region.
Generating one would need a three-pass layout. Its field bounds are implemented,
so a malformed CIFF block cannot make the parser allocate without limit.

**D48** (the concatenation of all ICC APP2 payloads forming one valid profile)
is honoured by emitting exactly one chunk of one, which is the only shape a
single segment can be self-consistent in; a real multi-chunk profile parses.

**One pfp limitation forced a structural compromise:** a second array named
`unknown` in the same `switch` makes the interpreter fail with an `IndexError`
in its `dest_type` metadata stack, so the JFXX depth cap guards only the
recursion and not the byte consumption that would replace it.

---

## Incidental finding: the checker under-reports

As with PNG, `checkers/jpg.sh` uses plain `grep -q Elapsed`, and
`identify -verbose` echoes segment bytes verbatim. A valid JPEG whose APPn
payload contains non-UTF-8 bytes makes grep treat the whole output as binary and
report failure. `grep -a` fixes it. This is why the checker reports 50/60 (83%)
where a byte-exact search over the same build reports 90%.
