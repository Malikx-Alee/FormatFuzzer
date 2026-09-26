# JPG — tiered generative template findings

| | |
|---|---|
| **Output** | `templates_llm/llm_opus5-tiered/jpg-llm.bt` — **2194 lines** from a 1631-line original, **1.3452×** (limit 2446 — the only format with real headroom) |
| **Inputs** | `templates_originals/jpg-orig.bt` + `llm_reterived_constraints_jpg-llm_opus5-tiered.json` |
| **JSON** | 171 constraints (A 77 / B 32 / C 62), 35 dependencies, 22 structure rules, 33 diversity axes |
| **Target** | libjpeg-turbo 3.2.0, `djpeg-static` |

## Verification

| step | result |
|---|---|
| 1 `ffcompile` | exit 0 |
| 2 `build_new.sh` | exit 0 |
| 3 generate 200 | **0 generation errors**; 147 distinct sizes, min 292, p25 431, median 492, p75 785, p95 2203, max 58000 |
| 4 round-trip `parse` | **200/200** |
| 5 gate | **no measured run regressed** |

**Coverage: 14.2% (2580/18178) → 23.6% (4282/18178), +9.4 points / +1702 lines /
+71 functions.** 1733 mine-only against 31 baseline-only. (The 14.3% on record
was a 10,000-file run; re-run at the prescribed 2000 the baseline is 14.2%.)

**Five decoders the baseline never enters at all:**

| file | base | mine | of |
|---|---|---|---|
| `jdarith.c` (arithmetic) | 0 | **319** | 418 |
| `jdphuff.c` (progressive) | 0 | **157** | 319 |
| `jddiffct.c` (lossless) | 0 | **141** | 168 |
| `jdlhuff.c` (lossless Huffman) | 0 | **79** | 90 |
| `jdlossls.c` | 0 | **60** | 78 |
| `jdcoefct.c` | 208 | 511 | 563 |
| `jdsample.c` | 72 | 248 | 257 |
| `jdmainct.c` | 49 | 171 | 185 |

The mass of the size histogram sits low because `X_image`/`Y_image` are bare and
FormatFuzzer's bare-integer draw is `1 + rand_int(16)` 87.5% of the time — tiny
images with tiny scans, with a long free tail.

---

## What was measured first

An lcov probe and a byte-level JPEG constructor were built before any template
code. The headline finding: **one correct 153-byte JPEG is worth 1804 lines —
70% of what the entire 2000-file baseline reaches.** For this format validity is
not a means to coverage, it very nearly *is* the coverage.

Measured against that reference, one file each:

| change | Δ lines | where |
|---|---|---|
| SOF2 progressive, DC-only scan | **+550** | `jdcoefct` 326, `jdphuff` 104 |
| …at 12-bit precision | **+668** | |
| SOF2 non-interleaved | +395 | |
| SOF3 lossless (precision 16) | **+375** | `jddiffct` 86, `jdlhuff` 73, `jdlossls` 31 |
| non-interleaved sequential scan | +252 | `jdcoefct` 118 |
| arithmetic SOF + DAC | **+247** | `jdarith` 132 |
| 2×2 sampling at 64×64 | +186 | `jdmainct` 118, `jdsample` 45 |
| omitting the DHT entirely | +145 | `jidctint` 100 |
| 12-bit precision | +118 | |
| APP14 Adobe transform | +71 | `jdcolor` 27 |
| 4 components (CMYK) | +70 | |
| random scan bytes | +49 | `jerror` 33 |
| APP0 JFIF | +44 | |
| no EOI | +37 | `jerror` 27, `jdatasrc` 6 |

The JSON is right that the arithmetic frame headers are reachable *only* through
the UNKNOWN branch, and that is worth an entire 418-line decoder.

**Two things the JSON does not record, both found by measurement:**

