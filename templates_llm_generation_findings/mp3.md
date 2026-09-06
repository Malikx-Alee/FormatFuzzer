# MP3 — `templates_originals/mp3-orig.bt` → `templates_llm/mp3-llm.bt`

Inputs: the original 010 template and
`llm_learned_specification/llm_reterived_constraints_mp3-llm_opus5.json`.
`templates/mp3.bt` was not opened. `templates_originals/mp3-orig.bt` is
byte-identical to `HEAD` (md5 `245313cd146656622b01b1d2a6607fdc`).

564 → 1099 lines: **108 removals, 643 additions, 400 of them comment lines**, and
all **78** declared identifiers preserved. No `Assert`, `Printf` warning or
`Warning` was deleted.

---

## Verification

| Command | Result |
|---|---|
| `./ffcompile templates_llm/mp3-llm.bt /tmp/mp3-llm-check.cpp` | **exit 0** (no `*ERROR:`/`*WARNING:` lines — this template validates with `Printf`, not `error_message`) |
| `./build_new.sh mp3-llm` | **exit 0** → `build/mp3-llm-fuzzer` (504,464 B), `build/mp3-llm.so` (504,408 B); 17 warning lines, all `-Wparentheses-equality`, 0 errors |
| `./build/mp3-llm-fuzzer fuzz /tmp/mp3-llm-out/f{1..200}.mp3` | **200/200 created, 0 failed** |
| `./build/mp3-llm-fuzzer parse /tmp/mp3-llm-out/f1.mp3` | **exit 0**; **200/200** across the set |
| `bash checkers/mp3.sh` | **cannot discriminate on this machine — see below** |

**Largest generated file: 11,850 bytes** — min 780, median 4,396, mean 4,746.

### The checker does not work here

`checkers/mp3.sh` is `mpg321 --stdout - <out.mp3`. On this machine mpg321 aborts
with SIGABRT (exit 134) on **every** input: the 200 generated files, 4 KB of
`/dev/urandom`, and every one of the 18 real LAME/ffmpeg-encoded MP3s in the
reference corpus. It is not distinguishing anything, so it is reported as
inconclusive rather than as 0/200. Validity was measured with the two decoders
that do work:

* **`ffmpeg -f null`** (strict — it refuses a file whose demuxer probe is not
  convincing): **156/200**, against **0/200** for the unmodified template.
* **`mpg123 -w /dev/null`**: 200/200 — but mpg123 also returns 0 for
  `/dev/urandom`, so it is not a discriminator either.

### Beyond the required commands

* **`./build/mp3-llm-fuzzer test 10000` → 10,000 round trips from 10,000
  attempts, 0 failures.**
* **18/18 real MP3 files parse**: mono and stereo, MPEG-1 and MPEG-2, 16 to 320
  kbit/s, 16 to 48 kHz, CBR and VBR, bare / ID3v2.3 / ID3v2.4 / ID3v1-appended,
  from both ffmpeg-libmp3lame and its Xing-less variants.

### Baseline (the unmodified original, built the same way)

| | original | rewrite |
|---|---|---|
| files created | 40/200 | **200/200** |
| own round-trip parse | 40/200 | **200/200** |
| real files parsed | **0/18** | **18/18** |
| `ffmpeg` accepts | 0/200 | **156/200** |
| `test 10000` | 2,479 | **10,000** |
| median / largest file | 10 B / 64,515 B | 4,396 B / **11,850 B** |

---

## The two things that had to be fixed before anything else

### 1. The original cannot parse a single MP3 file

Not "some" — none. FormatFuzzer's accessor keeps a bitmap of every byte a
**lookahead** has touched (`ReadBytes`, `ReadUShort`, `ReadByte`, `ReadUByte` all
write through it), and `file_integer` refuses outright — *"bitfield lookahead not
implemented"* — as soon as a marked byte overlaps a field declared with a bit
width. `MPEG_HEADER` is thirteen bitfields over one `uint32`, so a mark anywhere
in its four bytes is fatal. The original marks exactly those bytes twice over:

* the sync scan does `ReadUShort(seek_pos, data_values)` at every candidate frame
  position and then `FSeek(seek_pos - 1)` straight onto it;
* the ID3v2 probe does `ReadBytes(buf, 0, 3, buf_values)` at absolute offset 0,
  which is where the audio starts in a file with no prepended tag.

Both lookaheads are gone from the audio path, replaced by ordinary reads followed
by `FSeek`, which mark nothing:

