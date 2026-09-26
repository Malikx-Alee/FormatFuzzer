# BMP — tiered generative template findings

| | |
|---|---|
| **Output** | `templates_llm/llm_opus5-tiered/bmp-llm.bt` — **206 lines** from a 138-line original, **1.4928×** |
| **Inputs** | `templates_originals/bmp-orig.bt` + `llm_reterived_constraints_bmp-llm_opus5-tiered.json` |
| **JSON** | 30 constraints (A 7 / B 2 / C 21), 15 dependencies, 11 structure rules, 10 diversity axes |
| **Target** | gdk-pixbuf 2.42.12, `io-bmp.c` via the custom decode harness |

## Verification

| step | result |
|---|---|
| 1 `ffcompile` | exit 0 |
| 2 `build_new.sh` | exit 0 |
| 3 generate 200 | 0 errors; **147 distinct sizes**, most common 5× (2.5%), min 58, median 168, p75 490, p95 28346, max 47864 |
| 4 round-trip `parse` | **200/200** (95/200 decode in gdk-pixbuf) |
| 5 gate | **no regression — the first measured attempt was the final one** |

**Coverage: 19.7% (1079/5470) → 21.5% (1177/5469), +1.8 points / +98 lines / +2
functions**, a strict function superset. Within `io-bmp.c` itself: **517 → 618**.

The two coverage scripts drive BMP identically, so unlike GIF there was no
harness divergence.

---

## What had to be re-measured

**The coverage target is gdk-pixbuf; the JSON measured ImageMagick, Pillow and
ffmpeg.** None of the three is the harness, so the probe was rebuilt against
`io-bmp.c` directly (~60 mutations plus nine cumulative corpora). Several of the
JSON's gates do not hold here:

- **`biPlanes` is not a gate at all** — 0, 1, 2 and 255 all decode. The JSON made
  it Tier A on ImageMagick and ffmpeg refusing it. It is pinned anyway (Tier A is
  Tier A, and it costs nothing).
- **BI_JPEG and BI_PNG are refused at the header** (`io-bmp.c:399`,
  `Compressed > BI_BITFIELDS`), so their payloads are never read.
- **BI_BITFIELDS works at 16bpp as well as 32**, because gdk-pixbuf reads the
  masks from a fixed offset after the header rather than after the palette.
- **A correct RLE stream is worth essentially nothing here**: 10 files of
  well-formed RLE8/RLE4 gave 275 `io-bmp.c` lines against **277** for the same
  files filled with random bytes. What *is* worth something is **absolute mode**
  (+23), which random bytes only reach by luck.

The measured feature ladder that drove the design: six depths **+155**, top-down
**+18**, RLE **+99**, BI_BITFIELDS **+87**, rejection paths **+33**.

---

## Expressed

### Constraints

**All 7 Tier A entries.** `bfType` = "BM", `biSize` = 40, `biPlanes` = 1 — each
behind its own `SetEvilBit(false)` — and `bfSize` / `bfOffBits` / `biSizeImage`
backpatched by `FSeek` from the layout actually produced. The backpatch fires
only when the value differs, which keeps the parse direction honest for
well-formed files.

### Dependencies — all 15

- **#0–2 and #11** use the forward-lookahead form. `biCompression` sits two bytes
  *after* `biBitCount`, so it is drawn first by `ReadUInt(FTell() + 2, …)` and the
  depth branch follows: RLE8→{8}, RLE4→{4}, BI_BITFIELDS→{16,32},
  BI_JPEG/PNG→{0,24}, otherwise the full Tier B set. **#11** (a top-down image may
  not be compressed) selects a different lookahead array when `biHeight < 0`, so
  the set itself carries the rule.
- **#12 is a template gap the JSON flags**: the original declares pixel data only
  for `<8`, `==8`, `==24` and `==32`, so a 16bpp image gets *no pixel bytes at
  all*. One changed condition (`< 8 || == 16`) routes 16bpp into
  `imageData[bytesPerLine]`, reusing the original identifier rather than inventing
  one.
- **#9 is the other template bug**: `1 << biBitCount` at 16bpp asks for 65536
  palette entries (262 KB). Clamped to the format's own 256-entry ceiling — the
  `output_budget` the structure section prescribes, and a no-op when parsing any
  real file.

### `payload_wellformedness` — one field, three constructions

`rleData` is a single opaque array whose contract is chosen by `biCompression`.
All three are sized from `biWidth`, `biHeight` and `biBitCount`, never the
reverse.

