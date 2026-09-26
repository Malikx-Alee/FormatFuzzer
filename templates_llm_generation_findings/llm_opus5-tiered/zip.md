# ZIP — tiered generative template findings

| | |
|---|---|
| **Output** | `templates_llm/llm_opus5-tiered/zip-llm.bt` — **1003 lines** from a 669-line original, **1.4993×** (at the ceiling) |
| **Inputs** | `templates_originals/zip-orig.bt` + `llm_reterived_constraints_zip-llm_opus5-tiered.json` |
| **JSON** | 100 constraints (A 50 / B 15 / C 35), 20 dependencies, 12 structure rules, 17 diversity axes |
| **Target** | Info-ZIP UnZip 6.0, `yes \| ./unzip -P '' -t FILE` |

## Verification

| step | result |
|---|---|
| 1 `ffcompile` | exit 0 |
| 2 `build_new.sh` | exit 0 |
| 3 generate 200 | **0 generation errors**; **191/200 distinct sizes**, most common twice (1%), min 152, p25 782, median 2838, p75 8747, p95 29879, max 29904 |
| 4 round-trip `parse` | **200/200** |
| 5 gate | **no measured run regressed** (a Python simulation of the naive design tied the baseline — see below) |

**Coverage: 28.1% (1493/5304) → 32.0% (1699/5304), +3.9 points / +206 lines /
+4 functions.** 293 mine-only against 87 baseline-only.

> The baseline figure on record was 32.2%, but that was a **10,000-file** run;
> re-run at the prescribed 2000 it is 28.1%. Both numbers above are 2000-file
> runs minutes apart against the same instrumented build.

| file | base | mine | Δ | of |
|---|---|---|---|---|
| `inflate.c` | 76 | **337** | **+261** | 403 |
| `fileio.c` | 213 | 225 | +12 | 626 |
| `crypt.c` | 62 | 67 | +5 | 95 |
| `explode.c` | 21 | 25 | +4 | 198 |
| `extract.c` | 446 | 428 | −18 | 898 |
| `process.c` | 394 | 333 | −61 | 694 |

`zipinfo.c` (954 lines) and `list.c` (243) are unreachable under `-t` by any
input. **The real ceiling is 4107 lines, so 1699 is 41.4% of what is reachable.**

---

## What was measured, and what it overturned

An independent instrumented UnZip and an lcov probe were built before any
template code. Four of the JSON's conclusions did not survive.

**1. Info-ZIP 6.0 implements the "unsupported" methods.** The JSON records
methods 1–7, 9, 10, 18, 19 and 0x60–0x63 as "refused with 'invalid compression
method'". Not in 6.0 — `unshrink.c`, `unreduce.c` and `explode.c` are all in the
build. Measured per method against a deflate reference, with nothing but random
payload bytes:

| method | new lines | where |
|---|---|---|
| 1 (shrink) | **+78** | `unshrink.c` 53, `extract.c` 20 |
| 9 (deflate64) | **+66** | `inflate.c` 44, `extract.c` 17 |
| 6 (implode) | **+47** | `explode.c` 21, `extract.c` 21 |
| every other | +19 each | `extract.c` 15, the unsupported-method path |

So the full 19-value Tier B set is worth considerably more than the JSON argues.

**2. The deflate stream should not be one construction but three.** The JSON
gives a single stored-block recipe. Measured on one file each:

