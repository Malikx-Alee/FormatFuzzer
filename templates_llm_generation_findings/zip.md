# ZIP — `templates_originals/zip-orig.bt` → `templates_llm/zip-llm.bt`

Inputs: `templates_originals/zip-orig.bt` and
`llm_learned_specification/llm_reterived_constraints_zip-llm_opus5.json`.
`templates/zip.bt` was not opened. The original is unmodified.

Diff shape: 669 → 1179 lines, 60 removals / 570 additions. All 751 identifiers from the
original survive. Fifty-nine of the sixty "removals" are field declarations that gained a
trailing comment on the same line; the sixtieth is `while( !FEof() )`, which became
`while( !FEof( zipEofP ) )`. Two calls were added inside the loop body. Nothing else in
the original's structure changed.

## Verification

| Command | Result |
|---|---|
| `./ffcompile templates_llm/zip-llm.bt /tmp/zip-llm-check.cpp` | exit 0, "Finished creating cpp generator" |
| `./build_new.sh zip-llm` | exit 0 → `build/zip-llm-fuzzer` (559,920 B), `build/zip-llm.so` (559,864 B); 54 warnings, all `-Wparentheses-equality` |
| `./build/zip-llm-fuzzer fuzz /tmp/zip-llm-out/f{1..200}.zip` | exit 0, 200/200 created, no failures |
| `./build/zip-llm-fuzzer parse /tmp/zip-llm-out/f1.zip` | exit 0; 200/200 of the batch round-trips |
| `bash checkers/zip.sh` | exit 0 on f1; **200/200 PASS** — `unzip -P '' -t` verifies every entry's CRC |

**Largest generated file: 3,508 bytes** — min 22 (a valid empty archive), median 1,015,
mean 1,063.

Beyond the required commands:

* **The original template parses all 200 generated files.** That is the sharpest available
  check that the rewrite still speaks the grammar it was derived from.

* **An independent ZIP conformance walker finds 0 violations in the 200 files.** It
  re-derives every quantity from APPNOTE rather than trusting the generator: the end record
  is last with nothing after its comment; `elEntriesOnDisk == elEntriesInDirectory ==` the
  number of local headers walked; `elDirectoryOffset` is exactly where the local entries
  end and `elDirectorySize` exactly the measured directory length; every extra field
  decomposes into whole records summing to the declared length; a Zip64 record is 16 bytes
  with both 32-bit sizes at `0xFFFFFFFF` and a version of at least 45; an NTFS record is 32
  bytes with `Reserved` 0, `Tag` 1 and `Size` 24; a Unicode path record carries version 1,
  the **CRC-32 of the header's own filename**, and that same name; a stored entry's two
  sizes are equal and a deflate entry's differ by exactly the five-byte RFC 1951 block
  header, whose `LEN`/`NLEN` pair is checked; **every `frCrc` is recomputed from the
  payload and compared**; a name ending in `/` has both sizes zero; and all nine
  central-directory copies of a local field match, with `deHeaderOffset` pointing at the
  local header's signature, `deVersionMadeBy >= deVersionToExtract`, and the external
  attributes drawn from exactly the namespace the host-OS byte selects. When a Zip64 tail is
  present it checks the record's size field, its counts, its offsets, and that the locator
  points back at the record's signature.

* **Parse parity is exact.** Over the 233 real archives in `testcases/zip`,
  `testcases_4_learn/zip` and `coverage_targets`, the rewrite accepts and rejects **the
  identical set** as a baseline built from the untouched original: 193/233 each,
  **0 files differing** in either direction. (`output/zip*` holds no generated corpus.)
  Of the 40 both reject, 3 exceed FormatFuzzer's `MAX_FILE_SIZE`.