| context | codec | size derivation |
|---|---|---|
| `biCompression == 1/2` | Microsoft RLE8 / RLE4 | per row: runs of `min(n,255)` until `biWidth` pixels are accounted for, then `00 00`; `00 01` at the end. RLE4 packs two 4-bit indices per byte, so an absolute run is `ceil(k/2)` bytes padded to even |
| `biCompression == 3` | BI_BITFIELDS — three LE DWORD masks then raw rows | `12 + abs(biHeight) × (bytesPerLine + padding)`; the masks follow the declared depth (0xF800/0x07E0/0x001F at 16bpp, 0x00FF0000/0x0000FF00/0x000000FF at 32) |
| `biCompression == 4/5` | embedded JPEG / PNG | the payload opens with `FF D8` or `89 50 4E 47`, counted inside `biSizeImage` so the array-length identity holds in both directions |

The masks are the JSON's `unnamed_payload_substructure`: they have no field
anywhere in the `.bt`, so they are emitted as the leading bytes of `rleData`,
which at 32bpp is exactly where they belong. Rows alternate encoded and absolute
mode and **every third row opens with a `00 02 dx dy` delta**, so all three
branches of gdk-pixbuf's RLE state machine run — that plus the depth-correct
masks was worth +12 `io-bmp.c` lines over the first version.

### `diversity_axes` — all 10 confirmed

**Tier C, declared bare** (no value set, no `<min=>`, no `<max=>`): **`biWidth`**,
**`biHeight`** (its sign is the top-down axis), **`biClrUsed`**,
**`BITMAPLINE.colorIndex`**, **`BITMAPLINE.padBytes`**, **`RGBQUAD.rgbReserved`**.

**Tier B, complete set:** **`biBitCount`** — the five branches together emit all
eight values, each conditioned on a real dependency — and **`biCompression`**,
bare, with the weighted lookahead emitting all ten.

**Tier A axes whose free quantity stays free:** `biSizeImage` and `bfOffBits` are
bare at declaration and only backpatched, which is precisely what their
`tier_note` asks for.

`preferred_value` is applied as weighting by repetition in the value arrays,
never as a filter — `ReadUInt` has no preferred/possible split.

Confirmed in the corpus: **all 8 legal depths and all 10 compression methods
appear**, plus out-of-set depths from the evil bit. Top-down images are rare —
5 in 2000 — because FormatFuzzer's bare `LONG` is small-biased positive; that is
a property of the engine, not a narrowing, and `biHeight` stays bare.

A grep for `<min=`, `<max=`, `generation_range`, `practical` and `sensible`
returns zero.

---

## Not expressed

- **Header variants other than 40 bytes.** `BITMAPINFOHEADER` is a fixed
  eleven-field struct and `biSize` is never used to size anything, so 12, 52, 56,
  64, 108 and 124 are inexpressible — the JSON's own `template_parse_requirement`
  says widening needs real header bytes, not a different number. **This is
  measurable: it is exactly the 15 lines the baseline reaches and this template
  does not** (`io-bmp.c:324–335`, the BITMAPCOREHEADER branch and the
  unsupported-size error). Tier A was honoured rather than second-guessed, and
  this is the price.
- **A gap before the pixel data.** The template places pixels immediately after
  the palette and has no filler field, so `bfOffBits` is always exactly the
  palette end. The JSON records the same limitation. Measured cost on this
  target: **zero** — gaps added no `io-bmp.c` lines.
- **"Redraw the dimension pair" budgeting.** A `.bt` field is written once, so it
  cannot be redrawn. The pixel array is truncated instead, which gdk-pixbuf
  tolerates (measured: 0%, 10%, 50% and 100% of rows all decode). `biWidth` and
  `biHeight` keep their full free span in the header either way.
- **Complete embedded JPEG/PNG files** for BI_JPEG and BI_PNG — only the correct
  signature and a free-byte body are emitted. gdk-pixbuf refuses both compression
  codes at the header before reading a payload byte, so the measured benefit is
  zero, and the line budget was already at the limit.
- **The four remaining baseline-only lines** (`io-bmp.c:412–416`, "BMP image width
  too large") need `width × bytesPerPixel` to overflow a signed int. This template
  does emit such widths — 5 files in 2000 — so this is sampling noise rather than
  a structural gap.

None of these was worked around by constraining a Tier C field.

## Notes

The 69 lines of headroom were the binding constraint throughout: a backpatch
block, a dependency lookahead, an RLE state machine, the bitfield masks and three
budget clamps had to fit in them. Getting there cost most of the explanatory
comments (each surviving one still names its constraint) and K&R braces in the
added blocks; the original's own formatting is untouched.