- **Fractional sampling.** dependency[16] records only `sum(Hi*Vi) <= 10`.
  libjpeg additionally requires every `Hmax/Hi` to be an integer. Measured: all
  sixteen (H,V) pairs in 1..4 decode when a *single* component carries the
  non-unit factor; a second component with a differing non-unit factor gives
  "Fractional sampling not implemented yet". Unhandled, this killed 35 of 200
  files.
- **Non-zero DC categories.** The JSON's construction makes symbol 0 the shortest
  codeword in both tables, so every coefficient decodes to zero and the IDCT runs
  on an all-zero block. Leaving the DC table's *first* symbol free — a magnitude
  category 1..15, which dependencies[29] permits — makes the decoded difference
  non-zero, turning on dequantization and the full integer IDCT: `jidctint.c`
  0 → 151, worth **+264 lines** across a 200-file corpus.

---

## Expressed

### Constraints

**All 77 Tier A entries**, each inside a `SetEvilBit(false)` guard with a
distinct local name: the nine marker signatures; the fixed strings (`JFIF\0`,
`Exif\0`, the XMP URI, `ICC_PROFILE\0`, `Ducky`, `Photoshop 3.0\0`, `Adobe`,
`Adobe_CM\0`, `FPXR\0`, `8BIM`); the Tier A enumerations (SOF marker, precision,
component counts, sampling factors, table destinations, `htInfo`, `Tq`); and
every `szSection`, written back from the bytes each segment actually emitted
rather than computed up front.

**All 32 Tier B entries** with their complete `valid_values`: the 46-value
unrouted-marker set (less one — see below), `Pq`, `APP0.units`,
`APP0.extension_code`, `APP14.color_transform_code`, `DHP.P`, `JPGLS.precision`,
the Ss/Se/Ah/Al ranges and the EXIF enumerations on the parse side.

### Dependencies — all 35

[0]/[1] gate precision on the frame type — SOF3 is the only route to the thirteen
precisions other than 8 and 12, and all fifteen appear. [2]–[9] are the whole
spectral-selection matrix: SOF0/1 take Ss=0 Se=63 Ah=Al=0; SOF2 with a
multi-component scan takes the DC-only scan the JSON measured as the only clean
single-scan progressive file; SOF2 with one component may take an AC band; SOF3
takes a predictor 1..7. [12]/[13] make the DQT define all four destinations and
the DHT both classes of destination 0 before any scan may name one. [14] takes
the scan's component ids from the frame. **[16] is satisfied without narrowing any
sampling factor**, by choosing a single-component scan when `sum(Hi*Vi)` exceeds
10 — which is also worth +252 lines in its own right. [17] places RSTn markers.
[29] keeps DC symbols in 0..15. [33] is the Adobe transform. [34] is the
standalone-marker length quirk, kept as the template's own limitation.

### Structure — all 22

SOI is a fixed head outside the loop; the marker run is a **three-state
lookahead** (DQT → tables/parameters/frame → scan) so the generator walks the
layout instead of picking segments at random; the DQT is forced first because its
absence is the one fatal omission; the scan is contiguous; the EOI is a fixed
tail, omitted in ~14% of files to reach the synthetic-EOI path.

### `payload_wellformedness` — all six

| entry | codec | how the size is derived |
|---|---|---|
| `Huffmann_Table.length` | canonical Huffman spec (T.81 Annex C) | counts drawn at each length from the set the **Kraft bound still allows**: with `c_l = (c_{l-1}<<1) + n_l`, the draw is restricted so `c_l < 2^l` always. Never one fixed table. |
| `Huffmann_Table.HTV` | Huffman symbol list | exactly `sum(length)` bytes; AC symbol 0 is EOB, DC symbols are free magnitude categories 0..15 |
| `JPGFILE.scanData` | entropy-coded segment (T.81 Annex F) | `MCU count × (DC codeword + DC category bits + AC codeword)`, the MCU count from `X_image`, `Y_image`, `nr_comp`, `Horz`, `Vert`, `SOS.nr_comp` and `Ri` |
| `JPGFILE.unterminatedScanData` | same, unterminated | identical derivation; selected by omitting the EOI |
| `UNKNOWN.unknown` | marker-specific body | 0xFFC9–CB an arithmetic frame header (P, Y, X, Nf, component triple, length 11); 0xFFCC conditioning pairs with the DC low-nibble rule; 0xFFDC a two-byte line count; otherwise free bytes |
| `APP2.data` | ICC v2 profile | a complete 132-byte profile — size at 0–3, `mntr`/`RGB `/`XYZ `, the fixed `acsp` at 36–39, the D50 illuminant at 68–79, tag count 0 |

