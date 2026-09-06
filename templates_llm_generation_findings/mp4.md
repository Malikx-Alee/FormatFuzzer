# MP4 — `templates_originals/mp4-orig.bt` → `templates_llm/mp4-llm.bt`

Inputs: the original template and
`llm_learned_specification/llm_reterived_constraints_mp4-llm_opus5.json` (140
constraints, 54 dependencies, 22 structure rules, 14 template deviations, 8
schema extensions). `templates/mp4.bt` was never opened; the original under
`templates_originals/` is unchanged.

## Shape of the diff

807 → 1817 lines: **111 removals, 1121 additions**. All 196 declared identifiers
(structs, typedefs, fields, functions, enum members, switch case labels) survive.
Of the 111 removed lines, 110 are field declarations that come back with a value
set, a range attribute or a comment. **The only statement changed anywhere in the
file is one line**:

```
-while (FTell() < FileSize())
+while (!FEof(mp4EofP))
```

Everything else is additive: 480 comment lines, a 620-line generation-plan block
inserted between the enums and the helper functions, 59 value lists on field
declarations, 32 range attributes, 7 `<values=>` sets on bit fields, and two
calls inside `mp4box` (`mp4PlantHead` before the header and `mp4PlantBody`
after it).

## The central problem: a size-prefixed tree

Every box states its own byte count in its first four bytes, and that count
covers everything inside it. Nothing can be written until everything it contains
has been measured. The parse direction discovers the tree; the generate
direction has to decide it first.

`mp4BuildPlan()` lays out the whole tree in one pass and records, for every box
in the order the parser will meet it, the bytes that have to be exact: eight
header bytes, a content prefix, and one further exact run at a stated offset.
`mp4PlantHead()` writes the header just ahead of the read position and
`mp4PlantBody()` the rest, so every size, count, offset and cross-reference is
already correct the first time the parser looks at it. There is **no `FSeek`
backpatch and no `SetEvilBit(false)` anywhere in the file**.

A plant is a lookahead `ReadBytes` whose preferred and possible sets are both a
single computed image with `p = 1.0`: 255 times in 256 the image is written with
the evil bit suppressed for that call, and the remaining time the same set is
redrawn with evil restored — a net escape of about 1/32768 per plant. The same
call with a multi-entry menu picks uniformly from it *and* plants the choice,
which is where the generator gets its structural entropy.

### The plan runs in both directions, deliberately

The first version of this rewrite gated the planner on `IsParsing()`. It
generated correctly and it parsed real files, but it **broke FormatFuzzer's round
trip**: generate → parse → re-generate from the parsed decisions no longer
reproduced the file, because the two directions drew different numbers of random
decisions. `./build/mp4-llm-fuzzer test` failed on 8 of 10 real files.

The fix is the one the BMP rewrite already uses: run the planner unconditionally.
In the parse direction a plant simply reads the bytes that are there. When they
are the ones the plan expected — exactly the case for a file this template
generated — the reads cost the same decisions the writes did and the file
re-generates byte for byte. When they are not, the read falls through to a free
read of the actual bytes and the plan is ignored from there on.

The one thing that must never happen is a plant reaching past the end of a box,
so the split into `mp4PlantHead` / `mp4PlantBody` matters: the header plant is
eight bytes, exactly as safe as the header read the parser is about to make, and
the body plant is emitted **only once the header has come back the size the plan
laid down**. Only one variable stays gated on the direction — `mp4EofP` — and
assigning it draws no decisions.

Result: **10000 generate/parse/re-generate cycles, 0 round-trip failures.**

### Where the entropy comes from

Two menus, both planted on bytes inside the `ftyp` box whose value is free:

* the **box size** (offset 0..7), a menu of 8 — structure rule 20 makes the box
  size the only statement of the compatible-brand count, so picking it picks the
  brand count 1..8;
* the **minor_version** (offset 12..15), a menu of 16 — ISO/IEC 14496-12 4.3.3
  calls the field informative.

Between them they select the file's shape: progressive or fragmented, one track
or two, video first or audio first, edit list / sync-sample table / trailing
`free` box, uniform or per-sample `stsz`, coded frame size, frame rate, sample
count, fragment count, `sidx`, `pssh`, and the CENC boxes. Everything the plan
does not plant — brands, times where they are free, dimensions, flag bits,
graphics mode, language, quality — is drawn by the field declarations from their
own value sets, which is where the per-file variety lives.