* **Census over 200 files:** archives of 0 to 6 entries, including 24 valid empty archives
  of exactly 22 bytes; 402 stored and 299 deflate entries; 150 Zip64 entries and 37
  archives carrying the Zip64 end record and its locator; 17 directory entries and 684 file
  entries; 572 entries using the DOS attribute namespace and 129 the Unix one; 21 archive
  comments; and every extra-field shape the template models —
  none 98, extended timestamp 132, NTFS 113, timestamp+NTFS 124, Unicode path 84, Zip64 150.

## What I implemented

### The problem this format poses

A ZIP is written forwards and read backwards. Every length in a local header precedes the
bytes it measures, the central directory is a second copy of nine fields per entry plus the
archive's only pointers, and the end record — which an extractor finds first, by scanning
backwards — carries the directory's offset and size. The original template walks all of
this as a flat forward stream and, as template_deviations #11 records, never follows a
single one of those pointers, so nothing in it constrains them.

The rewrite answers this the same way as the rest of this series: **`zipPlanEntry()`,
`zipDirImage()` and their siblings choose one complete layout and plant every header byte
through ffcompile's lookahead**, so each length, offset and count is right the first time
it is written. Because a ZIP's cross-references all point *backwards* — the directory is
written after the data it indexes, and the end record after the directory — every plant is
a forward plant at `FTell()`, with exactly one exception.

**That exception is the CRC.** `frCrc` sits at header offset 14, fourteen bytes before data
that does not exist yet and is deliberately random. It is the one field left unplanted when
the header goes down, and `zipAdvance()` back-plants it from
`Checksum(CHECKSUM_CRC32, …)` once the payload has been written — a plant rather than an
`FSeek`-and-rewrite backpatch, so it needs no `SetEvilBit(false)` and cannot make the parse
direction reject a file it used to accept. `unzip -t` verifies exactly this number, which is
why the checker passes on every file.

### Constraints

* **The seven signatures (`fixed_value`, `evil_bit_safe: false`)** — planted at every record
  boundary. The dispatch at the top of the loop peeks the same four bytes with `ReadUInt`,
  so the plant is what drives it; a `SetEvilBit(false)` init list on the field could not
  help, because the peek happens first.
* **`frVersion` / `deVersionToExtract` / `deVersionMadeBy`** — 20, raised to 45 for a Zip64
  entry (dependency 12), with `deVersionMadeBy >= deVersionToExtract` (dependency 39) and a
  **zero high byte** on both "version needed to extract" fields, which is
  template_deviations #8: `VERECORD` types that byte as a host-OS code where APPNOTE
  reserves it.
* **`frFlags` / `deFlags`** — 0. Bit 3 would demand a data descriptor (see below) and bits 0
  and 6 an encryption header this generator cannot fill in.
