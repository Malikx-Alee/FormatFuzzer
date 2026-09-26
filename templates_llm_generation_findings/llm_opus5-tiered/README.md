# Tiered generative templates — findings index

One document per format, covering what the tiered constraints JSON could be
**expressed** in the rewritten `.bt`, what could **not**, and what had to be
measured rather than believed.

| | |
|---|---|
| **Strategy** | tiered (`docs_llm/tiered_constraint_strategy.md`, prompts 1 and 2) |
| **Model** | claude-opus-5 |
| **Templates** | `templates_llm/llm_opus5-tiered/<fmt>-llm.bt` |
| **Inputs per format** | `templates_originals/<fmt>-orig.bt` + `llm_learned_specification/llm_reterived_constraints_<fmt>-llm_opus5-tiered.json`, and nothing else |
| **Gate** | `scripts/target_coverage.py <fmt> --count 2000` vs `scripts/target_coverage_llm.py <fmt> --llm-model opus5-tiered --count 2000` |

## Results — all ten formats, 2000 files each, 0 driver timeouts on either side

| format | target | baseline | tiered | Δ pts | Δ lines | Δ fn | lines | ratio |
|---|---|---|---|---|---|---|---|---|
| [png](png.md)  | libpng 1.6.57 `pngtest -m`              | 21.6% (2687/12424)   | **38.1%** (4735)  | **+16.5** | +2048  | +78  | 582/388   | 1.5000 |
| [pcap](pcap.md)| tcpdump 4.99.6 + libpcap 1.10.6         | 4.9% (2241/45648)    | **13.7%** (6272)  | **+8.8**  | +4031  | +211 | 329/220   | 1.4955 |
| [jpg](jpg.md)  | libjpeg-turbo 3.2.0 `djpeg`             | 14.2% (2580/18178)   | **23.6%** (4282)  | **+9.4**  | +1702  | +71  | 2194/1631 | 1.3452 |
| [midi](midi.md)| TiMidity++ 2.15.0                       | 9.8% (2883/29416)    | **13.8%** (4050)  | **+4.0**  | +1167  | +33  | 386/261   | 1.4789 |
| [zip](zip.md)  | Info-ZIP UnZip 6.0 `unzip -t`           | 28.1% (1493/5304)    | **32.0%** (1699)  | **+3.9**  | +206   | +4   | 1003/669  | 1.4993 |
| [mp4](mp4.md)  | FFmpeg 6.1 transcode                    | 4.1% (21527/521084)  | **6.9%** (36213)  | **+2.8**  | +14686 | +744 | 1185/807  | 1.4684 |
| [avi](avi.md)  | FFmpeg 6.1 transcode                    | 4.4% (22682/521084)  | **6.5%** (34111)  | **+2.1**  | +11429 | +790 | 456/304   | 1.5000 |
| [bmp](bmp.md)  | gdk-pixbuf 2.42.12 `io-bmp.c`           | 19.7% (1079/5470)    | **21.5%** (1177)  | **+1.8**  | +98    | +2   | 206/138   | 1.4928 |
| [gif](gif.md)  | giflib 5.2.2 `gif2rgb -1`               | 25.1% (606/2412)     | **26.7%** (644)   | **+1.6**  | +38    | +1   | 306/204   | 1.5000 |
| [wav](wav.md)  | WavPack 5.9.0 `wavpack -y`              | 20.9% (2358/11286)   | **22.5%** (2543)  | **+1.6**  | +185   | +3   | 855/574   | 1.4895 |

**Every format improved. None regressed.** Every template is inside the 1.5×
line-count limit, and `templates_originals/` is unmodified throughout.

## What the tier discipline expressed well

- **Tier A as an identity, not a constant.** Where the JSON marks a length,
  count or offset Tier A, the value is written back from the bytes actually
  emitted and the *quantity* stays free. That is what let sample counts, chunk
  counts, entry counts and frame counts span their full range while every
  length field stayed exact.
- **Tier B completeness is where most of the coverage is.** Emitting the whole
  legal set rather than the convenient member is the single largest repeated
  win: 103 pcap link types (+1356), 29 AVI `biCompression` values, 23 WAV format
  tags (WAVE_FORMAT_IEEE_FLOAT alone lights all 109 lines of `pack_floats.c`),
  19 ZIP methods, 21 MP4 handler types, all 18 MIDI meta types.
- **Tier C left alone beats Tier C tuned.** In ZIP, leaving `deFileName` free —
  which Tier C demands — measured *better* than mirroring the local name
  (+22 lines in the name-mismatch handling). The tier rule and the coverage
  objective agreed.