| payload | lines |
|---|---|
| stored blocks only (the JSON's recipe) | 770 |
| stored + `03 00` — an empty **fixed**-Huffman final block, 2 bytes | **914** |
| stored + a 12-byte constant **dynamic** final block | **939** |
| a real `zlib.compress(…, -15)` stream | 926 |

The empty final block decodes to nothing, so it leaves the content, the CRC and
both size fields untouched — and buys `inflate_codes` and `inflate_dynamic` for
2 or 12 bytes. The dynamic one was hand-built
(`05 c0 81 00 00 00 00 00 10 ff d5 04`, HLIT=257/HDIST=1/HCLEN=18, one-bit code
lengths for symbols 1 and 18) and verified to decode to `b""`. **Emitting all
three at random beats a genuine compressor: union 982 vs 926.** This single
change is where the +261 `inflate.c` lines come from.

**3. Encryption is the biggest structural lever, because the harness passes
`-P ''`.** Setting flag bit 0 is worth **+86 lines, 61 of them `crypt.c`**. A
*correctly* ZipCrypto-enveloped entry adds only +29 beyond that — which is why
the cipher was not implemented.

**4. The extra-field IDs Info-ZIP dispatches on are worth more than the JSON's
five.** `TestExtraField` branches separately on `EF_OS2` (0x0009), `EF_ACL`
(0x4c41), `EF_MAC3` (0x334d), `EF_BEOS` (0x6542) and `EF_NTSD` (0x4453), then
calls `test_compr_eb` → `memextract`. Emitting those IDs with **free-length
random data** — Tier B id, Tier C payload, nothing hand-shaped — recovered **55
of the 133 lines the first design was missing** and added 118 overall.

---

## Expressed

### Constraints

**All 50 Tier A entries**, each inside a `SetEvilBit(false)` guard with a
distinct local name. The nine fixed values are the seven record signatures plus
`efVersion` = 1 and `VendorID` = "AE". The 40 calculated values are all written
back from the bytes actually emitted, never computed independently:
`frCrc`/`deCrc`/`ddCRC` as `Checksum(CHECKSUM_CRC32, …)` over the entry's
uncompressed content *where it physically sits in the file*; the three size
triples; every length field; and the two cross-reference offsets
(`deHeaderOffset`, `elDirectoryOffset`) recorded as each record is written —
structure[7] measures a one-byte error in either as fatal in all four readers.

**All 15 Tier B entries** with their complete `valid_values` and
`preferred_value` applied as repetition weighting: the 19 compression methods,
the 44-ID extra-field registry, the 14 version levels, 20 host OSes, both 16-bit
flag masks, the 38 external-attribute values, the 12 AlgIDs (twice), the three
AES strengths, the three PRCFLAGs, the internal-attribute bits and the NTFS
`Tag`.

### Dependencies — all 20

[0]/[1] select the payload from the method; [2]/[3] make COMP_WzAES a marker and
size the salt from the strength; [4]/[5] gate the encryption preambles on bits 0
and 6; [6] is the data descriptor with `frCompressedSize` forced to 0 and the
mandatory signature; [7] is the Zip64 escape, now the *guard* on the template's
`FSkip`; [8]–[11] fix each modelled extra record's size (16 / 5+name / 24 / 7);
[12] and [13] are the directory's back-reference and repeated fields; [14]–[16]
tie the external attributes to the host OS and the trailing-slash convention;
[17] is the UTF-8 bit; [18]/[19] are the Zip64 pairing and the count escape.

### Structure — all 12

The layout is driven by a **three-state tag lookahead** — local records, then the
directory, then the end records — so the generator walks the format's state
machine. `first_element` forces a local header at offset 0; `cardinality` on the
entries is a free geometric draw (the generator picks its own successor tag);
`required`/[4] emit exactly one directory entry per record and count them into
the end record; `last_element` terminates the loop; `mutually_exclusive` is the
four-way data branch; `forbidden` keeps the seven signatures the only top-level
records.

One structural point the JSON does not raise: **every local record owes the
directory an entry**, so `(entries + 1) × 56 + 96` bytes are held back before any
record may use the budget. Without that the archive fills its budget and can
never write its own directory or end record.

### `payload_wellformedness` — one entry, three constructions

`ZIPFILERECORD.frData` is the only entry. `frCompression` selects:

| method | what is emitted | size derivation |
|---|---|---|
| 8 / 9 | a **raw DEFLATE stream, RFC 1951** — no zlib header, no Adler-32 — as one stored block, optionally followed by an empty final block | header 5 bytes, then `frUncompressedSize` content bytes; `LEN`/`NLEN` from that same count |
| 0 | the content byte for byte | `frCompressedSize` = `frUncompressedSize` |
| all others | the content as opaque bytes, reaching each unsupported-method path | same |

The content length is the **free draw of `frUncompressedSize` itself**, clamped
only by the output budget and then written back exactly. Because the content
travels inside one stored block, its literal bytes stay contiguous in the file,
and `frCrc` is a `Checksum` straight over them — no size field is ever trimmed to
fit a precomputed stream. One stored block always suffices: `MAX_FILE_SIZE` is
65536 and a block's `LEN` holds 65535.

Corpus check over 1000 files: the three tail shapes come out **228 / 231 / 229** —
stored-final, fixed tail, dynamic tail.

### `diversity_axes` — all 17 confirmed

**Tier C, declared bare** (no value set, no `<min=>`, no `<max=>`):
`ZIPFILERECORD.frFileName`, `ZIPENDLOCATOR.elDiskNumber`, `.elComment`,
`ZIPDIRENTRY.deFileComment` — and the 21 other Tier C fields (`deFileName`,
`efData`, `efUnicodeName`, the timestamps, disk numbers, `Bitlen`, `Format`,
`CertData`, `Reserved`, `IVData`, `ErdData`, `VData`, `SaltValue`, `dsData`,
`DataSect`, …).

**Tier B, whole set** (`tier_note`: "emit the whole legal set"): `frCompression`
(19), `frFlags` (16 bits), `efHeaderID` (44), `deExternalAttributes` (38),
`VERECORD.HostOS` (20), `VERECORD.Version` (14), `EXTRAFIELD.Strength` (3).

**Tier A quantities left free** — per the JSON's own extension, "do not fix that
quantity, not that the field may disagree with it". Each is drawn bare and then
written back exactly: `frUncompressedSize`, `frCompressedSize`,
`frFileNameLength`, `frExtraFieldLength`, `efDataSize`, `elEntriesInDirectory`.

A grep for `<min=`, `<max=`, `generation_range`, `practical`, `sensible` returns
**zero**.

Confirmed in a 1000-file corpus: **25 distinct compression methods** (all 19 plus
evil-bit extras), **26 versions**, **24 host OSes**, **65 extra-field IDs**, all
16 flag bits set individually (plus 752 files with flags 0), 188 distinct name
lengths, 1–10+ entries per file, data descriptors in 405 files, Zip64 pairs in
181, digital signatures in 166.

**One finding worth recording:** `deFileName` free — which is what Tier C demands
— is also **better** than mirroring the local name (+22 lines in `extract.c`'s
name-mismatch handling, union 936 vs 914). The tier rule and the coverage
objective agreed here.

---

## Not expressed

- **Prefix data before the first local header.** structure[0]'s own
  `generation_note` calls this out: the loop reads a tag at offset 0 and aborts on
  anything else, though all four readers accept a 64-byte prefix. Costs
  `extract.c`'s `extra_bytes` reconciliation.
- **The Zip64 escapes actually being used.** dependency[7] and [19] need
  `frCompressedSize` = 0xFFFFFFFF or `elEntriesInDirectory` = 0xFFFF. The escape
  is *recognised* — it is now the guard on the template's `FSkip`, replacing an
  unconditional skip that would desynchronise every Zip64-tagged entry — but never
  emitted: structure[8] made the four data branches selected by flags, so a record
  carrying the escape would have its data both read and skipped, and the entry
  count cannot reach 65535 inside the budget. Costs ~14 lines of `process.c`'s
  Zip64 retry path.
- **A valid imploded or shrunk stream.** Shannon-Fano trees and LZW-with-partial-
  clear are not constructible in the template language at arbitrary size. Random
  payloads reach `explode.c` 25/198 and `unshrink.c` 59/93 and go no further; 40
  random method-6 files added nothing beyond the first.
- **A correct ZipCrypto envelope.** Needs a stateful byte-wise stream cipher plus a
  second pass to overwrite the plaintext after the CRC is taken. Measured worth
  **+29 lines**, against a line budget already at 1.4993×.
- **`zipinfo.c` (954 lines) and `list.c` (243)** — unreachable under `unzip -t` by
  any input whatsoever.
- **Structurally broken archives** — the 87 baseline-only lines, in `process.c`'s
  not-a-zip / empty-zipfile / missing-bytes paths and `extract.c`'s bad-offset
  recovery. These are the direct cost of every Tier A field being evil-guarded:
  the baseline reaches them precisely because its signatures, offsets and counts
  are unguarded and go wrong at random. No guard was weakened to chase them.

One near-miss worth stating: FormatFuzzer's bare-integer draw is
`1 + rand_int(16)`, which **never yields 0**, so `elDiskNumber` is almost never
zero and nearly every archive trips UnZip's multi-part warning. The cost was
measured by patching the end records — forcing 0 gains 13 `process.c` lines and
loses 4, a net **+9**. Not material, and pinning it would violate Tier C, so it
stays bare.

**No Tier C field was narrowed to work around any of these.**

## Four bugs verification caught

- **ffcompile mines `frCompressedSize == 0`** from the original's line 462
  straight into that field's known values — `frCompressedSize(1, { 0 })` — pinning
  every entry in every archive to zero length. Fixed with local copies; the
  template's own `== 0xFFFFFFFF` escape test then re-introduced it and needed the
  same treatment. Explicit comments at both sites.
- **A lookahead binds the bytes at its own position.** Drawing free lengths with
  `ReadUShort(FTell())` and then writing a clamped value leaves the field with the
  *drawn* value (85 and 232) while the array uses the clamp (40) — silently
  inconsistent. Every calculated field therefore uses declare-bare →
  emit-clamped → **backpatch from an outer scope**.
- **Four idempotence failures broke the round trip** (48/200 at worst). A
  backpatched length is re-read on the next parse, so every clamp has to be a
  fixed point: the structured extra records were emitting `prefix + efDataSize`
  bytes instead of `efDataSize`; the NTFS sub-record walk overshot the per-record
  cap so the written size re-clamped below the bytes present; the `IVSize` and
  `ErdSize` backpatches seeked to offsets that omitted the intervening array; and
  clamping the extra-field *budget* was not idempotent because the last record
  overshoots it.
- **A tag whose branch then declines to emit wedges the file** — the lookahead has
  already committed those four bytes and no later value set can redraw them. This
  bit twice: an empty archive (`PK\x01\x02` at offset 0) and a Zip64 record
  declined for lack of room. Fixed by only ever offering a tag the branch will
  actually write.