The scan is zero bytes, so no `0xFF` ever appears and the byte-stuffing gate is
satisfied by construction. When the budget cannot hold the full scan it is
**truncated** — libjpeg conceals the missing MCUs and still decodes. No
dimension, component count, sampling factor or restart interval is ever narrowed
to make a scan fit. A measured share of scans is left as free bytes instead,
because the JSON's own gate says both the valid and the garbage stream are
coverage.

### `diversity_axes` — all 33 confirmed

**Tier C, declared bare** (no value set, no `<min=>`, no `<max=>`):
`SOFx.X_image`, `SOFx.Y_image`, `DRI.Ri`, `QuanTable.qTable`, `COMPS.compId`,
`COMMENT.comment`, `JPGFILE.garbage`, `IFD.nDirEntry`, `DIRENTRY.nComponent`,
`CDIR.nDirEntry`, `APP0.xThumbnail`, `APP0.yThumbnail`.

`xThumbnail`/`yThumbnail` deserve a note: every **declaration** is bare. The only
writes are the `structure[14]` rule the JSON itself prescribes — when the budget
cannot hold `3*x*y`, emit *no* thumbnail by zeroing the dimensions rather than
shrinking them.

**Tier A, whole legal set emitted** (the JSON's own `tier_note`: "emit the whole
legal set, do not narrow it to the convenient member"): `SOFx.nr_comp` (all ten,
1–10 confirmed), `COMPS.Horz` and `COMPS.Vert` (**all sixteen pairs** confirmed),
`SOS.nr_comp` (all four), `SOFx.marker` (all four, plus the three arithmetic
ones), `SOFx.precision` (all fifteen), `COMPSOS.AC`/`COMPSOS.DC`,
`Huffmann_Table.htInfo`, `.length`, `.HTV`, `APP2.block_num`, `APP2.block_total`.

**Tier B, whole set:** `APP14.color_transform_code`, `QuanTable.Pq` (both),
`SOS.Ss`, `SOS.Se`, `UNKNOWN.UnknownMarker`, `APP0.extension_code`,
`DIRENTRY.dataFormat`, `DIRENTRY.tagNumber`.

A grep for `<min=`, `<max=`, `generation_range`, `practical`, `sensible` returns
**zero**.

Confirmed over 1000 files: all 7 frame markers, 14 of 15 precisions in the
sample, frame components 1–10, scan components 1–4, **all 16 legal sampling
pairs**, both `Pq` values, 54 distinct markers, dimensions spread tiny/small/large.

---

## Not expressed

- **A genuinely Huffman-coded scan.** The construction emits canonical all-zero
  codewords plus free DC magnitude categories. Encoding arbitrary AC run/size
  pairs needs a bit-packer with byte stuffing, which the template language can
  express only at ruinous line cost. Consequence: the AC coefficient and EOB-run
  loops in `jdhuff`/`jdphuff` are only partly reached (`jdhuff` 303 of 347).