## What was implemented, and how

### Constraints

* **`fixed_value` (29 entries)** — the nine `matrix.*` members, `preferred_rate`,
  `preferred_volume`, `volume`, `balance`, `media_rate`, `quality`, `mfr`,
  `flags_mask`, `scheme_version`, the `reserved*` fields and the two `dummy`
  arrays. Where the field is a plain scalar it carries `= { v }`
  (`uint32 mfr = { 0 }`, `uint16 quality = { 0 }`, `uint32 scheme_version =
  { 65536 }`). Where it is a struct instance whose type is shared — every `fp32`
  and `fp16` — the value cannot be attached to the instance, so the plan plants
  it: the 36-byte unity matrix, the 8.8 volume, the 16.16 rate.
* **`enumerated_values` (17 entries)** — `= { v1, v2, ... }` lists:
  `codingName`, `scheme_type`, `aux_info_type`, `default_is_protected`,
  `default_per_sample_IV_size`, `default_constant_IV_size`,
  `default_sample_info_size`, `version` (per arm, 0 or 0/1),
  `default_sample_description_index`, `sample_description_index`,
  `first_sample_flags`, `sample_flags`, `default_sample_flags`. The enum-typed
  `graphics_mode` gets `= { qtgCopy }`, which the JSON's `value_names` key asks
  for. `boxheader.type` is covered below; `major_brand` and
  `compatible_brand.brand` share `fourcc.value`, also below.
* **`range_constraint` (32 attributes)** — `<min=, max=>`, always the
  `generation_range` rather than the spec bound: `fp16.value` 0..256,
  `fp32.value` 65536..125829120, `time_scale` 1..90000, `timescale` 1..90000,
  `track_id`/`trackID`/`referenceID` 1..8, `duration`/`media_time` 0..600000,
  `sample_delta`/`sample_duration`/`default_sample_duration` 1..600000,
  `sample_size`/`default_sample_size` 0..65536, `sample_count` 1..256,
  `entry_count` 0..256, `num_entries` 0..16, `KID_count` 0..4, `DataSize`
  0..1024, `reference_count` 1..64, `sequence_number` 1..16, `first_chunk` and
  `samples_per_chunk` 1..64, `subsample_count` 0..16, `contentSize` 4..4096,
  `minor_version` 0..512.
* **`calculated_value` (55 entries)** — none is left free. Every box size, every
  `entry_count`, `sample_count`, `num_entries`, `reference_count`, `DataSize`,
  `KID_count`, every `chunk_offset`, `data_offset`, `saio offset`,
  `sequence_number`, `next_track_id`, `duration` and `entry_size` is derived from
  the measured layout and planted. `boxheader.size` is the head of that chain.
* **`bitmask_constraint` (11 entries)** — `mp4lang.value` gets
  `= { 0x55C4, 0, 32767 }` ('und' plus the two QuickTime readings);
  `first_sample_flags`, `sample_flags` and `default_sample_flags` get the two
  internally consistent whole-word values the JSON lists; the packed `str_sidx`
  words and every FullBox `flag[3]` are planted, because a uniform draw over a
  packed word is almost never a legal combination.
* **`pattern_constraint`** — `fourcc.value` becomes a 22-entry value list. See
  the limitations section for why it holds the brand set and not the box types.
* **`lookahead`** — the JSON's `comparison_sites` schema extension records that
  this template has no lookahead call at all and that the mineable literals are
  the two switch statements. The rewrite adds the missing call site: a
  `ReadBytes` over the 46 box types plus `"raw "`/`"sowt"` immediately before
  `fourcc type` in `boxheader`, with `const local string ReadBytesInitValues[0]`
  at the top so the per-call-site set wins.

### Dependencies

All 54 appear. The branch-shaped ones are already branches in the original and
gained a comment naming them plus, where useful, a value set: the `version`
width switches (6, 7, 8, 9), the `version`-selected `tenc` byte (10), the pssh
key list (11), the six `tfhd` flag bits and five `trun` flag bits (12–22), the
`saiz`/`saio` aux-info bit (23), the `senc` subsample test (24), the constant-IV
sentinel (25), the `saiz` per-sample table (27) and the `stsz` sentinel (28, 29).

