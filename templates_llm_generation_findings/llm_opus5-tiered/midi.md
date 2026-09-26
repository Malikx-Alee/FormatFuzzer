# MIDI — tiered generative template findings

| | |
|---|---|
| **Output** | `templates_llm/llm_opus5-tiered/midi-llm.bt` — **386 lines** from a 261-line original, **1.4789×** (limit 391) |
| **Inputs** | `templates_originals/midi-orig.bt` + `llm_reterived_constraints_midi-llm_opus5-tiered.json` |
| **JSON** | 53 constraints (A 27 / B 1 / C 25), 18 dependencies, 13 structure rules, 12 diversity axes |
| **Target** | TiMidity++ 2.15.0, `./timidity -c dummy.cfg -Ol -o /dev/null FILE` |

## Verification

| step | result |
|---|---|
| 1 `ffcompile` | exit 0 |
| 2 `build_new.sh` | exit 0 |
| 3 generate 200 | **0 generation errors**; `min=14 p25=166 median=366 p75=24004 p95=24006 max=24014`, **140 distinct sizes**, largest bucket 19/200 (9.5%) |
| 4 round-trip `parse` | **200/200**; an independent structural validator finds **0 defects across all 2044 tracks** |
| 5 gate | no regression |

**Coverage: 9.8% (2883/29416) → 13.8% (4050/29416), +4.0 points / +1167 lines /
+33 functions.** 1261 mine-only against 94 baseline-only.

| file | base | mine | of |
|---|---|---|---|
| `readmidi.c` (the parser) | 941 | **1764** | 3990 |
| `reverb.c` | 476 | **785** | 2627 |
| `playmidi.c` | 389 | 422 | 5636 |
| `instrum.c` | 134 | 143 | 1205 |

`readmidi.c` — where this format's depth lives — nearly doubles.

The cluster near 24,000 bytes is the `output_budget` ceiling, reached by the ~26%
of files whose free `m_seclen` draw lands in the uint32 tail — not a pinned field.
The validator checks every `MTrk` intact, every `m_seclen` exact, every track
ending `FF 2F 00`, `m_ntracks` matching, no trailing bytes.

---

## What was measured

An lcov probe and a byte-level SMF constructor ran ~180 probe files before any
template code. **One valid MIDI file is worth 2409 lines on its own — 72% of the
entire 10,000-file baseline.** Deltas over that single file:

| lever | Δ lines |
|---|---|
| **SysEx** (GS reset / universal) | **+716** |
| **XG address sweep** | **+516** |
| **GS block addresses** | **+450** |
| **GS per-part addresses** | **+338** |
| the 18 meta types | +202 |
| karaoke (`@KMIDI KARAOKE FILE`) | +116 |
| universal SysEx (GM on/off, master volume) | +109 |
| the 7 channel-voice families × channels | +82 |
| undefined meta types | +74 |
| controllers 0–127 | +35 |
| running status, velocity 0, delta widths | +33 |
| programs / key signatures / format / tickdiv | +30 / +14 / +13 / +9 |

**The single most important finding**: `readmidi.c` contains complete **Roland
GS** and **Yamaha XG** SysEx dispatch trees — hundreds of lines each — and the GS
tree is gated on a **checksum** at `readmidi.c:2945`:

```c
for (i = 4; i < gslen-1; i++) checksum += val[i];
if (((128 - (checksum & 0x7F)) & 0x7F) != val[gslen-1]) return 0;
```

Get it wrong and the entire tree is skipped. The template computes it.
**1353 of 1353 GS messages in the corpus verify correct.**

---

## Expressed

### Constraints