* **the prepended tag** is detected by instantiating `ID3v2_TAG` unconditionally
  and rewinding to 0 when `hdr.head` is not `"ID3"` (structure rule 0,
  dependency 43). `head`'s value set is `{ "ID3", "\xff\xfb\x90" }` — the second
  entry is not a signature at all, it is the first three bytes of an MPEG frame
  header, and choosing it is how the rewrite says "this file has no tag". That
  also gives structure rule 5 its "about half the time": 106 of 200 generated
  files carry an ID3v2 tag.
* **the appended tag** is detected by re-assembling `MPEG_HEADER`'s first three
  bytes out of the bitfields that just read them and comparing with `0x544147`
  (structure rule 3, constraints[ID3v1_TAG.id]). The bit positions come straight
  from the JSON's `bitfield_layout` extension.

Lookahead is still used — seven `ReadBytes` plants — but only where every byte it
touches is read back by a char or `ubyte` array rather than by a bitfield.

### 2. Three pieces of arithmetic the template gets wrong

The JSON's instruction for a `template_deviation` is to follow the specification.
Three of them are load-bearing, because a wrong frame length puts the next sync
word in the wrong place and desynchronises everything after it:

* **template_deviation 4 — the mono halving.** Line 447 halves `frame_size` when
  `channel_mode == 3`; the template's own header comment lists it as a known bug.
  No such rule exists in ISO/IEC 11172-3. Removing it is what took real-file
  parsing from 0/18 to 7/8 in one step, and it is why
  constraints[MPEG_HEADER.channel_mode] can keep all four values.
* **the MPEG-2 Layer III bitrate table.** Dependency 4 gives it as
  8,16,24,32,40,48,56,64,80,96,112,128,144,160 kbit/s; the original's shift
  arithmetic yields 64 at index 5 where the standard says 40, and 80 at index 6
  where it says 48. Replaced with the table's own two-slope form. (This one is
  not in the JSON's deviation list — the entry for dependency 4 says the template
  "encodes it in the arithmetic on lines 410-427", which it does not.)
* **the MPEG-2 Layer III frame length.** MPEG-2 and MPEG 2.5 Layer III carry 576
  samples per frame, not 1152, so the constant is 72 rather than 144. The
  original uses 144 throughout and therefore doubles the length of every MPEG-2
  Layer III frame. Fixing this is what made the last real file parse.

**template_deviation 5** (a Layer I padding slot is four bytes, not one) is left
as it is and documented: Layer I is not generated, so it is unreachable.

---

## The evil bit, and why most of it had to go

The seven fields that decide a frame's length — `frame_sync`, `mpeg_id`,
`layer_id`, `protection_bit`, `bitrate_index`, `frequency_index`, `padding_bit` —
are all `evil_bit_safe: false` in the JSON, and the reason is sharper than it
looks. An out-of-pool value fails the template's own sanity check, the template
resynchronises **two bytes back**, and those two bytes survive as garbage between
two frames. That is exactly the break a decoder reports as *"failed to find two
consecutive MPEG audio frames"*.

Worse, the two-byte resync makes the generate and parse directions read
**different** four-byte windows: generation writes a header, rejects it, and
rewrites from two bytes on, while parsing reads the composite of the two attempts
as one header. That was worth 2 self-parse failures in 200 and it broke `test`
outright.

So the evil bit is suppressed across the whole length-critical run
(`SetEvilBit(mp3TagMode)` … `SetEvilBit(evil)`), and every pool in it therefore
has to cover every value a **real** file can carry, or the parse direction would
assert instead of escaping. That is why:

* `bitrate_index_values` lists all fourteen legal indices rather than a curated
  few, and is deliberately **not** pinned by `mp3Pin` — a variable-bitrate file
  changes it frame to frame. The generated stream is VBR as a result.
* `mp3Pin` narrows only the four stream-identity fields — version, layer,
  sampling frequency and channel mode — and only after the first frame has said
  what they are. That is structure rule 2's *"do not re-randomise version, layer,
  bitrate and frequency per frame"*, which is not advice: a decoder identifies
  the stream by finding two consecutive frames whose headers agree.
* `channel_mode` keeps its escape even so, because LAME switches between stereo
  and joint stereo from one frame to the next and the pin would break on the
  second frame of a real file.
* `mp3TagMode` puts the escape back once the frame budget is reached. Generation
  needs it there (the "TAG" pattern is written through the header pools, and the
  attempt has to be able to miss), and the parse direction needs it more: that is
  where a real file's appended tag turns up, and `"TAG"` read as a header is in
  none of the pools.

