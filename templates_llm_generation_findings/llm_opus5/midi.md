# MIDI — `templates_originals/midi-orig.bt` → `templates_llm/midi-llm.bt`

Generative rewrite of the 010 Editor Standard MIDI File template for FormatFuzzer,
driven by `llm_learned_specification/llm_reterived_constraints_midi-llm_opus5.json`
(54 constraints, 46 dependencies, 19 structure rules, 14 template deviations).

Inputs were exactly those two files. `templates/midi.bt` was not read;
`templates_originals/midi-orig.bt` is unmodified (`git diff --quiet` confirms it).

261 lines in, 711 out. The diff is 32 removals and 470 additions; every removal is
a field declaration replaced by the same declaration carrying a value set, apart
from three structural lines called out below, and all 85 struct, field and enum
identifiers of the original are still present.

---

## Verification results

| Command | Result |
|---|---|
| `./ffcompile templates_llm/midi-llm.bt /tmp/midi-llm-check.cpp` | **exit 0**, "Finished creating cpp generator" |
| `./build_new.sh midi-llm` | **exit 0** → `build/midi-llm-fuzzer` (466,704 B), `build/midi-llm.so` (466,648 B); 66 warnings, all `-Wparentheses-equality` from ffcompile's own output |
| `./build/midi-llm-fuzzer fuzz /tmp/midi-llm-out/f{1..200}.mid` | **exit 0**, 200/200 files, no assertion retries |
| `./build/midi-llm-fuzzer parse /tmp/midi-llm-out/f1.mid` | **exit 0**; **200/200** of its own output round-trips |
| `bash checkers/midi.sh` | **exit 0** on f1; **200/200 PASS** over the whole batch |

**Largest generated file: 402 bytes** — min 48, median 155, mean 172. Nothing
approaches the "few hundred KB" threshold: a file is at most four tracks of at
most fifteen events each, with meta and SysEx payloads capped at twelve bytes.

Beyond the required commands:

* **200/200 of the generated files are strictly conforming Standard MIDI Files**
  under an independent walker written from SMF 1.0 — 419 track chunks, every one
  ending in its End of Track event, every declared chunk length matching the bytes
  actually present, no trailing bytes, and not one ordering violation of any of
  S09–S13 or S15.
* **Parse parity against 323 files: the original parses 147, the rewrite 144.**
  The corpus is the repo's 6 real `testcases/midi/*.mid`, 17 conforming files
  synthesised to exercise features the real six lack (running status, every meta
  type, both SysEx forms, 1–4 byte variable-length quantities, formats 0/1/2,
  SMPTE division), and 300 files from `output/midi/*/valid/`. **All 23 conforming
  files parse identically under both.** The three differences are all in the
  third group, which is machine-generated near-random bytes that timidity happens
  to accept; each has a stray End of Track event in the middle of a track, which
  the rewrite treats as the end of the chunk (S05/D44).
* Feature census over the 200 files: all three formats (60 / 118 / 22); metrical
  and SMPTE division (172 / 28); 1–4 tracks; 1404 running-status events; all seven
  channel voice message types plus 276 SysEx events; **all eighteen meta-event
  types the enum declares**, including the `META_SEQUENCER_EVENT` fallback the
  original never dispatches; 3343 one-byte and 1843 two-byte variable-length
  quantities; 163 of 165 Set Tempo values inside 40–240 BPM.

---

## What I implemented

### The track envelope, which is where this format bites (C49, D43, S04, S06, DEV04)

`local uint remaining = m_seclen;` decremented by `sizeof(message)` inside
`while (remaining)` is not merely a mis-parse risk. `remaining` is unsigned, so an
overshoot of one byte wraps it towards 2^32 and the loop runs essentially forever —
which is exactly what happens if a generator picks a chunk length before the events
exist. The length is therefore **back-patched**: the field is written as a
placeholder, the events are generated, and the measured length is seeked back to
and rewritten with the evil bit off. The placeholder cannot be planted, because a
byte carrying a lookahead mark is copied back out of the buffer on every write path
and could never be rewritten; it is given a 4096–65535 generation range instead, so
`remaining` always starts far larger than any track this template emits.