**Tier A (all 27), each evil-bit guarded:** `MThd` and `MTrk`
(`= { "MThd" }` / `= { "MTrk" }`); `MidiHeader.m_seclen = { 6 }` (the template's
struct is a fixed six-byte body, so 6 is the only self-consistent value it can
emit — the JSON's own `template_parse_requirement`); `m_format` with all three
values, preferred 0/1 weighted by repetition; `MidiTrack.m_seclen` backpatched;
`meta_event.m_length` and `sysex_event.m_length` computed per type; the twelve
channel-voice data bytes, `DeltaTime.t3` and the key-signature pair.

**`meta_event.m_type` (the only Tier B entry):** all 18 values, with
`preferred_value` [47, 81, 88, 89, 1, 3] applied by repetition. **All 18 appear
in the corpus.**

### Dependencies — all 18

[0] the track count equals the chunks emitted (the loop counts and backpatches).
[1] format 0 is advisory — deliberately violated sometimes, as the JSON
recommends. [2] a negative tickdiv switches to SMPTE. [3] running status is legal
only once a status has been set — `canRun`. [4]/[9] FF/F0/F7 cancel running
status. [5]/[6] the two-data-byte families versus the one-data-byte
program-change and channel-pressure asymmetry, which the JSON flags as "the
asymmetry a generator is most likely to get wrong". [7] 0xFF opens a meta event.
[8]–[14] the seven specification lengths: EOT 0, tempo 3, SMPTE 5, time signature
4, key signature 2, sequence number 2, channel prefix / port 1. [15] the nine
text types take a free length. [16] SysEx carries an explicit length. [17] the
continuation-bit chain.

### Structure — all 13

MThd is a fixed head; tracks are a bounded loop; the first message of each track
carries an explicit status (`lastStatus`/`canRun` reset per track); each track
ends `FF 2F 00`; messages are contiguous; the track length is exact; no fifth
delta-time byte; the nine event branches are mutually exclusive; nothing follows
the final track.

**Three template mechanics worth naming.** (1) Value sets are applied **at a
lookahead**, not on the declaration — `ReadUByte(pos, set)` draws and plants, and
the bare declaration takes the byte. That was forced: the status and data bytes
are `char`, so a `vector<char>` set cannot hold 0x80–0xFF without a narrowing
error, and ffcompile silently **drops** a `<values=>` attribute on any declaration
inside an `if`/`switch`/`while`. (2) Every `m_type` comparison goes through a
local copy, because ffcompile mines `<field> == <const>` and would pin the Tier B
enumeration to one member — the original compares it eighteen times. (3) Both
lengths are **backpatched**, with loop conditions built as fixed points so a
re-parse walks the same messages and the backpatch becomes a no-op.

### `payload_wellformedness` — the one entry

**`sysex_event.m_message`** — MIDI System Exclusive (MMA MIDI 1.0). Every byte
has bit 7 clear except the terminating `0xF7`, and the length is computed from
the payload chosen, never the payload trimmed to a fixed length. Four real
manufacturer forms:

| variant | bytes | size derivation |
|---|---|---|
| **Roland GS Data Set** | `41 10 42 12 aa bb cc dd ck F7` | 10; address drawn from the sets TiMidity branches on, **checksum computed over `val[4..7]` per the GS spec** |
| **Yamaha XG Parameter Change** | `43 10 4C ah am al dd F7` | 8; `val[0]==0x43 && val[2]==0x4C` is TiMidity's XG gate |
| **Universal** (GM System On, Identity Request, master volume) | `7E/7F 7F ss dd F7` | 5 |
| free 7-bit body | `<n bytes> F7` | `n+1`, n from the message's own free delta time |

`m_length` is then planted with exactly that count, and
`m_message[m_length.total]` takes the planted bytes. In the 200-file corpus:
GS 1353, universal 630, free 590, XG 577.

### `diversity_axes` — all 12 confirmed

**Declared bare** (no value set, no `<min=>`, no `<max=>` — the Tier A/B sets are
applied at the preceding lookahead, the JSON's `lookahead` form):
`MidiHeader.m_ntracks` (line 114), `MidiHeader.m_tickdiv` (115),
`meta_event.m_usecPerQuarterNote` (295), `MidiHeader.m_seclen` /
`MidiTrack.m_seclen` (343, backpatched), `MidiMessage.m_status` (160),
`DeltaTime.t0` (126), `meta_event.m_type` (269), `note_on_event.m_velocity`
(187), `controller_event.m_controller` (204), `sysex_event.m_length`.

Also bare: every text payload, `m_seqNum`, `m_channelPrefix`, `m_port`, the five
SMPTE bytes, the four time-signature bytes, `m_data`, and the remaining eleven
data-byte fields. A grep for `<min=`, `<max=`, `generation_range`, `practical`,
`sensible` returns **zero**.

**Confirmed in the corpus** (200 files, 2044 tracks, 401,238 messages): all 3
formats (78/76/46); **all 115 legal explicit status bytes and all 112
channel-voice statuses**; **all 18 meta types**; delta times in all four byte
widths (376,201 / 23,458 / 1,481 / 98); running status on 48.9% of messages; 28
distinct track counts spanning 0–93; all four SysEx variants.

---

## Not expressed

- **The `output_budget` figures.** structure[3] asks for ~256 KB per file and
  structure[4] for ~64 KB per track. The engine caps any generated file at
  `MAX_FILE_SIZE` = 65536 and the random stream at `MAX_RAND_SIZE` = 131072,
  which at ~3–4 draws per byte binds first. 24,000 is the effective budget. It
  still stops the generator *adding messages and tracks*; no delta time, note
  value or payload length is trimmed to reach it.
- **The karaoke path, measured at +116 lines, deliberately forgone.**
  `readmidi.c:473` looks for a text meta event beginning `@K`, and free text never
  spells `@KMIDI KARAOKE FILE`. Planting it would mean writing specific bytes into
  `meta_event.m_text`, which is Tier C `unconstrained` — so it stays bare and the
  cost is reported instead. Same line taken on the PCAP port fields.
- **The SMPTE timebase is reachable but rare.** dependencies[2] is implemented
  (`m_tickdiv` is bare and signed, so both branches exist), but FormatFuzzer's
  bare-integer draw puts 87.5% of a `short` in 1..16, so only 4 of 200 files carry
  a negative tickdiv. Capping or biasing the field would violate
  diversity_axes[1], which names it explicitly.
- **Parse fidelity above 24,000 bytes.** The message and track loops carry the
  budget guard in their conditions, so a real MIDI file larger than that would be
  truncated on parse. Its own output round-trips 200/200, and the engine cannot
  generate anything larger.
- **The 94 baseline-only lines** are 73 in `readmidi.c`, 14 in `common.c` and 7
  elsewhere — error and resynchronisation paths the baseline reaches by emitting
  malformed chunk lengths and unguarded status bytes. Reaching them means breaking
  the structural invariants Tier A exists to protect.

**No Tier C field was narrowed to work around any of these.**

## Four bugs verification caught

- **The 24-bit tempo bitfield is broken under ffcompile.** The original declares
  `uint m_usecPerQuarterNote : 24;` then `FSeek(FTell()-1)` to drop the fourth
  byte. Measured: ffcompile writes the **whole four-byte storage unit** and does
  **not advance `FTell()`** until it flushes (`FTellBits()` = 32, `FTell()`
  unchanged), so that seek lands one byte *before* the field. Replaced with
  `ubyte m_usecPerQuarterNote[3]` — the three bytes the format defines and
  dependencies[9] requires, identifier kept, value still Tier C and free.
- **The forced end-of-track was planting its meta type one byte ahead**, and a
  byte already in the lookahead bitmap cannot be re-planted — the second plant
  silently loses and the stale byte wins. 1862 of 2022 tracks lacked an
  `FF 2F 00` tail. Moved the plant inside the meta branch behind a global flag.
- **The evil bit on the status byte was the real corruptor.** An out-of-set status
  draw below 0x80 while `lastStatus` is 0 makes the template take *none* of the
  nine branches, consume no payload, and leave a planted byte unconsumed — which
  then poisons the next plant and eventually the `MTrk` magic itself (a
  declaration over a bitmap byte is also restored to the stale value). Guarding
  every Tier A plant with `SetEvilBit(false)` took the structural defect count
  from 53 no-EOT + 7 broken chains to **zero**. The 13 values the evil bit draws
  are exactly the JSON's `excluded_values` — System Common and Real-Time messages
  not permitted in a file — so guarding is the correct Tier A treatment, not a
  loss of variety.
- **Randomness exhaustion.** `MAX_RAND_SIZE` is 131072 and generation consumes
  roughly 3–4 draws per byte, so the JSON's 64 KB-per-track / 256 KB-per-file
  budget aborted 45 of 200 files mid-track with "random size exceeded rand_size",
  leaving them truncated. The budget is now 24,000 bytes.
