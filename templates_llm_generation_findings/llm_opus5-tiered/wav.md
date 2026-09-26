# WAV — tiered generative template findings

| | |
|---|---|
| **Output** | `templates_llm/llm_opus5-tiered/wav-llm.bt` — **855 lines** from a 574-line original, **1.4895×** |
| **Inputs** | `templates_originals/wav-orig.bt` + `llm_reterived_constraints_wav-llm_opus5-tiered.json` |
| **JSON** | 65 constraints (A 25 / B 9 / C 31), 25 dependencies, 13 structure rules, 17 diversity axes |
| **Target** | WavPack 5.9.0, `wavpack -y` |

## Verification

| step | result |
|---|---|
| 1 `ffcompile` | exit 0 |
| 2 `build_new.sh` | exit 0 |
| 3 generate 200 | 0 errors; **185/200 distinct sizes**, most common **twice** (1%), min 60, p25 370, median 750, p75 3204, p95 6004, max 60024 |
| 4 round-trip `parse` | **200/200** |
| 5 gate | **first attempt regressed by 2.6 points** — diagnosed and fixed (below) |

**Coverage: 20.9% (2358/11286) → 22.5% (2543/11286), +1.6 points / +185 lines /
+3 functions**, a strict function superset; 214 mine-only lines against 29
baseline-only.

> **Baseline caveat.** `coverage_results/wav/summary.txt` held **22.1%** from an
> August run; that was not used as the comparison point, because it predates the
> target-coverage bug fixes in the recent commits. `target_coverage.py wav
> --count 2000` re-run twice on the same toolchain gives **20.9%** both times
> (2354 and 2358 lines). This template measured 22.4%, 22.4%, 22.5% across three
> runs. Both sides are stable; only the stale stored number disagrees.

| file | mine | base | Δ |
|---|---|---|---|
| `src/pack_floats.c` | 109 | **0** | **+109** |
| `src/pack_utils.c` | 526 | 499 | +27 |
| `src/pack.c` | 577 | 557 | +20 |
| `cli/riff.c` | 126 | 110 | +16 |
| `cli/wavpack.c` | 382 | 370 | +12 |

The single largest item is that **the baseline never emits
`WAVE_FORMAT_IEEE_FLOAT`** — `pack_floats.c` is completely dark for it. Emitting
the whole Tier B tag set lights all 109 of its reachable lines.

---

## The regression, and what caused it

**Attempt 1 measured 18.3% (2064 lines) — 2.6 points *below* baseline.** The
cause was not a Tier C field that had been constrained:

> ffcompile mines any constant compared against a **field** into that field's
> known-value set.

The original tests `format.wChannels == 1` three times (lines 83, 88, 93). That
made the generated `unsigned_short_class wChannels(1, { 1 })` — **`wChannels`
was pinned to 1 in 1985 of 2000 files** even though it was declared bare.
`src/extra2.c`, WavPack's entire stereo decorrelation analyser, sat at **0/550**.
Comparing a `local int64` copy instead leaves the field genuinely free; channel
counts now span 187 distinct values and `extra2.c` reaches 193.

The same trap applies to `wChannels > 0`, which would have mined `{0}` — every
comparison is now routed through `nc`/`nch` copies.

Three further fixes followed: the format chunk's `size_identity` (a free
`unknown` tail pushed `ckSize` past WavPack's `sizeof(WaveHeader)` ceiling of 40,
so most extensible files were rejected); the audio byte count derived from
`wBlockAlign` rather than left as a raw byte count (with a free count, 12% of
files declared fewer bytes than one sample frame); and a negative-length guard in
the array clamp that had been trimmed away, truncating 10% of files.

**Ladder: 2064 → 2437 → 2504 → 2523 → 2543.**

---

## Expressed

### Constraints

**All 25 Tier A entries**, in 17 `SetEvilBit(false)` guards with distinct local
names: `groupID`/`riffType` = "RIFF"/"WAVE", `wcbsize` = 2 (and 22 for
extensible), `FACTCHUNK.chunkSize` = 4 and `Sampler_Data` = 0 (the two
`template_parse_requirement` entries), and six backpatched `calculated_value`
fields — `hsize`, the `chunkSize` of the format, data, cue, LIST, subchunk,
unknown and sampler chunks, plus `dwCuePoints`, `Num_Sample_Loops`,
`wBlockAlign` and `dwAvgBytesPerSec`.