The loop gains one extra condition, `!midiEotSeen`. During generation `remaining`
is still the placeholder and cannot end the loop, so the End of Track event is what
bounds it — which S05 requires to be the last event of the chunk anyway. During a
parse of a conforming track the two conditions coincide exactly, because that same
event is where `remaining` reaches zero.

### The status byte, which is where the format desynchronises (C10, D06–D18, S16)

The original reads an unconstrained byte and dispatches on it. Generating that
writes a random status, and thirteen of the sixteen `0xFn` values are System Common
or System Real Time codes that SMF gives no file encoding at all — the template
routes every one of them to `sysex_event` and reads a length field that is not
there. The status byte is now planted from a menu rebuilt before every event, and
the menu encodes the running-status rules directly: an explicit status at the start
of every track (S09, D17) and after every meta or SysEx event (S10, D18), because
those cancel running status and the original never clears `lastStatus` (DEV06).
Zero running-status violations appear in the 200 generated files.

### Everything that depends on something else

`m_format` and `m_ntracks` are planted as a **pair**, so D00 (format 0 is by
definition one track) holds by construction and cannot be violated by two
independent draws; format 1 is never given fewer than two tracks, because S13 makes
its first track a tempo map that carries no channel voice events, and a one-track
format 1 file would hold no music. The meta-event type menu is likewise selected
from state: Sequence Number only as a track's first event (S11), Copyright Notice
only as the first event of the first track (S12), the timing meta-events only in a
format 1 tempo map (S13), and Set Tempo never in timecode mode, where delta times
are already absolute subdivisions of a second (D37). Inside `controller_event` the
value byte branches on the controller number just drawn, which is D19, D20 and D21
as three arms of an `if` rather than three post-hoc checks.

Every meta-event length is derived from the type rather than drawn: 2, 1, 1, 0, 3,
5, 4, 2 and 4 for the fixed-shape types (D23–D30, D32), and 12 for the nine
text-carrying types, which are the only ones D31 leaves free.

---

## Two design decisions worth your attention

### 1. Padded bitfields make `FTell()` lie, and every lookahead is placed by `FTell()`

`uint m_usecPerQuarterNote : 24` is a 24-bit field of a `uint`. With 010's default
padded bitfields it claims four bytes of storage and leaves eight bits pending that
`write_file_bits` does not flush — `file_pos` is not advanced at all, so `FTell()`
keeps reporting the position where the field *started*. The original compensates
with `FSeek(FTell() - 1)`: the flush that happens on the next ordinary write then
lands four bytes on from there, which is three bytes on from the tempo value, which
is correct. It works, but only because the original never asks `FTell()` anything
in between.

This rewrite asks constantly — every plant is placed at `FTell()`. So after a Set
Tempo event every subsequent lookahead landed four bytes early, on top of bytes
already written, and the deferred flush eventually covered a byte that a plant had
marked, at which point `file_integer` aborts with *"bitfield lookahead not
implemented"*. 85 of 200 files failed that way before I found it.

`BitfieldDisablePadding()` makes the 24-bit field occupy exactly the three bytes the
format defines. There is then nothing pending, `FTell()` is accurate, the
compensating rewind is deleted, and the net effect on a parse is identical — three
bytes consumed either way. The fix is also what DEV07 asks for in its own words:
*"Emit exactly three big-endian bytes for the tempo value."*

### 2. A plant is exact in both directions, but only where a plant is possible

`ReadBytes(peek, pos, n, pref, pref, 1.0)` writes the preferred value with the evil
bit switched off 255 times out of 256 and marks the bytes in the lookahead bitmap,
so the field declared over them is forced to that value even when its own evil roll
fires — `file_integer` copies a bitmap-marked byte back out of the buffer on every
path, including the evil one. Parsing is untouched, because a real file whose bytes
differ leaves no compatible candidate and `file_integer` short-circuits on that
*before* it consults the evil bit. That is what lets the field declarations stay
byte-for-byte identical to the original while still generating exactly: `char t0;`,
`char m_status;` and `char m_magic[4];` are unchanged, and the plant above each one
does the work.