`private_bit`, `mode_extension`, `copyright`, `original` and `emphasis` keep the
escape throughout — none of them touches the frame length.

---

## What the JSON asked for, and where it is

### `constraints` — all 48 entries

`synchsafe_integer.raw` is planted (a `ubyte[4]` array takes no per-call-site
value list) from a menu the caller fills, selected by `mp3SynchSel`. The plant is
armed only once the `"ID3"` signature has matched, because a lookahead mark is
never cleared and `ID3v2_TAG` rewinds to 0 when it does not — four marked bytes
would otherwise sit frozen in the middle of the first MPEG frame.

`ID3v1_TAG`: `id` pinned with the evil bit off (the struct is only reached once
those three bytes have already been read and found to be `"TAG"`); `title`,
`artist`, `album` and both widths of `comment` get 30- and 28-byte value sets;
`year` gets `{"1999","2003","2021"}`; `zero` is 0; `track` is `<min=1, max=30>`;
`genre` gets the preferred 17 plus dependency 41's out-of-enum 255.

`ID3v2_HEADER`: `head` as above, `ver_major` `{3,3,3,4}` (dependency 19 diverts
anything else into an opaque blob), `ver_revision` 0, all three named flags and
the anonymous five-bit remainder pinned to 0, `size` planted from a six-entry
menu of tag sizes.

`ID3v2_EXTENDED_HEADER`: `size` pinned to 6 and `FLAG_CRC_PRESENT` to 0, which is
how dependencies 27/28 are satisfied given that the flag is declared *after* the
size it selects; `padding_sz` 0, which is exact because the frame loop fills the
tag body exactly.

`FRAME_FLAGS`: every named flag and both anonymous five-bit runs pinned to 0.

`ID3v2_FRAME` / `ID3v2_4_FRAME`: 16-entry identifier sets from the JSON's
`known_values`; the v2.3 size planted as a plain big-endian uint32 and the v2.4
size as a synchsafe integer — the difference that makes two frame structs
necessary; `id_asciiz_str` forced to 0 and `encoding` to 0 (ISO-8859-1), which is
also how dependencies 33 and 34 are satisfied, by never selecting an encoding
that imposes a BOM or a length parity.

`MPEG_HEADER`: eleven of the thirteen bitfields carry `<values=>` pools, listed
above. `MPEG_FRAME.mpeg_frame_data` is free except for its side-information
prefix — see below.

### `dependencies` — all 46

0/1 and 13 (MPEG 2.5 and the reserved version are unreachable because
`frame_sync` is pinned to 0xFFF); 2-5 (both frequency tables and both bitrate
tables, now that the MPEG-2 arithmetic is correct — 746 of 2,357 generated frames
are MPEG-2); 6-9 (the reserved layer, frequency, bitrate and emphasis values are
absent from the pools); 10/11 (the CRC field's presence — 306 of 2,357 frames
carry one); 12/13 (`mode_extension` pinned to 0); 14/15 (Layer II's bitrate and
channel-mode interlocks — vacuous, see below); 16 (the padding slot); 17-30 (the
whole ID3v2 tag: version-selected frame layout, the opaque-blob fallback, the
forbidden 0xFF version bytes, the extended header's presence and its size/flag
agreement, padding); 31-38 (text-frame encoding bytes, the UTF-16 BOM and parity
rules, and the three format flags whose prefix bytes neither frame struct
declares); 39-41 (the ID3v1.1 discriminator triple and the 255 genre); 42/43
(both tags' anchoring); 44/45 (at least one frame per tag, and the tag size
positioning the audio).

### `structure` — all 19

Rules 0-6 (the three top-level sections, their order and their cardinalities);
7-10 (the ID3v2 frame run and its padding); 11/12 (frames abut exactly, header
first); 13 (the ID3v1.1 triple); 14/15 (one frame layout per tag, blob or frames
but not both); 16 (nothing after the ID3v1 tag); 17 (the last frame must fit);
18 (Xing/VBRI — see below).

The audio loop is bounded by `FEof(mp3EofP)` with a frame budget of
`4 + bitrate_index` derived from the first frame, plus a hard 4096-iteration cap
and a progress test. Measured over 200 files: **5 to 18 frames, median 13**,
inside structure rule 2's 4-to-64 bound.

### `unnamed_bitfields` — all 4

`ffcompile` accepts a `<values=>` attribute on an **anonymous** bitfield, so all
four reserved runs are pinned to zero without inventing an identifier for them,
which the JSON's own schema note says the hard rules forbid.