The six chunkIDs are left **bare**, because the JSON gives each a `lookahead` at
line 535: the shared `ReadBytes(tag, FTell(), 4, pref, poss)` is what writes
them, and `ReadBytes` turns the evil bit **off** for its preferred set, so
guarding the declaration would fight the lookahead rather than protect it.

**All 9 Tier B entries** with their complete `valid_values`. `preferred_value` is
applied as repetition weighting, never as a filter — `wFormatTag`'s 23 values
appear as 20×1, 14×3, 14×65534, 3× each of 17/2/6/7/85 and 1× the fifteen
unpreferred ones. **All 23 appear in the corpus** (the rarest, 273, 16 times in
2000), alongside 15 out-of-set values from the evil bit.

### Dependencies — all 25

- **[1], [8], [9]** run *forward*: `wBlockAlign` and `dwAvgBytesPerSec` are
  declared before the depth they derive from, so the depth is drawn by
  `ReadUShort(FTell() + 6, …)` with a per-tag array (4 for IMA, 8 for companded,
  32/64 for float, the whole set otherwise) and `wBitsPerSample` is then declared
  bare and takes the looked-ahead value. The lookahead is **not** evil-guarded,
  because diversity_axes[2] explicitly wants out-of-set depths; six such values
  appear in the corpus.
- **[6] vs [7]** are two different byte-rate formulas keyed on the tag, which the
  JSON calls "a common source of malformed files" — both are emitted.
- **[12]** required a tail the template does not declare, so `wcbsize`,
  `wValidBitsPerSample`, `dwChannelMask`, `SubFormat` and `GUIDtail` are new
  fields — the only identifiers added, and `FORMATCHUNK.unknown`'s own note asks
  for exactly this.
- **[18]** (no format chunk ⇒ data chunk forbidden) is a branch, not a post-hoc
  check: before a format chunk exists the same bytes are read as an opaque chunk,
  so the file still carries a "data" tag and a real reader meets the case.

### Structure — all 13

`first_element` is the fixed 12-byte head with `hsize` written last; `ordering`
uses two `ReadBytes` call sites so that until a format chunk exists the only
preferred tag is `"fmt "`; `required` means the loop cannot end before both a
format and a data chunk exist; `cardinality` is the `!FEof()` chunk sequence with
a running budget; `mutually_exclusive` (a second format chunk) is a branch. All
24 named unmodelled tags from `UNKNOWNCHUNK.chunkID`'s notes are in the possible
set, and **517 distinct chunk tags** appear in the corpus.

### `payload_wellformedness` — one entry, six constructions

`DATACHUNK.waveformData` is the only entry; its `applies_when` /
`alternate_payloads` extensions make it six contracts in one field. All are sized
from `derives_from`; no format field is ever adjusted to fit one.

| tag | codec | size derivation |
|---|---|---|
| **17** DVI/IMA ADPCM | self-contained blocks, 4-bit nibbles | `floor(chunkSize / wBlockAlign)` blocks of exactly `wBlockAlign` bytes; per block, per channel, a 16-bit predictor + a step index over the whole 0–88 range + one zero reserved byte, then `wBlockAlign - 4*wChannels` free nibble bytes |
| **1** PCM, **3** IEEE float, **6/7** A-law/mu-law | none — raw samples | `chunkSize` free bytes; `chunkSize` itself is `ceil(free_length / wBlockAlign) * wBlockAlign` |
| **2** MS ADPCM, **85** MPEGLAYER3 | block/frame codecs the template does not model | the 34- and 14-byte format-chunk tails dependencies [10] and [11] require; the data stays free |

`wSamplesPerBlock` is computed as
`((wBlockAlign - 4*wChannels) * 8) / (wBitsPerSample * wChannels) + 1` **from** a
block size chosen freely at `4*wChannels + 1 + (dwSamplesPerSec % 2039)` — the
JSON's "never pick a samples-per-block figure and then bend the block size to
match". That deliberately non-multiple block size is also what reaches
`riff.c:215`, the `BlockAlign % NumChannels` rejection.

**Measured value of the ADPCM emitter on this target: zero.** WavPack accepts
only PCM and IEEE float and refuses tag 17 at `riff.c:206` before reading a
payload byte. It was implemented in full anyway because it is Tier A; this report
is the honest place to say what it bought.

### `diversity_axes` — all 17 confirmed

