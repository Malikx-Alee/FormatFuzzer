# PCAP — `templates_originals/pcap-orig.bt` → `templates_llm/pcap-llm.bt`

Inputs: the original 010 template and
`llm_learned_specification/llm_reterived_constraints_pcap-llm_opus5.json`.
`templates/pcap.bt` was not opened. `templates_originals/pcap-orig.bt` is
byte-identical to `HEAD` (md5 `ea0022394bbbb0b772c790f1792a2256`).

220 → 887 lines: **33 removals, 700 additions, 413 of them comment lines**, and all
**59** declared identifiers preserved. Every removal is a field declaration replaced by
a constrained one, plus `while( !FEof() )` → `while( !FEof( pcapEofP ) )`. No `Assert`,
`Warning` or `error_message` was deleted; two `Warning` calls were added.

---

## Verification

| Command | Result |
|---|---|
| `./ffcompile templates_llm/pcap-llm.bt /tmp/pcap-llm-check.cpp` | **exit 0**, "Finished creating cpp generator" |
| `./build_new.sh pcap-llm` | **exit 0** → `build/pcap-llm-fuzzer` (458,224 B), `build/pcap-llm.so` (458,168 B); 32 warnings, all `-Wparentheses-equality`, 0 errors |
| `./build/pcap-llm-fuzzer fuzz /tmp/pcap-llm-out/f{1..200}.pcap` | **200/200 created, 0 failed** |
| `./build/pcap-llm-fuzzer parse /tmp/pcap-llm-out/f1.pcap` | **exit 0**; 200/200 over the whole set |
| `bash checkers/pcap.sh` (`tcpdump -nr -`) | **exit 0** on f1; **200/200**, and **2000/2000** on a larger run |

**Largest generated file: 13,336 bytes** (min 414, median 3,274, mean 3,955).
Over 2,000 files: min 328, median 3,042, p95 9,358, **max 18,834**.

Beyond the required commands:

* `./build/pcap-llm-fuzzer test 10000` → **9,999 round trips from 10,000 attempts**.
* The **unmodified original template parses 200/200** of the rewrite's output.
* All **5 supplied testcases** parse.
* An independent conformance walker finds **0 structural violations** in 200 files
  (2,281 records) and **0 in 2,000 files** (21,849 records). Every deviation it reports
  is on a field the JSON marks `evil_bit_safe: true` — see *Where the evil bit still
  bites*.
* **Parse parity** against the original over 30 real and degenerate inputs: 29 identical,
  1 where the rewrite is strictly more permissive (see below).

### Baseline (the unmodified original, built the same way)

| | original | rewrite |
|---|---|---|
| files created | 30/200 | **200/200** |
| own round-trip parse | 30/200 | **200/200** |
| `tcpdump -nr` accepts | 0/200 | **200/200** |
| `test 10000` | 1,700 | **9,999** |
| largest file | 64,813 B | **13,336 B** |
| median file | 84 B | 3,274 B |
| files with structural violations | 200/200 | **0/200** |

---

## The shape of the problem, and the shape of the fix

libpcap has no terminator, no count field and no signature at a record boundary.
`PCAPRECORD.incl_len` is the only delimiter in the format, and the template walks the
packet *by shape* rather than by `incl_len` (template_deviation 4), so every length
inside a record has to agree with the one written before it or the parse runs straight
into the next record header and the rest of the file is garbage.

The JSON's `generation_note` for structure rule 4 asks for the packet bytes to be
written first and measured — "the length can never be chosen before the packet exists".
This rewrite inverts that instead: it **chooses the outermost length and derives every
inner one from it**, so each length field is still exactly right but is known before it
is written and **no `FSeek` back-patch is needed anywhere**.

```
incl_len       chosen from a bounded, planted menu           structure 4
pcapRoom     = incl_len - len_before_l3                      dependency 26
total_length   chosen inside [ip_hdr_len*4, pcapRoom]        dependency 12
L4proto        chosen from what total_length leaves over     dependencies 13-15
udp_hdr_len  = total_length - ip_hdr_len*4                   dependency 16
tcp_hdr_len    bounded by the same difference                dependency 17
AppData      = the remainder                                 dependencies 21-22
padding      = incl_len - len_before_l3 - total_length       dependency 27
```

Every derivation reads fields that are already on disk, so **generation and parsing make
the same decisions in the same order**. Nothing is gated on `IsParsing()` except the
`FEof()` probability, which is an assignment and costs no randomness. That is why
`test` round-trips 9,999 of 10,000 files.

The record bytes then add up to `incl_len` *exactly*:
`len_before_l3 + 20 + (total_length - 20) + padding = incl_len`.