The corollary is that a plant is a positional commitment. Two of them cost me a
morning: the status byte was initially planted at the message start, on top of the
delta time it should have followed, which produced tracks consisting of nothing but
delta times; and the twelve-byte text payload plant had to be given a *type* guard,
not just a length guard, or a stray length on a Set Tempo event would put a mark on
the one field in the format that cannot carry one.

---

## What I could not express

**pfp silently drops `<values=>` and `<min=>`/`<max=>` from any declaration inside
an `if` block, and a bitfield cannot take an init list at all.** `= { ... }` init
lists survive inside conditionals; attributes do not. `uint x : 24 = { 500000 };` is
a parse error outright. Between them that leaves a bitfield inside a conditional
branch — which is precisely where `m_usecPerQuarterNote` lives — with no way to
constrain it where it stands. The workaround is that integer ranges are registered
per variable *name* on the field's first declaration and stored in the generated
object rather than passed at the call, so declaring the field once at struct top
level, where the attribute survives, applies the range to the real declaration too.
The template does this in `MidiHeader` for the tempo range, and reuses the same
mechanism for the track length placeholder — `m_seclen`'s range attribute sits on
the header's declaration of that name and describes the track's.

**The tempo value cannot be planted either**, only ranged: `file_integer` asserts
the moment the lookahead bitmap covers a bitfield, and the bitmap check spans the
whole four-byte storage unit, so even a three-byte plant over the value would trip
it. It therefore keeps a 1-in-128 evil escape, which is 2 of the 165 tempo events
in the sample.

**Two of the four SMPTE division combinations D05 lists are generated, not all
four**, and delta times are not rescaled when timecode mode is chosen. S14 notes
that the choice of mode changes what every delta time in the file means; deriving
the delta-time bound from the division would need the division to be visible at the
point each delta time is chosen, which it is, but the tick-per-frame arithmetic
buys no structural coverage over the metrical path.

**Delta-time selection is deterministic given the event index**, not random. All
randomness in a FormatFuzzer template has to come out of a generated field, and the
delta time is the *first* thing in an event — there is no earlier field to draw
from. Every fifth event therefore uses a two-byte quantity and the rest step
through 12, 24, 36 ticks, which exercises both encodings and the continuation-bit
dependency (D38, D39) but does not sample them. Values congruent to 0 modulo 128
are avoided as well, because `SPrintf` builds the planted encoding and cannot
produce a string with an embedded NUL; the one value that needs one, zero itself,
has a constant.

**Text payloads are twelve printable characters drawn from five fixed strings.**
D31 leaves these lengths genuinely free, and the plant that keeps them printable
per SMF 1.0's recommendation is what fixes the length — a variable-length plant
would need one string constant per length.

**`m_ntracks` is clamped rather than trusted.** DEV01 records that the field is a
signed `short` where SMF 1.0 defines an unsigned 16-bit count, so a count above
32767 becomes a negative array bound in the original. The rewrite clamps a negative
count to zero and an absurd one to one before using it as the bound. A count of
zero is passed through unchanged, because a header-only file is something the
original accepts and 25 files in the corpus rely on it.

---

## Incidental finding

`checkers/midi.sh` is `! timidity - -Ol -o /dev/null <out.midi 2>/dev/null | grep -q ^-:`
— note `out.midi`, not `out.mid`, and note that it passes whenever timidity prints
no line beginning `-:`. It is a real decode test (garbage and empty input both
fail it), but it says nothing about whether a track's declared length matches its
contents, because timidity resynchronises on the next `MTrk`. The 200/200 above is
corroborated by the independent conformance walk described earlier, which does
check that.