- **The EXIF/TIFF IFD sub-tree and the Canon CIFF block** are parse-only in the
  generation direction — dependencies[22]–[28] and structure[9]–[11] are honoured
  on the parse side. Measured reason: libjpeg-turbo never parses APP1 or the CIFF
  APP0, so the entire sub-tree is worth **0 lines** to this target, while
  generating it requires correct TIFF origins, out-of-line value blocks and IFD
  chaining. The JSON says the same of the ICC profile it does ask for ("djpeg
  decodes the image identically with a valid or a garbage profile") — that one is
  emitted anyway, since it is cheap.
- **The nested JPEG streams** (structure[21], dependencies[19]/[25]): JFXX 0x10
  and the EXIF thumbnail. The template parses them; generating one needs the
  nested stream's length backpatched into the enclosing segment *before* that
  length is used to bound the nested parse, and djpeg ignores both.
- **Parsing a third-party JPEG's entropy-coded segment.** Because the scan extent
  is now derived from the frame geometry instead of found with `FindFirst`, the
  template will mis-size a real photograph's denser scan. Its own output
  round-trips 200/200. This is the direct cost of the `FindFirst` finding below,
  and the one fidelity trade in the rewrite.
- **`0xFFD9` in the unrouted-marker set.** structure[18] forbids an EOI before the
  scan and libjpeg refuses the whole file for it, so it is the one value of the 46
  not emitted — a `forbidden` structure rule taking precedence, not a narrowed
  axis. The measured-fatal markers (0xFFC5–C8, 0xFFCD–CF, 0xFFDE, 0xFFDF, 0xFFF7)
  *are* all emitted; each costs its file's decode but is a real rejection branch.
- **The 31 baseline-only lines** are almost entirely structural-error paths the
  tier rules exist to prevent: `JERR_SOI_DUPLICATE`, `JERR_SOF_DUPLICATE`,
  `JERR_SOS_NO_SOF`, four `JERR_BAD_LENGTH`, two `JERR_BAD_COMPONENT_ID`, two
  `JERR_DHT_INDEX`, two `JERR_BAD_HUFF_TABLE`, `JERR_NO_SOI`,
  `JERR_IMAGE_TOO_BIG`, `JERR_BAD_PRECISION`, `JERR_COMPONENT_COUNT`. The baseline
  reaches them because its Tier A fields are unguarded; no guard was weakened to
  chase them.

**No Tier C field was narrowed to work around any of these.**

## Six bugs verification caught

- **`ffcompile` does not array-ify repeated declarations — it overwrites.** A loop
  of `ubyte length;` yields a scalar, so `length[i]` would not compile. Every
  constructed array (Huffman counts, symbol list, ICC profile, scan) instead
  commits its bytes with **forward lookaheads** and then declares the original's
  array bare.
- **A lookahead cannot target a bitfield** — "bitfield lookahead not implemented",
  200/200 files failed. `Pq`/`Tq`, `AC`/`DC` and `Ah`/`Al` moved to `<values=>`
  attributes.
- **`FindFirst` in the generation direction materialises the marker it is
  searching for.** It appended a second `FF D9` and a run of padding past the end
  of every file; the spurious hit then sent the scan down the random-bytes branch
  and called `FileSize()`, which committed a random file length and padded it with
  garbage. Median file: 34 KB of noise. Removing the call took the round-trip from
  77/200 to **200/200** and the median file from 34 KB to 492 bytes.
- **`FileSize()` itself** commits a random length and pads — the original calls it
  at top level to set `JpegFileEnd`. Replaced with a literal ceiling; now called
  nowhere.
- **Signature lookaheads commit more than a short branch consumes.** The APPn
  "unknown" branches read fewer bytes than the 5-, 12-, 14- and 29-byte signature
  lookaheads had committed, leaving unread trailing bytes and a short parse. Fixed
  with a per-branch minimum body length.
- **`g_sofm` was never recorded for SOF0–3**, so every progressive file got
  sequential Ss/Se and was refused outright. And a `& 0x0FFF` bound on opaque
  bodies dropped the original's `- 2`, making the length not a fixed point of
  itself — the round-trip fell to 117/200 until it became `(szSection - 2) & 0x03FF`.

ffcompile also mines `szSection != 12` from APP13 into the class **every** marker
segment shares, and `nComponent == 1` into a Tier C axis; both neutralised with
local copies.