* **`frCompression`** — `COMP_STORED` (the preferred value) or `COMP_DEFLATE`.
* **`frFileTime` 0, `frFileDate` 33** — the JSON's single-value sets; 0x0021 is 1980-01-01.
* **`frCompressedSize` / `frUncompressedSize`** — planted as one eight-byte pair, so
  dependency 9 (a stored entry's two sizes are the same number) holds by construction and so
  does the five-byte overhead of a deflate block.
* **`frFileNameLength`, `frExtraFieldLength`, `deFileNameLength`, `deExtraFieldLength`,
  `deFileCommentLength`, `dsDataLength`, `elCommentLength`** — every one measured from the
  bytes actually built, never drawn.
* **`deDiskNumberStart`, `elDiskNumber`, `elStartDiskNumber`, `el64DiskNumber`,
  `el64StartDiskNumber`, `elStartDiskNumber` (Zip64 locator)** — 0, the only value a
  single-volume archive can carry.
* **`elr64DirectoryRecordSize`** — exactly 44, the one size that yields the conforming field
  set and an empty `DataSect` (template_deviations #6).
* **`ZIP64ENDLOCATOR.elEntriesInDirectory`** — 1. template_deviations #7: APPNOTE calls this
  the total number of *disks*, not an entry count, so writing the file count here would claim
  a multi-volume archive.
* **`EXTRAFIELD.efVersion` 1, `Reserved` 0, `Tag` 1, `Size` 24** — the fixed values of the
  records the generator emits.

### Dependencies

* **9** (stored ⇒ the two sizes are equal) and **10** (deflate ⇒ a real RFC 1951 stream) —
  both hold. A deflate entry's payload is a **final stored block**: `01`, the length, and
  its one's complement, followed by the literal bytes. It is the only deflate stream
  producible without a compressor, it inflates to exactly `frUncompressedSize` bytes, and
  its CRC is taken over the inflated bytes, not the block.
* **11, 12, 13, 47 (Zip64)** — a Zip64 entry sets both 32-bit sizes to the `0xFFFFFFFF`
  escape, raises the version to 45, and carries the Zip64 extra field as its **only** record
  so that the scalar read at line 628 refers to it (template_deviations #3). The extra
  field's `efCompressedSize` is the byte count the top-level loop then `FSkip`s, which is
  dependency 47 and the only thing keeping the walk in step.
* **14, 15, 16, 17, 18 (extra-field sizes)** — the Unicode path record is `5 + name length`;
  the NTFS record is 32, being four reserved bytes and one Tag-1 attribute of exactly 24;
  the Zip64 record is 16; the AES record's 7 and the strong-encryption record's minimum of 8
  are annotated on their branches but not emitted.
* **19, 20, 21, 22 (key length must match algorithm)** — annotated on both the extra-field
  and decryption-header forms; not emitted, since neither branch can be generated.
* **23, 24 (the extra-field length must decompose exactly)** — the enclosing length field is
  the measured sum of every `(efDataSize + 4)` built, which is what the `while (len > 0)`
  walks at lines 407-411 and 502-506 require; they have no other termination condition.
* **25 (a zero-size record is legal)** — the "none" case emits `frExtraFieldLength` 0 and the
  walk is skipped entirely.
* **26 to 33 (nine fields stored twice)** — `zipDirImage()` reads every one of them out of
  the same planner arrays the local header was built from, so the two copies cannot drift.
* **34 (identical names)** — both call `zipNameOf()`.
* **35, 36 (the end record's counts and size)** — taken from the entry count and the measured
  directory length, with `elDirectoryOffset + elDirectorySize` landing exactly on the end
  record.
* **37 (`deHeaderOffset`)** — the recorded absolute offset of the matching local header.
* **38 (the attribute namespace)** — the host-OS byte of `deVersionMadeBy` selects it:
  `OS_FAT` gets DOS bits (`FA_ARCHIVE`, or `FA_DIRECTORY` for a directory entry) and
  `OS_Unix` gets a `st_mode` in the high sixteen bits (`0100644`, or `0040755`). This is
  template_deviations #14, which warns that the `FILEATTRIBUTE` enum mixes two disjoint
  namespaces; the walker confirms no file mixes them.
* **40 (a directory entry)** — a name ending in `/` with **both** sizes zero, which also
  rules out the deflate form, since even an empty stored block is five payload bytes.
* **42, 43, 44 (the Zip64 tail)** — the record, its locator and the classic end record are
  emitted together in that order, the locator pointing at the record's signature, and the
  classic record keeps the real counts because they fit in 16 and 32 bits.
* **45 (the extensible data sector)** — `elr64DirectoryRecordSize` is 44, so `DataSect` is
  empty.
* **46 (the seven top-level signatures)** — the loop's tagged union, unchanged.

### Structure rules

* **first_element / last_element / required / ordering** — the record sequence is local
  entries, then the whole central directory, then the optional Zip64 pair, then the
  mandatory end record with nothing after its comment. The **empty archive is generated as a
  first-class shape**, one file in eight: the first record's signature is planted from a
  menu holding `PK\x03\x04` and `PK\x05\x06`, which is exactly the structure rule's "an
  empty archive is the one exception and begins directly with the end-of-central-directory
  record". 24 of the 200 files are the resulting 22-byte archive.
* **cardinality (the top-level loop, 1 to 8 entries)** — the loop is bounded by the planned
  record sequence rather than by `FEof`'s coin flip; see below.
* **contiguous (both header groups)** — a local entry's name, extra field and payload are
  planted as one image, and a directory entry's name, extra field and comment likewise.
* **cardinality (the extra field, 0 to 4 records; the NTFS chain)** — at most two records per
  header and at most one attribute per NTFS record, sized as the rule's own generation_note
  prescribes.
* **mutually_exclusive (the four payload layouts)** — only the plain branch is generated.
* **forbidden (trailing bytes, unknown signatures)** — nothing follows the end record, and
  the original's `Warning` + `return -1` arm is kept; it is what catches a corrupted
  signature during generation too.
* **ordering (endianness)** — `LittleEndian()`, and every planted literal is written low byte
  first. The signatures are planted as `"PK\x03\x04"` and friends, i.e. in reading order.

### The one statement change

`while( !FEof() )` → `while( !FEof( zipEofP ) )`. `FEof`'s probability argument is the loop's
only lever. `feof()` returns 0 without consuming a decision whenever `file_pos < file_size`
and consults randomness only at the true end. In parsing, `p = 0.0` makes it **exact**: the
parse lambda yields 255 at end of file and 0 elsewhere, and the threshold `255 * (1 - 0)`
separates them perfectly. In generation, `p = -1.0` puts the threshold at 510, out of
`rand_int(256)`'s reach, so the walk cannot end early; `zipAdvance()` sets `p = 1.0` after the
end record, which puts the threshold at 0 and ends it exactly there. Leaving the default
`p = 0.125` would truncate the archive one time in eight at *every* record boundary.

## What I could not express, and why

* **The data descriptor cannot be generated, only parsed.** `FindFirst` behaves completely
  differently in the two directions: parsing, it searches the input for the descriptor
  signature; generating, `file_acc.final_file_size` is 0, so it instead **plants** the
  signature at `start + rand_int(16)` — a payload length chosen at random by the runtime,
  which no plan can accommodate — and one call in 128 returns −1 outright while another one
  in 128 widens the range to `MAX_FILE_SIZE`. A descriptor entry would therefore desynchronise
  or produce a 64 KB file about 1.6% of the time. The JSON reaches the same conclusion from
  the other direction: the ordering rule for `ZIPDATADESCR` says "prefer not to use
  descriptors at all: emit the sizes and CRC in the local header with flag bit 3 clear, which
  removes a whole record and a FindFirst search from the parse". Both branches are kept for
  parsing; dependencies 6, 7 and 8 and the four `ZIPDATADESCR` constraints are annotated but
  unexercised. The alternative — flag bit 3 with *non-zero* header sizes, so the descriptor
  becomes a top-level record — generates safely and `unzip` accepts it, but it violates
  dependency 7 outright, so I did not take it.

* **The digital signature record is not generated.** It builds and the original template
  parses it, but `unzip` rejects the archive: it insists that
  `elDirectoryOffset + elDirectorySize` lands on the end record, whereas dependency 36's own
  note allows it to land on the digital signature record instead. Folding the signature's
  bytes into `elDirectorySize` makes `unzip` accept (return 1, a warning), but that
  contradicts the same dependency's primary reading — "the total byte length of every
  ZIPDIRENTRY record". Faced with two incompatible readings I kept the arithmetic exact and
  omitted the record; its parse branch and its two constraints stay.

* **Encrypted entries are not generated.** Both encryption layouts need real cryptography:
  the strong-encryption branch needs a decryption header whose `VCRC32` validates, and the
  WinZip AES branch needs a salt, a password verifier and an HMAC authentication code that
  `unzip -P ''` would have to reproduce. `unzip` 6.0 does not implement AES at all and exits
  81 on such an entry, which the checker treats as a failure. Dependencies 0 to 5 and 22 and
  the thirteen `StrongEncryptedHeader` constraints are annotated on their branches, along
  with template_deviations #3 and #4 — the salt length defaults to zero unless the AES extra
  field is the *last* record — but nothing emits them.

* **`EXTRA64FIELD` is left dead.** template_deviations #1 records that the struct is
  typedef'd and never instantiated, its only use commented out, and that its `efDataSize` is
  a 4-byte field where APPNOTE specifies 2. Its eight constraints entries are flagged
  `unused_in_parse_flow`. Wiring it up would change what the template reads; it is kept
  verbatim, unused, and `elr64DirectoryRecordSize` stays at 44 so `DataSect` is empty.

* **Compression methods other than 0 and 8 are not generated.** `checkers/zip.sh` runs
  `unzip -t`, which decompresses every entry and checks its CRC, so an entry claiming
  `COMP_BZip2` or `COMP_LZMA` with random bytes fails. Method 8 is reachable only because a
  single RFC 1951 *stored* block is a legal deflate stream that a template can emit without a
  compressor. template_deviations #13 notes the `COMPTYPE` enum is not exhaustive; that is
  moot here, since the two values used are both in it.

* **Several archive-level choices are derived rather than planted.** Every byte of a local
  file header is either a fixed value or one of the two decisions the planner plants there,
  and the entry count appears only in the *end* record at the far end of the file — so the
  number of entries, whether the Zip64 tail is emitted, whether the archive carries a
  comment, which extra-field shape an entry gets, whether it is a directory, and which
  attribute namespace it uses are all computed from the two values the first entry drew.
  Every combination still occurs across a corpus (see the census), but they are correlated
  within one file rather than drawn independently.

* **A Zip64 entry's central directory carries the real sizes, not the sentinels.** APPNOTE
  permits this when the values fit in 32 bits, `unzip` accepts it, and it keeps
  dependencies 31 and 32 checkable; a directory entry with `0xFFFFFFFF` would need its own
  Zip64 extra field carrying a 64-bit `deHeaderOffset`, which template_deviations #2 says
  this template cannot read at all.

* **`SetEvilBit(false)` is used nowhere.** Unlike the other formats in this series, ZIP's
  signatures are consumed by a `ReadUInt` lookahead *before* the field that would carry the
  init list, so protecting the declaration would not protect the dispatch. The plants carry
  the signatures instead, which is also why parse parity came out at exactly zero files
  differing.

## The residual failure mode

`ReadBytes(…, preferred, preferred, 1.0)` is exact 255 times in 256; the remaining roll
re-draws from the same set with the evil bit *restored*, a further 1 in 128 — about 1 in
32,768 per plant. That fallback is not a defect to remove: it is what lets the parse
direction stay tolerant, since with the evil bit suppressed a parse of any file whose bytes
differ from the menu would assert. A typical archive carries about twenty plants.

Over a 2,000-file stress run: **1,999 of 2,000 generated and 1,999 of 2,000 accepted by
`unzip -t`.** The single failure lost a local header's signature plant, so the dispatch fell
through to the template's own `Warning` and `return -1` — no crash and no large file, just a
truncated archive. Merging the signature into the same fourteen-byte image as the version,
flags, compression, time and date roughly halved this rate; it was one file in 200 before
that merge.

## Incidental findings

* `checkers/zip.sh` reads `out.zip` from the working directory and accepts `unzip -t`
  returning 0 **or 1**, so a warning-level complaint still counts as a pass. It is a strong
  test — it inflates every entry and checks every CRC — but it is satisfied by an archive
  whose `deHeaderOffset` values are wrong, since `unzip -t` reads the central directory and
  seeks, never cross-checking against the local headers it skips. The independent walker
  described above checks those pointers.

* The JSON's `ZIPFILERECORD.frFileName` and `ZIPDIRENTRY.deFileName` entries give
  `preferred_value` as a *list* of three names rather than a single value; the rewrite
  generates names of the same shape (`file0.dat`, `empty2.txt`, `dir0/`) built to make the
  directory-entry rule of dependency 40 reachable.