**Tier C, declared bare:** `FORMATCHUNK.wChannels`, `FORMATCHUNK.dwSamplesPerSec`,
`DATACHUNK.samples` (all three element types), `SAMPLES.channels`,
`FACTCHUNK.uncompressedSize`, `LISTSUBCHUNK.listData`, `CUEPOINT.dwPosition`.

**Tier B, complete set:** `wFormatTag` (23), `wBitsPerSample` (8, via the
lookahead), `LISTCHUNK.chunkType` (INFO/adtl/wavl — all three, 388/386/368),
`LISTSUBCHUNK.chunkID` (26 INFO + 4 adtl + 2 wavl, selected by the list type per
dependencies [19]–[21]), `UNKNOWNCHUNK.chunkID` (24 named tags plus arbitrary
ones), `SMPLLOOPS.Type` (0,1,2,3), `SMPLCHUNK.SMPTE` (0,24,25,29,30).

**Tier A axes whose free *inputs* stay free:** `wBlockAlign` (derived from
`wChannels` and the depth, never a constant), `DATACHUNK.chunkSize` (the audio
length is the free choice), `dwCuePoints` and `Num_Sample_Loops` (how many
records is free; the field records the count).

A grep for `<min=`, `<max=`, `generation_range`, `practical` and `sensible`
returns **zero**.

**One conflict had to be resolved:** the JSON gives `wChannels`
`excluded_values: [0]` while diversity_axes[0] marks it
`must_remain_unconstrained: true`. Tier C plus the prompt's rule won — it is bare.
Measured cost: none, because FormatFuzzer's bare `ushort` draws `1 + rand_int(16)`
in its small branch, so zero never actually occurred in 2000 files, and
dependency [16] covers the zero-block-align case the exclusion was protecting.

Feature spread over the 2000-file corpus: 38 distinct format tags (all 23 legal +
15 evil), 14 distinct bit depths (all 8 legal + 6 evil), **187 distinct channel
counts**, 517 distinct chunk tags, all three LIST types. 398/2000 (19.9%) encode
successfully; the rest reach the rejection branches, which is the point of
emitting the whole tag and depth sets.

---

## Not expressed

- **Any RIFF magic other than "RIFF".** Tier A pins `groupID`, so `RF64` (which
  would unlock `is_rf64`, the ds64 size fields and the `is_rf64 && !got_ds64`
  rejection) and a wholly unrecognised fourcc are both out. **Measurable: 10 of
  the 29 baseline-only lines are exactly that** — `wavpack.c:1981–1988` and
  `riff.c:75–76`.
- **A data `chunkSize` that disagrees with the bytes present.**
  `DATACHUNK.chunkSize` is Tier A `calculated_value`, so it is backpatched from
  the bytes actually written. That costs `wavpack.c:2225–2228` ("couldn't read
  all samples") and 2586, which the baseline reaches by declaring more audio than
  it writes. 5 more of the 29.
- **The over-16 MB and over-4 MB rejection paths** (`riff.c:280` and 324) need
  files far larger than `MAX_FILE_SIZE` = 65536. Worth a measured +35 and +2 on a
  hand-built probe; unreachable here at any budget.
- **The JSON's byte budgets** (1 MiB total, 768 KiB audio, 64 KiB each for LIST
  and unmodelled chunks, 8 KiB for the fact/cue/smpl group) all exceed
  `MAX_FILE_SIZE`. Their ratios were kept and scaled to the engine ceiling, plus a
  `Room()` helper so no array can run past the buffer. That is a clamp on array
  lengths, never on a field.
- **Landing exactly on one of WavPack's 15 standard sample rates**
  (`pack_utils.c:279`). `dwSamplesPerSec` is Tier C and the JSON says outright
  that "the classic rates 8000, 11025, 22050, 44100 and 48000 … must not become
  the emitted set", so an exact hit on a 32-bit free field essentially never
  happens. The non-standard branch (`write_sample_rate`, including its four-byte
  form) is taken instead.
- **Format chunks longer than 40 bytes** are rejected by this target, so
  dependency [10]'s 50-byte Microsoft ADPCM layout is emitted but never decoded.
  Still the right thing to write, and it reaches the rejection branch.
- **A WAVE form with no data chunk** no longer parses, because structure[1] and
  [3] make both chunks `required` and the loop will not end before producing them.
  This is the one parse-direction capability given up; it buys every generated
  file a format chunk, which is what dependency [18] and structure[2] hang on.

None of these was worked around by constraining a Tier C field.

## Notes

The line budget was the binding constraint from the start: the SMPL display
functions alone are 290 lines of the original, carried verbatim.