---

## Three mechanisms, and why each field gets the one it does

The single hardest lesson of this format is that **`SetEvilBit(false)` is not free**.
FormatFuzzer's evil bit escapes a declared value set once in 128 draws, and the escape
distribution is deliberately biased small — 87.5 % of escapes land in 1..16. A snaplen
of 3, an `incl_len` of 7 or a `total_length` of 11 is exactly the shape that
desynchronises the record stream or underflows one of the four unguarded subtractions
into a four-billion-byte array. An `incl_len` below 34 cannot be made consistent at all:
an Ethernet header plus the twenty mandatory IP bytes is already 34.

`SetEvilBit(false)` stops that — but it also makes the **parse** direction refuse every
real capture whose value is not in the set (`file_accessor.h`: *"Evil bit is disabled,
but an evil decision is required to parse this file"*), and `snaplen`, `incl_len` and
`total_length` take arbitrary values in real captures. An early revision that suppressed
the evil bit on those three failed all five supplied testcases.

### 1. Lookahead plants — the nine size-critical fields

```
ReadBytes( pcapPeek, FTell(), 4, pcapInclMenu, pcapInclMenu, 1.0 );
uint32 incl_len;       /* number of octets of packet saved in file */
```

`ReadBytes(..., preferred, possible, 1.0)` writes one menu entry at the read position
**with the evil bit suppressed for that call** and marks those bytes in the accessor's
bitmap; the plain field declaration that follows copies the marked bytes back over
whatever it drew — `file_integer` does this on every path, before it writes. Generation
therefore takes a menu entry with probability 32767/32768 (the 1/256 fallback branch
restores the evil bit, giving 1/256 × 1/128), while the field itself stays **completely
unconstrained in the parse direction**: `ReadBytes`' own parse lambda routes a value that
is not in the menu to the evil-restored branch, which reads anything.

Planted: `version_major`+`version_minor` (one 4-byte image), `snaplen`, `network`,
`incl_len`, `total_length`, `L4proto`, `udp_hdr_len`. Ten `ReadBytes` call sites.

These are the `lookahead` sets the JSON's schema has no entry for, because the original
contains **no lookahead call of any kind** (template_deviation 12). The menus are built
at run time from `pcapChr`/`pcapLE32`/`pcapBE16`, which is what makes a menu entry with
embedded NUL bytes — every little-endian length below 2^24 has some — expressible at all.

### 2. Declared value sets and range attributes — everything the evil bit may corrupt

21 init-list value sets and 6 `<min=,max=>` attributes, on fields where an out-of-set
value costs at most one malformed packet: `magic_number`, `thiszone`, `sigfigs`,
`orig_len`, the MAC and IPv4 address bytes, `DiffServField`, `Identification`, `Flags`,
`TTL`, `HdrChecksum`, `SrcPort`, `DstPort`, `SEQ`, `ACK`, `ChkSum`, `ts_sec`, `ts_usec`,
`version`, `priority`, `dei`, `id`.

### 3. `SetEvilBit(false)` — only where suppression is provably parse-neutral

Four fields, and the argument is the same for the first three: an out-of-set value makes
the template abort *anyway*, so suppressing the escape removes nothing from the set of
files it can parse.

* `PCAPHEADER.magic_number` — the guard at line 25 returns 1 on anything else.
* `Layer_2.L3type` (`{0x0800 ×5, 0x8100}`) — any other EtherType leaves `L3`
  uninstantiated and the unconditional `L3.ip_hdr_len` read at line 158 asserts
  (template_deviation 0, structure rule 8).
* `Dot1q.L3type` (`{0x0800}`) — any other inner type takes Layer_3's undecoded branch,
  which never declares `L4proto`, and line 158 asserts (dependency 6).
* `Layer_3.ip_hdr_len` (`{5}`) — **the one place where suppression genuinely narrows what
  the template can parse**, and it is unavoidable; see the next section.

---

## `ip_hdr_len` — the field with no good answer

The decoded IPv4 branch reads exactly the twenty mandatory bytes and **never reads an
options region**. So the bytes an IP header occupies are always 20, while `ip_hdr_len`
claims `ip_hdr_len*4`, and the record's total length works out to
`incl_len + 20 - ip_hdr_len*4`. Only `ip_hdr_len == 5` makes a record consistent; the
error cannot be absorbed by `total_length` (it cancels) or by `padding` (whose expression
is fixed by the original). At the evil bit's 1/128 per IP header and ~11 records per
file, leaving the escape in place corrupted roughly 9 % of files.

A bitfield cannot be planted either — `file_integer` asserts *"bitfield lookahead not
implemented"* as soon as the bitmap covers its byte — so the choice really was between
the escape and `SetEvilBit(false)`. Suppression won.

The cost is that a capture carrying IPv4 options is now refused rather than silently
mis-parsed. Measured, this costs nothing: the original refuses such a file too, with
*"Array length too large"*, because `tcp_hdr_len*4` then exceeds what `total_length`
leaves. All five supplied testcases are IHL 5.

`Layer_3.version` keeps its escape (`evil_bit_safe: true`, nothing downstream reads it),
so a raw-IP capture carrying IPv6 still parses — exactly as badly as the original parsed
it (template_deviation 2).

---

## What the JSON asked for, and where it is

### `constraints` — all 48 entries

| entry | how |
|---|---|
| `PCAPHEADER.magic_number` | `= { 0xA1B2C3D4 }` + `SetEvilBit(false)`; also the byte-order mark (dep 29) and timestamp-unit selector (dep 28) |
| `.version_major` / `.version_minor` | planted as one 4-byte image — libpcap refuses any other pair outright |
| `.thiszone` / `.sigfigs` | `= { 0 }`, evil bit left on (corruption_risk low, read by nothing) |
| `.snaplen` | planted menu `{65535 ×3, 262144, 2048, 1514}`, every entry ≥ the 1514 `incl_len` cap |
| `.network` | planted menu `{1, 1, 1, 101}` — only two of the 25 link types parse coherently |
| `MACaddr.Byte[0]` | 8-entry MAC menu, every first octet with bit 0 clear and bit 1 set → the preferred_value 2 pattern |
| `Layer_2.DstMac` / `.SrcMac` | same menu; all unicast, which is what SrcMac requires |
| `Layer_2.L3type` | `{0x0800 ×5, 0x8100}` + `SetEvilBit(false)`; both ≥ 1536, so dep 8's 802.3 length reading never applies |
| `Dot1q.priority` / `.dei` | `<values=>` arrays weighted to preferred_value 0 |
| `Dot1q.id` | `<min=1, max=4094>` — excludes the priority-tagged 0 and the reserved 4095 |
| `Dot1q.L3type` | `{0x0800}` + `SetEvilBit(false)` |
| `IPv4addr.Byte[0]` | superseded by the flow table (below); all octets pinned, all RFC 1918 |
| `Layer_3.version` | `<min=4, max=4>` |
| `Layer_3.ip_hdr_len` | `<min=5, max=5>` + `SetEvilBit(false)` |
| `Layer_3.DiffServField` | the nine DSCP class selectors plus EF, preferred 0; the four codepoints above 127 written as their signed-char encodings (`-128`=CS4 … `-32`=CS7) |
| `Layer_3.total_length` | planted, four candidates offset from the record's room |
| `Layer_3.Identification` | `= { 0 }` — RFC 6864 for the atomic datagram the Flags value makes this |
| `Layer_3.Flags` | `{0x4000 ×3, 0x0000}`; bit 15 always clear (dep 19), never a fragmentation shape (dep 18) |
| `Layer_3.TTL` | `<min=32, max=255>` |
| `Layer_3.L4proto` | three planted menus keyed on the room left over |
| `Layer_3.HdrChecksum` | computed — see below |
| `Layer_3.SRC_IP` / `.DST_IP` | flow table |
| `Layer_3.Unknown` | guarded `hdr_length-4` |
| `Layer_4.SrcPort` | 8-entry ephemeral menu, preferred 49152 |
| `Layer_4.DstPort` | registered-service menus, preferred 80 for TCP and 53 for UDP |
| `Layer_4.udp_hdr_len` | planted `total_length - ip_hdr_len*4` |
| `Layer_4.ChkSum` | `= { 0 }` — legal in IPv4 UDP and the preferred_value |
| `Layer_4.SEQ` | `<min=0, max=2000000000>` |
| `Layer_4.ACK` | `= { 0 }` |
| `Layer_4.tcp_hdr_len` / `.Reserved` | mined comparison sets `{5,6,7,8}` and `{0}` — see below |
| `Layer_4.Crap` / `.packet` | guarded lengths |
| `PCAPRECORD.ts_sec` | `= { pcapTsSec }`, advanced once per record |
| `PCAPRECORD.ts_usec` | `<min=0, max=999999>` |
| `PCAPRECORD.incl_len` | planted 18-entry menu, 60 … 1514 |
| `PCAPRECORD.orig_len` | `= { incl_len ×3, incl_len+4, incl_len+64 }` |
| `PCAPRECORD.L2` / `.d1q` / `.L3` / `.L4` | the conditional structure, unchanged |
| `PCAPRECORD.AppData` / `.padding` | derived, guarded |

### `dependencies` — all 31

0–3 (link type), 4–8 (EtherType), 9–10 (MAC/IP unicast agreement — every generated
address is RFC 1918 unicast, so dep 10's multicast antecedent never fires), 11–12
(version → IHL → total_length), 13–17 (protocol → layer 4 layout and header length),
18–20 (Flags, Identification, checksum coverage), 21–23 (payload lengths, UDP
pseudo-header), 24–27 (orig_len ≥ incl_len; incl_len ≤ snaplen; datagram fits the
record; padding is the difference), 28–29 (the magic fixes the timestamp unit and byte
order), 30 (timestamps are ordered).

Deps 25 and 30 are worth naming because of *how* they are satisfied: 25 holds for the
whole file by construction, because the smallest planted `snaplen` (1514) is the largest
planted `incl_len`; 30 holds because `ts_sec` is advanced from a file-scope base once per
record rather than drawn independently.

### `structure` — all 17

The 24-byte head element, the mandatory header, the bounded record loop, the absent
terminator, the contiguous header/data pairing, the two ordering rules (position and
time), the strictly nested protocol chain, the required `L3`, the three mutually
exclusive `Layer_3` sites, the three mutually exclusive layer 4 layouts, the
EtherType-gated VLAN tag, the TCP/UDP-only payload, the mixed endianness, the mandatory
Ethernet header, no trailing bytes, and the per-file link type.

The record loop replaces `while( !FEof() )` with `while( !FEof( pcapEofP ) )`:
`-1.0` drives FEof's threshold to 510 so it can never fire (the first four records),
`1.0` drives it to 0 so it always does (at 32 records or 24 KB). Both assignments are
gated on generation, because the parse direction needs a probability strictly between 0
and 1 for `FEof` to be exact. Measured over 200 files: **min 4, median 9, max 32 records**
— exactly the JSON's `generation_bound`.

### `template_deviations` — all 14

0, 1, 2, 5, 6, 9, 10, 11, 12 and 13 are handled by the choices above. 3 and 4 — the four
unguarded length subtractions and the missing `incl_len` bound — are handled by explicit
guards, which is the JSON's own `action` ("derive every one of these from the parts
actually written"):

```
local uint16 crapLen = 0;
if (tcp_hdr_len*4 > 13)
    crapLen = tcp_hdr_len*4 - 13;   // original: BYTE Crap[tcp_hdr_len*4-13]
```

The guards are symmetric — no `IsParsing()` — and are no-ops for any well-formed
datagram, so they change the parse of nothing except files the original refused. That is
visible in the parity run: `jumbo.pcap` is the one input of 30 where the two templates
differ, and the rewrite accepts it where the original dies with *"Array length too
large"*.

7 and 8 are recorded rather than fixed: the TCP checksum stays invisible inside `Crap`,
and the bitfield order is left implicit but verified — the generated files come out with
`0x45` as the first IP header byte, so ffcompile does pack first-declared into the most
significant bits under `BigEndian()`, as schema_extension `bitfield_layout` assumes.

---

## The IPv4 header checksum

`Layer_3.HdrChecksum` is a `calculated_value` whose `covers` includes `SRC_IP` and
`DST_IP` — two fields the template writes **after** it. `bt.h` offers `Checksum()` for
CRC-8/16/32 only, and nothing in the language reads bytes back out of the file, so the
RFC 1071 sum has to be built from the field values, which means the two addresses must be
decided before the checksum is emitted.

Rather than back-patch — an `FSeek` rewrite makes the generate and parse directions take
different numbers of decisions, which is what `test` measures — the rewrite decides them
first, rotating an **eight-entry flow table** once per IP header and handing each
`IPv4addr` instance its four bytes through a file-scope local. The checksum function then
reads the five preceding header words back at their **actual** values, so it stays correct
even when the evil bit has corrupted `DiffServField`, `Flags`, `TTL` or `L4proto`.

The cost is that the addresses are drawn from eight flows rather than uniformly — which
is arguably closer to a real capture, where a handful of endpoints talk repeatedly.
Measured over 21,849 generated IP headers: **21,367 carry a correct RFC 1071 checksum
(97.8 %)**. The 482 that do not are the 1/128 evil-bit escapes on `SRC_IP`, `DST_IP` or
`HdrChecksum` itself, all three of which the JSON marks `evil_bit_safe: true`.

---

## What I could not express

**`tcp_hdr_len` and `Reserved` could not take an attribute at all.** ffcompile silently
drops `<min>`, `<max>` and `<values=>` from a **bitfield declared inside an `if`** — the
metadata never reaches the emitted `generate()` call, and `.generate(4)` comes out with no
constraint. (The same declaration at a struct's top level works: `Layer_3.version` and
`Layer_3.ip_hdr_len` both get their ranges.) A bitfield cannot be planted either. What is
left is the mechanism the JSON says this template has always used — ffcompile harvests
every direct field/constant comparison into that field's good-known-value set
(template_deviations 11 and 12) — so the two checks

```
if (tcp_hdr_len != 5 && tcp_hdr_len != 6 && tcp_hdr_len != 7 && tcp_hdr_len != 8)
    Warning("TCP data offset outside the generated range 5..8");
if (Reserved != 0)
    Warning("TCP reserved nibble is not zero");
```

are simultaneously the parser-side validation the original never had and the generator's
value sets. ffcompile confirms it: `tcp_hdr_len: ['5','6','7','8']`, `Reserved: ['0']`.

**`<min>`/`<max>` are dropped when any other attribute precedes them.** `<name="Vlan Id",
min=1, max=4094>` registers `{1, INT_MAX}`; `<min=1, max=4094, name="Vlan Id">` registers
`{1, 4094}`. The attribute order on `Dot1q.id` is deliberate.

**The UDP checksum is emitted as 0, not computed.** Dependency 23: the pseudo-header
reaches back into the IP header and forward across the whole payload, and the payload is
written *after* the checksum field. Computing it would need the same
decide-everything-first treatment as the IP checksum, but over up to 1,460 payload bytes,
which would mean pinning the payload as well — i.e. deleting the entropy the payload
exists to provide. 0 means "not computed" and is legal in IPv4 UDP; it is also the JSON's
`preferred_value`.

**The TCP checksum cannot be reached.** template_deviation 7: bytes 3-4 of `Layer_4.Crap`
are the checksum, but `Crap` is one opaque array and the template has no field for them.
Splitting it would require new identifiers.

**`Layer_4.SEQ`'s full range cannot be named.** `integer_ranges` in the generated C++ is
`std::vector<std::vector<int>>`, so a bound above `INT_MAX` is not expressible; the
attribute says `max=2000000000` and the true 32-bit range is in a comment.

**`snaplen`'s floor of 68 is not offered.** The JSON's `generation_range` starts at 68,
but dependency 25 makes `snaplen` an upper bound on every `incl_len`, and libpcap rejects
a record whose caplen exceeds it outright. Every menu entry is therefore ≥ 1514.

**`ip_hdr_len` is pinned to 5, not 5..15**, and `tcp_hdr_len` to 5..8 rather than 5..15 —
both narrowings are explained above and both are the JSON's own `preferred_value`
neighbourhood.

---

## Where the evil bit still bites

Over 2,000 files / 21,849 records: **0 structural violations**. 852 files carry at least
one deviation, and every one is on a field the JSON marks `evil_bit_safe: true`:

| deviation | files (of 2,000) |
|---|---|
| IP header checksum wrong | 482 |
| IP version nibble ≠ 4 | 192 |
| `ts_sec` not monotonic | 162 |
| `orig_len` < `incl_len` | 156 |
| `ts_usec` above 999999 | 154 |
| layer 2 padding above 46 | 44 |
| TCP reserved nibble ≠ 0 | 38 |
| TCP data offset below 5 | 10 |
| IP reserved flag set | 5 |

None of these changes how many bytes a record occupies, which is why `tcpdump` still
accepts 2000/2000. They are the mutation channel doing its job on exactly the fields the
extraction said could take it.

The one entry that is not an escape is *padding above 46*: for a raw-IP capture with
`incl_len` 1514 the room is 1514 while `total_length` is capped at the 1500-byte
generation_range maximum, so the smallest candidate leaves 60 bytes over. A raw-IP record
has no layer 2 trailer for the Ethernet 60-byte-minimum rule to apply to, so this is
cosmetic.

## Coverage of the generated corpus (2,000 files)

* link type 1 / 101: 1,503 / 497 · snaplen 65535 / 2048 / 1514 / 262144: 985 / 332 / 359 / 324
* EtherType 0x0800 / 0x8100 / raw: 13,886 / 2,650 / 5,313
* all **14** protocol numbers from the JSON's `valid_values`, led by UDP 5,163 and TCP 4,211
* TCP data offsets 5/6/7/8: 1,038 / 1,088 / 991 / 1,072 (plus 22 escapes across 0-4 and 10-15)
* 8 destination ports, led by 80 (792) and 443 (763)
* `incl_len` 60 … 1514, median 142 · `total_length` up to 1500 · padding 0/4/26/46 by design