The cross-record ones (31–37, 41, 43, 44) cannot be branches — they are equalities
between numbers written in different boxes — so the plan enforces them by
construction: the `stts` runs sum to the `stsz` sample count, the `stsc` runs map
exactly those samples into the chunks the `stco` table locates, the `stco`
offsets land inside the `mdat` payload, `next_track_id` is one past the largest
`track_id`, every `trackID`/`referenceID` names a `tkhd` that exists, the three
durations are one length in three time scales, and the `trun` data offset is the
measured distance from the `moof` to its `mdat`.

Dependencies 38/39/40 (handler subtype ↔ media header) are enforced by the plan
emitting `vmhd` with `'vide'` and `smhd` with `'soun'` from the same variable.
Dependency 50/51 (the `vmhd` flags word must be exactly 1, graphics mode 0,
opcolor black) are the three `<values=>` sets and two `= { 0 }` lists.
Dependency 53 (below 0x0400 the language field changes vocabulary) is what
`mp4lang.value`'s three-value list encodes.

### Structure rules

| rule | how |
|---|---|
| 0, 3 `ftyp` first | plan slot 0, planted at offset 0 before anything else |
| 1 exactly one `moov` | plan slot 1 |
| 2 at least one `mdat` | one per progressive file, one per fragment |
| 4 no terminator | nothing trailing is emitted; the last box's size reaches EOF exactly |
| 5 bound the top-level walk | `FEof(mp4EofP)` in place of `FileSize()` |
| 6 bound the child walk and the depth | the plan is a flat pre-order list, so both are finite by construction |
| 7 header then content, contiguous | content measured first, header written from the measurement |
| 8 one `mvhd`, first in `moov` | plan order |
| 9 ≥1 `trak`, unique non-zero ids | 1..2 tracks, ids 1..n |
| 10 the trak/mdia/minf/stbl chain | `mp4PlanTrack()` builds it innermost-first |
| 11 one `stsd`, one entry | `entry_count` planted as 1 |
| 12 `stsz` requires `stts`, `stsc`, `stco` | all four written from one sample list |
| 13 `stco` xor `co64` | `stco` only |
| 14, 15, 16 fragments | `mvex`+`trex` before any `moof`; sequence numbers 1..n; each `moof` immediately followed by its `mdat` |
| 17, 18 forbidden sizes | the plan never emits 0, 1, or 2..7 |
| 19 big-endian | `BigEndian()` untouched; every image is built big-endian |
| 20 brand count from the box size | the size menu is the brand-count menu |
| 21 one `hdlr` per `mdia` | plan order, subtype tied to the media header |

### Template deviations

