# GIF — tiered generative template findings

| | |
|---|---|
| **Output** | `templates_llm/llm_opus5-tiered/gif-llm.bt` — **306 lines** from a 204-line original, **1.5000×** (at the limit) |
| **Inputs** | `templates_originals/gif-orig.bt` + `llm_reterived_constraints_gif-llm_opus5-tiered.json` |
| **JSON** | 60 constraints (A 21 / B 13 / C 26), 22 dependencies, 13 structure rules, 18 diversity axes |
| **Target** | giflib 5.2.2, `gif2rgb -1` |

## Verification

| step | result |
|---|---|
| 1 `ffcompile` | exit 0 |
| 2 `build_new.sh` | exit 0 |
| 3 generate 200 | 0 errors; **172 distinct sizes**, most common 9× (4.5%), min 20, median 4283, p95 33130, max 42638 |
| 4 round-trip `parse` | **200/200** |
| 5 gate | first run regressed — **cause was a harness bug, not the template** (below) |

**Coverage: 25.1% (606/2412) → 26.7% (644/2412), +1.6 points / +38 lines**, and a
strict superset of the baseline's functions.

Against real `gif2rgb`: 40 full decodes, 132 confinement rejections, 26
background-out-of-range, 2 decoder error paths.

---

## The harness bug this format uncovered

The first run measured **22.5%**, a 2.6-point regression.
`scripts/target_coverage_llm.py:278` drove `gif2rgb` **without `-1`**, while
`scripts/target_coverage.py:369` already had the fix. Without `-1`,
`-o /dev/null` becomes `/dev/null.R` and `GIF_EXIT` fires *after* decoding but
*before* the RGB dump — so `DumpScreen2RGB`'s output loop and `DGifCloseFile`
are unreachable no matter how good the file is.

The fix was ported (one line plus its comment). **Every LLM-variant number
previously recorded by that script is understated by roughly that amount and is
not comparable to a `target_coverage.py` baseline.** `drive_midi` still diverges
between the two scripts the same way (`timidity -c dummy.cfg - < file` vs
`-c <cfg> file`) — left alone as out of scope, but probably the same class of bug.