- **`payload_wellformedness` derived from `derives_from`** rather than the other
  way round. No dimension, count, depth or rate was ever narrowed to fit a
  precomputed payload in any of the ten.

## What recurred as *not* expressible

1. **`output_budget` always exceeds the engine.** `MAX_FILE_SIZE` is 65536 and
   `MAX_RAND_SIZE` is 131072; the JSONs ask for 1 MiB and up. Every format
   scaled the ratios down and said so. Nothing was clamped except array lengths.
2. **Value sets on `string` fields.** ffcompile has no `possible_values`
   overload for `std::string`, so registered keyword lists (PNG text keywords,
   ZIP names) cannot be declared and fall back to free content.
3. **Lookaheads cannot target bitfields** (`bitfield lookahead not implemented`),
   and ffcompile **silently drops `<values=>` on a bitfield inside `if`/`switch`/
   `while`**. Hit in PCAP, JPG and MIDI; worked around by hoisting or by
   `<values=>` at struct top level.
4. **Parsing a foreign file's compressed payload.** Wherever a codec stream is
   pinned under `SetEvilBit(false)` — PNG zlib, GIF LZW, ZIP deflate — a
   third-party file's differently-coded payload no longer parses. Self
   round-tripping, which AFL+FFMut needs, works everywhere (200/200 in all ten).
5. **Baseline-only lines are almost always malformed-input error paths.** They
   are the direct price of Tier A guarding, and none was bought back by
   weakening a guard: PNG 77, ZIP 87, PCAP 116, MIDI 94, AVI 195, JPG 31.

## The engine traps that cost real coverage

Recorded here because they are template-language findings, not format findings.

- **ffcompile mines `<field> == <const>` into that field's known-value set and
  pins it — across every struct sharing the field name.** This caused three
  separate measured regressions: WAV `wChannels` pinned to 1 (`extra2.c` at
  0/550), AVI `datalen` pinned to 44 (0/200 parses), ZIP `frCompressedSize`
  pinned to 0. The fix is always the same: compare a `local` copy.
- **`local T x[1];` compiles to an empty `std::vector`.** Every `x[0] = …` is
  out-of-bounds UB and `<values=x>` silently degrades to a free draw — with
  behaviour differing between `-O1` and `-O3`. Found in PCAP.
- **A byte already in the lookahead bitmap cannot be re-planted**; the second
  plant silently loses. Found in MIDI and ZIP.
- **`FindFirst` and `FileSize()` materialise what they look for** in the
  generation direction. In JPG this appended 34 KB of padding to the median
  file; removing both calls took the round-trip from 77/200 to 200/200.
- **`ffcompile` merges same-named anonymous structs** — MP4's `trun` and `senc`
  both declare `entry`, and one class was generated for both.
- **The bare-integer draw is small-biased**: 87.5% of any bare integer is
  `1 + rand_int(16)`. This is load-bearing in both directions — it is why 94.6%
  of GIF images fit their exact payload, and why PCAP ports above 255 and MIDI
  SMPTE timebases are rare. It is a property of the engine, never corrected by
  narrowing a field.

## Where the JSON was wrong, and how it was caught

Every format was probed against the *actual* harness before any template code
was written. Seven formats turned up `measured_gate` claims that did not hold,
usually because the JSON measured a different tool or a different version.

| format | the JSON said | measured here |
|---|---|---|
| pcap | `snaplen` "advisory only, bounds nothing" | `sf-pcap.c:637` truncates every packet to it — **+1173 lines** |
| pcap | `orig_len` "completely unvalidated" | `print.c:354` discards the packet — **90.1% of records dropped** |
| avi  | `genericblock.id` "completely free, even 'xxxx' decoded" | 6.1 derives the stream index from it — **−4878 lines** for a non-digit prefix |
| bmp  | `biPlanes` is a gate (per ImageMagick/ffmpeg) | gdk-pixbuf accepts 0, 1, 2, 255 — not a gate at all |
| zip  | methods 1–7, 9, 10 "refused as invalid" | Info-ZIP 6.0 implements them — shrink **+78**, deflate64 **+66**, implode **+47** |
| gif  | confinement is `confidence: medium` | it is the format's front gate: `gif2rgb.c:440` aborts the whole file |
| mp4  | out-of-range `sample_description_index` "reaches a fallback" | `mov.c:4363` drops **every sample of the track** — zero frames decoded |

Two were also harness bugs rather than template bugs: `target_coverage_llm.py`
drove `gif2rgb` without `-1` (worth ~2.5 points on every GIF variant ever
measured by that script; fixed), and the stored WAV and ZIP baselines on record
came from 10,000-file runs and are not comparable to a 2000-file number.