All 14 are annotated on the code they describe and acted on where they change
what may be generated: version 0 only in `mvhd`/`tkhd`/`mdhd` (#2), an 8-byte
`senc` IV (#3), `senc` `flag[2]` exactly 2 or exactly 0 (#4), no `enca` (#5),
`str_stsd` left dead (#6), the two spellings of the flags field and of the aux
parameter treated as one (#7), the three unsigned-where-signed fields kept well
inside the positive range (#8), the two four-character codes emitted as their
big-endian integers (#9), every count capped (#10), and — the reason the plan
exists at all — sizes 0 and below 8 never emitted (#0, #1).

## What could not be expressed, and why

1. **`boxheader.type`'s 46-value enumeration cannot live on the field.** `fourcc`
   is one typedef with one `char value[4]` declaration, and ffcompile attaches a
   per-call-site value list to a *declaration*, not to an instance. That single
   list has to serve `boxheader.type`, `major_brand`, `compatible_brand.brand`
   and the two `hdlr` codes. It holds the brand set, because the brands are the
   only fourcc instances the plan does not plant. The box types are implemented
   twice over instead: as the planted type of every box, and as the 48-entry
   lookahead menu in `boxheader`.
2. **`mp4time.value`'s generation range does not fit.** `file_accessor` stores
   `<min>`/`<max>` in an `int`, and 3082844800 is past `INT_MAX`. Every creation
   and modification time is planted instead.
3. **One integer range per identifier.** ffcompile creates the global object for
   a field name once, so the first `<min=,max=>` it sees for a name wins and later
   ones are silently dropped. `sample_count` is declared in five arms with two
   different ranges, `entry_count` in eight, `duration` in three. The tightest
   range is attached at the first declaration and a comment says so; every other
   use is planted, so the loss is documentation-only. `fp32.value` and
   `fp32uvw.value` are worse — same name, same width, so they share one object.
   Resolved by planting every `fp32uvw` (all nine are inside the unity matrix)
   and giving the shared range to the `tkhd` width/height bound, which is the
   only unplanted `fp32` left.
4. **`default_crypt_skip_byte_block = 0x91` cannot be declared.** ffcompile maps
   `byte` to a signed `char` and 145 does not narrow into it. Two of the three
   enumerated values are declared and the third is named in a comment.
5. **A bit field cannot carry an init list.** `byte dummy2 : 4 = { 0 }` is a
   parse error in py010parser, and `file_integer` refuses a bit-field lookahead
   outright (`"bitfield lookahead not implemented"`), so a plant cannot reach
   them either. The four `tkhd_flags` bits and the two `vmhd_flags` bits use
   `<values=>` arrays, which is the only mechanism left.
6. **`co64` is unreachable.** Structure rule 13 makes it exclusive with `stco`
   and it exists only for files above 4 GB, which `MAX_FILE_SIZE` forbids. Same
   for `boxheader.size64` and the `size == 1` escape of dependency 0: both parse
   branches stay, neither is generated.
7. **`sinf`, `schi`, `schm`, `frma` and `tenc` are parse-only.** A protection
   scheme box lives inside an encrypted sample entry, and the template reads
   `stsd` entries as recursive `mp4box`es whose type the switch does not name —
   so the default arm skips the whole entry, `sinf` included. Putting a `sinf`
   anywhere the walk actually reaches would mean putting it somewhere ISO/IEC
   14496-12 does not allow. Their constraints (`codingName`, `scheme_type`,
   `scheme_version`, the whole `tenc` chain, dependencies 10, 25, 26, 48, 49)
   are declared on the arms; the CENC boxes that *are* legal where the walk goes
   — `pssh` in the `moov`, `saiz`/`saio`/`senc` in the `traf` — are generated.
8. **`enca` is not generated.** Template deviation 5: the arm reads a version,
   three flag bytes and an entry count that an `AudioSampleEntry` does not have.
   A valid `enca` would be mis-parsed by this arm; one shaped to satisfy the arm
   would be a file no demuxer accepts. The plan uses a plain `sowt` entry, which
   the default arm skips cleanly, and the `enca` arm keeps its annotation.
9. **`mp4box.base_data_offset` is deliberately absent.** It is a raw 64-bit file
   offset with no bounds check that would have to be back-patched; the JSON's own
   note says omitting it, so offsets default to the enclosing `moof`, is what most
   fragmented files do. The `tfhd` bit stays clear and the branch stays.
10. **`mp4box.width`/`height`'s generation range is honoured, but the coded frame
    size is not taken from it.** 0x01400000 is 320 pixels and an uncompressed
    320×240 frame is 230 KB of `mdat` — three and a half times `MAX_FILE_SIZE`.
    ISO/IEC 14496-12 8.3.2 says the track dimensions are the presentation size
    and "need not be the same as the pixel dimensions of the images, which is
    documented in the sample description", so the two are separated: `tkhd`
    width and height keep the JSON's range, and the sample entry carries a coded
    size of 8..32 pixels.
11. **`udta` and `skip`** appear in the type menu but carry no constraints of
    their own and would be pure filler, so nothing generates them.
12. **`str_stsd` stays dead.** The schema extension `unused_in_parse_flow` says
    so explicitly; the range is recorded on `contentSize` and the struct is left
    uninstantiated exactly as the original has it.

## A compiler collision worth recording

`ffcompile` gives the `trun` arm's anonymous per-sample struct **the same C++
class as the `senc` arm's**. Both are anonymous structs whose instance is named
`entry`, and pfp derives the class name from that instance alone
(`classname = field_name + "_struct"`), so the second one to be compiled reuses
the first. The compiled `trun` therefore reads `senc`'s fields — an 8-byte
`per_sample_IV`, and a subsample table when `flag[2] == 2` — instead of its own
four conditional ones. **The original has the identical collision**, so renaming
would be a behaviour change rather than an optimization.

The plan works around it without touching an identifier: `trun` flags
`0x000601` make a real entry a 4-byte `sample_size` plus a 4-byte `sample_flags`
— exactly the 8 bytes the compiled arm consumes — with `flag[2]` set to 1 so the
`senc` subsample branch stays shut. The file is then correct for a real demuxer
*and* self-consistent for this template. Before the workaround the container walk
printed a size mismatch on every fragmented file; after it, none.

## Verification

| command | result |
|---|---|
| `./ffcompile templates_llm/mp4-llm.bt /tmp/mp4-llm-check.cpp` | **exit 0**, "Finished creating cpp generator" |
| `./build_new.sh mp4-llm` | **exit 0** → `build/mp4-llm-fuzzer` 590,592 B, `build/mp4-llm.so` 590,536 B; 38 warnings per unit, 36 `-Wparentheses-equality` and 2 `-Wbraced-scalar-init` |
| `./build/mp4-llm-fuzzer fuzz /tmp/mp4-llm-out/f{1..200}.mp4` | **200/200 created, 0 failed**, no size-mismatch warnings |
| `./build/mp4-llm-fuzzer parse /tmp/mp4-llm-out/f1.mp4` | **exit 0**; 200/200 round-trip |
| `bash checkers/mp4.sh` | **exit 0** on f1; **199/200** re-encode under ffmpeg |

Sizes over the 200: min 787, median 4,182, mean 6,401, **largest 25,741 bytes**.

Beyond the required commands:

* **The original template parses all 200 generated files.**
* **Parse parity is exact.** Over 24 real files — the 10 in `testcases/mp4` plus
  14 built with ffmpeg covering H.264, MPEG-4, ProRes, AAC, ALAC, faststart,
  fragmented, DASH, rtp-hinted, `.mov`, `.3gp` and `.m4v` — the original and the
  rewrite accept the identical set, 24/24 each, 0 differing.
* **Round trip: `./build/mp4-llm-fuzzer test` — 9,985 files from 10,000 attempts,
  0 re-generation mismatches.** The baseline built from the original manages
  1 file from 2,480 attempts and then fails the comparison.
* **An independent conformance walker finds 1 structural violation in 200** and
  **4 in 1,997**, recomputing every box's size against its content, both tiling
  levels, the `stts`/`stsc`/`stsz` totals, the chunk offsets against the `mdat`
  extents, the duration conversions, `next_track_id`, the handler/media-header
  pairing, the `trun` sample-size sum against its `mdat`, the `saio` offset
  against the `senc` IVs, and the `sidx` size formula. All four are plant escapes.
* **Stress, 2,000 files: 1,997 generated** (3 plant escapes, all caught as
  `FSeek/FSkip: invalid position`, no crash and no large file), **1,982/1,997
  accepted by ffmpeg**. Of the 15 rejections, 14 are the *evil bit* firing on the
  `tkhd` width or height — a field the JSON marks `evil_bit_safe: true` — which
  gives ffmpeg a negative sample aspect ratio; 1 is a plant escape. The evil bit
  producing a near-miss file there is the intended behaviour, not a defect.
* **Census over the 1,997**: 1,024 progressive / 973 fragmented; 1,503 one-track
  / 494 two-track; 1,726 video / 765 audio tracks; 527 with an edit list, 398
  with a sync sample table, 1,007 with a trailing `free`, 1,019 with a `pssh`,
  504 with a `sidx`, 480 with the CENC trio. Every planned box type appears:
  `ftyp moov mvhd trak tkhd edts elst mdia mdhd hdlr minf vmhd smhd dinf dref
  stbl stsd stts stsc stsz stco stss mdat free mvex mehd trex sidx moof mfhd
  traf tfhd trun saiz saio senc pssh` plus the `raw `/`sowt` sample entries.

### Baseline, for comparison

Built from the unmodified original as `mp4-orig-baseline`: it parses 10/10 real
files, but of its own 200 generated files **0 parse**, **0 pass the checker**,
and the median size is 65 KB — it calls `FileSize()`, which in the generate
direction draws a uniform file length of up to `MAX_FILE_SIZE` and pads the whole
of it with random bytes before the first box is written.

### One known cosmetic warning

Parsing a generated file prints `Warning: unparsed (lookahead) bytes left at the
end of file`. The `mdat` payload is consumed by the default arm's
`FSkip(contentsize)`, which writes through the padding path and so never advances
`parsed_file_size`. The hard check, `file_size == final_file_size`, passes; the
round trip passes. Removing it would mean giving `mdat` a declared field, which
is a change to the parse direction rather than an optimization.