Separately, this toolchain could not link at all (`ld` cannot parse the
CommandLineTools 27.0 SDK's `.tbd` files);
`export SDKROOT=$(xcode-select -p)/Platforms/MacOSX.platform/Developer/SDKs/MacOSX.sdk`
fixes it.

---

## Expressed

### Constraints

All **17 `fixed_value` markers** pinned. Complete Tier B sets for `Version` (2),
`LZWMinimumCodeSize` (7), `ApplicationIdentifier` (7), `DisposalMethod` (8,
weighted to the 4 defined) and `UNDEFINEDDATA.Label` (all 252, via a generated
256-entry label table). The three `calculated_value` entries hold by
construction — `DATASUBBLOCK.Size` because the same lookahead byte is both the
loop control and the field, and the two colour tables via the original's
doubling loop.

### Dependencies — 21 of 22

- **#20, confinement**, turned out to be the format's real front gate rather than
  the soft rule the JSON records at `confidence: medium`: `gif2rgb.c:440` aborts
  the *whole file* when `Left + Width > SWidth`. Exact equality passes, one over
  does not. Implemented the way the JSON frames it — the `then` field is
  `ImageLeftPosition`, so the upcoming free dimensions are read with
  `ReadUShort(FTell()+4)` and the **placement** is derived from them. Width and
  height are never touched, and ~2/3 of frames still overflow and reach the
  rejection path.
- **#16, "87a forbids extensions", deliberately not implemented.** giflib compares
  only the first three bytes — `87a` and even `99z` were measured decoding a
  graphic control extension fine. Honouring it would delete extension coverage
  from half the corpus for no gate.

### `payload_wellformedness` — the one entry, and what moved the number

`DATASUBBLOCK.Data`, codec **GIF LZW, LSB-first, variable width (GIF89a
Appendix F)**. Size derived as `nPix = ImageWidth * ImageHeight`, code width from
`LZWMinimumCodeSize`. Both stay bare; the stream is computed from them.

**The JSON's literal-only construction was not used as written.** It is correct —
all 112 combinations of code size 2–8 × 8 dimension pairs × both interlace flags
were verified to decode — but it costs 26 lines of `dgif_lib.c`, because a stream
of pure literals never builds a dictionary entry worth tracing. The baseline's
*random* bytes hit `DGifDecompressLine`'s prefix walk by accident; a correct
literal-only stream never does.

The emitter instead produces, per group: `Clear`, one literal, then repeats of
`ClearCode + 2`. The first of those is the KwKwK special case
(`Prefix[CrntCode] == NO_SUCH_CODE`); the rest take the normal trace. Each emits
exactly **two** pixels, so the accounting stays closed-form:

```
gpix = 2*runLen - 1;  nFull = nPix / gpix;  rem = nPix - nFull*gpix
totalCodes = nGroups + nFull*runLen + lastCodes + 1
```

giflib's `DGifDecompressLine` was ported to Python to verify this: exact pixel
counts for every N ∈ 2..8 and every P from 0 to 65535, code width never
exceeding N+1, then 462 real `gif2rgb` runs with zero failures. It recovered
`920/929/943/952/964/967/1016` — the whole prefix-walk group.

Padding after EOI inside the chain is free (giflib was measured accepting up to
600 bytes of it), so the sub-block split lengths stay arbitrary.

### `diversity_axes` — all 18 confirmed bare

`ImageWidth`, `ImageHeight`, `SizeOfGlobalColorTable`, `SizeOfLocalColorTable`,
`LogicalScreenDescriptor.Width`, `.Height`, `TransparentColorIndex`, `DelayTime`,
`BackgroundColorIndex` — no value set, no `<min=>`, no `<max=>`.

Tier B axes carry their complete sets (`InterlaceFlag`, `GlobalColorTableFlag`,
`LocalColorTableFlag`, `DisposalMethod`, `LZWMinimumCodeSize`,
`ApplicationIdentifier`); every packed-field flag spans its full bit width, so
bare already *is* the complete set. `DATASUBBLOCK.Size` is pinned in value but
free in segmentation, from a table covering all of 1..255.
`ImageLeftPosition`/`ImageTopPosition` carry the confinement dependency — the
only `= {}` on a Tier C field, and the sanctioned exception.

A grep for `<min=`, `<max=`, `generation_range` and `practical` returns zero.

**The GIF trap did not need resisting.** FormatFuzzer's bare-integer generator is
already small-biased (measured: 88.4% of bare `ushort`s in 1..16, 2.95%
full-range), so **94.6% of images fit the exact payload** while the tail still
produces 65535-wide frames.

---

## Not expressed

- **Foreign GIFs will not parse past the image data.** The LZW bytes are emitted
  under `SetEvilBit(false)`, so parsing a third-party GIF fails where its
  compressed bytes differ from the computed stream. Inherent to the prompt's own
  `ZLIB_ZERO_STREAM` recipe, which has the identical property. Self
  round-tripping — what AFL+FFMut needs — works on all 200.
- **The JSON's budgets exceed the engine ceiling.** `MAX_FILE_SIZE` is 65536;
  the 1 MiB / 768 KiB figures are unreachable, so they were clamped to
  40 KiB / 20 KiB and the template says so.
- **12 baseline-only lines**, all malformed-stream error paths:
  `D_GIF_ERR_READ_FAILED` (601/612), the out-of-order KwKwK branch (937–941),
  `D_GIF_ERR_IMAGE_DEFECT` (960), and the `Code > LZ_MAX_CODE` guard. The price
  of emitting *correct* payloads: 12 given up to take 35 in the same file, and
  nothing narrowed to buy them back.
- **NETSCAPE's conventional position** is reachable (an application extension as
  the first block sits right after the global colour table) but not forced;
  forcing it needs a pre-loop special case there was no line budget for.

## Notes

Reaching exactly 1.50× cost the per-declaration evil guards on lookahead-pinned
markers. That turned out to be a fix rather than a compromise: guarding the
*declaration* leaves the marker wrong 1/123 of the time (the **lookahead** is
what goes evil), while guarding the lookahead pins it 20000/20000. All 200 files
carry a correct signature and trailer.