### `lookahead_pools` — all 6

Pool 0 (`ReadByteInitValues`) is kept and joined by two per-call-site pools: one
that forces the ID3v2.3 text-encoding byte to 0, and one that plants the *first
letter* of the next frame identifier so `is_compatible_string` narrows that
frame's identifier set to the ones beginning with it. Pool 1 (`buf_values`) and
pool 2 (`data_values`) are the two removed lookaheads; both declarations are kept
with a comment. Pools 3-5 are the three the JSON calls wrong, and all three are
replaced — `mpeg_id_values` no longer contains a value a one-bit field cannot
hold, and `bitrate_index_values` no longer contains the two values the sanity
check rejects.

---

## What I could not express

**The frame payload is not audio.** `constraints[MPEG_FRAME.mpeg_frame_data]`
calls the content free, and for the main data it is — but the first bytes of a
Layer III frame are the side information, and a random one makes the decoder fail
on the frame it describes ("big_values too big", "invalid block type"). Zeroing
just that prefix — 17 bytes for MPEG-1 mono, 32 for MPEG-1 non-mono, 9 for MPEG-2
mono, 17 otherwise, planted and copied back — gives a structurally valid silent
granule and leaves the rest free. Producing genuinely decodable audio would need
an encoder, not a grammar.

**Neither checksum is computed.** `MPEG_HEADER.checksum` is CRC-16 with
polynomial 0x8005 and initial value 0xFFFF over the header tail *and the side
information that has not been written yet*; `bt.h`'s `Checksum()` offers only
CRC-8/16/32 with boost's reflected CRC-16/ARC, which is a different algorithm.
`ID3v2_EXTENDED_HEADER.crc` covers the frames and padding, which likewise do not
exist at the point the field is written. Both are emitted free; the JSON marks
the second `evil_bit_safe: true` for exactly that reason.

**Layer II and Layer I are not generated, and no longer parsed.**
`constraints[MPEG_HEADER.layer_id]` prefers 1, and the pool holds only 1. Layer I
would need a different frame-length identity (48 rather than 144) and a four-byte
padding slot, and MPEG-2 Layer II a third bitrate table, none of which the
template has. Because the pool is also what the parse direction accepts with the
evil bit suppressed, this narrows what can be read: a `.mp2` or Layer I file is
refused. That also makes **dependencies 14 and 15** — MPEG-1 Layer II's bitrate
and channel-mode interlocks — vacuous; they are recorded in a comment rather than
implemented.

**MPEG 2.5 is not supported**, which the original lists as TODO item 1 and the
JSON records as template_deviation 13. `frame_sync` is pinned to 0xFFF, so a
0xFFE file is refused rather than decoded with the wrong tables.

**`mode_extension` is pinned to 0 rather than narrowed by `channel_mode`.**
`channel_mode` is declared first, so dependency 12 could in principle be
expressed by rewriting the pool between the two declarations — but a statement
inside a bitfield run puts pfp's `BitfieldRW` into an invalid state and ffcompile
aborts. 0 satisfies dependency 12 for every channel mode and is the
specification's own value for the three non-joint ones; dependency 13's four
joint-stereo alternatives are not reachable.

**Structure rule 18 (Xing / Info / VBRI) is not emitted.** The convention has no
field in this template — the bytes fall inside `mpeg_frame_data` — and the rule's
own `generation_note` says to omit it unless generating VBR with seek support.

**Two ffcompile limits shaped the file and are worth recording.** py010parser's
string-literal rule backtracks exponentially on a long run of `\x00` escapes and
hangs the compiler outright at about twenty of them, which is why the ID3v1 text
fields are space-padded (the JSON's pattern admits 0x20) rather than NUL-padded.
And `ffcompile` lifts every `local` into one global namespace, so two functions
that both declare `r` share it and a self-referential concatenation
`r = r + f()` silently aliases — the zero-padding helper returned an empty string
until each helper's locals were given distinct names.

---

## Coverage of the generated corpus (200 files, 2,357 frames)

* ID3v2 present in 106 files (77 version 3, 28 version 4); ID3v1 present in 93
* MPEG-1 1,611 frames / MPEG-2 746; Layer III throughout
* channel mode stereo 644, joint 638, dual 258, mono 817
* CRC-protected frames 306 of 2,357
* **all fourteen bitrate indices** used, 9 (128 kbit/s) weighted ×3
* all three sampling-frequency indices: 1,238 / 547 / 572
* 5 to 18 frames per file, median 13
