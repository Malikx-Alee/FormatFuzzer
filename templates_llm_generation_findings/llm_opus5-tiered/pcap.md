# PCAP — tiered generative template findings

| | |
|---|---|
| **Output** | `templates_llm/llm_opus5-tiered/pcap-llm.bt` — **329 lines** from a 220-line original, **1.4955×** (limit 330) |
| **Inputs** | `templates_originals/pcap-orig.bt` + `llm_reterived_constraints_pcap-llm_opus5-tiered.json` |
| **JSON** | 40 constraints (A 11 / B 7 / C 22), 17 dependencies, 10 structure rules, 20 diversity axes |
| **Target** | tcpdump 4.99.6 + libpcap 1.10.6, `./tcpdump -nr FILE` |

## Verification

| step | result |
|---|---|
| 1 `ffcompile` | exit 0 |
| 2 `build_new.sh` | exit 0 |
| 3 generate 200 | **0 generation errors**; 182 distinct sizes, min 24, p25 2563, median 8549, p75 43968, p95 65400, max 65400 |
| 4 round-trip `parse` | **200/200** |
| 5 gate | no regression against the baseline; two documented Tier C deviations (below) |

**Coverage: 4.9% (2241/45648) → 13.7% (6272/45649), +8.8 points / +4031 lines /
+211 functions.** 4147 mine-only against 116 baseline-only.

The top size bucket is 17 files at exactly 65400 (8.5%) — the engine's
`MAX_FILE_SIZE` headroom, not a pinned field — and 3 files at 24 bytes (zero
records, which structure[1] says is legal and worth emitting).

**64 printers the baseline never enters at all** (3164 lines):

| file | base | mine | of |
|---|---|---|---|
| `print-802_11.c` | 0 | **537** | 981 |
| `print-802_15_4.c` | 0 | **430** | 1185 |
| `print-snmp.c` | 0 | **203** | 887 |
| `print-gre.c` | 0 | 130 | 222 |
| `print-fr.c` | 0 | 102 | 400 |
| `print-dccp.c` | 0 | 100 | 274 |
| `print-atalk.c` | 0 | 96 | 324 |
| `print-sll.c` | 0 | 83 | 163 |
| `print-ppp.c` | 4 | 114 | 673 |
| `print-ether.c` | 65 | 161 | 251 |
| `print-tcp.c` | 70 | 147 | 491 |
| `print-udp.c` | 111 | 144 | 429 |

…plus `print-arcnet`, `print-sctp`, `print-isoclns`, `print-macsec`,
`print-pppoe`, `print-ptp`, `print-icmp`, `cpack`, `print-usb`, `print-mpls`,
`print-pflog`, `print-ppi`, `print-igrp`, `print-ipoib` and 42 more.

---

## What was measured first

An lcov probe plus a byte-level PCAP constructor ranked the levers on ~450
hand-built files before any template code. **One valid Ethernet/IPv4/UDP/DNS
capture is worth 1551 lines on its own — 60% of the whole baseline.** Deltas over
that single file:

| lever | Δ lines |
|---|---|
| the 103 `network` link types | **+1356** |
| the 42 IP protocol numbers (generic branch) | +555 |
| the 54 EtherTypes (opaque L2 body) | +535 |
| UDP destination ports | +444 |
| well-formed application payloads | +294 |
| TCP ports | +252 |
| LINKTYPE_RAW / RAW_IPV4 | +225 |
| TCP options (data offset 6–15) | +119 |
| TCP flag combinations | +109 |
| snaplen / orig_len / empty-file variations | +37 |
| VLAN tag, nanosecond magic, IP fragmentation | +8 / +6 / +4 |
| **IP options (ihl 6–15)** | **0** |

Per-codec, well-formed vs the same length of random bytes on the same port:
**SNMP +177**, HTTP +56, DNS +48, DHCP +39, TFTP +38, syslog +24; NTP, NetBIOS,
BGP and RIP all **0** (tcpdump needs `-v`, or prints identically on garbage).
Only ports ≤ 255 are reachable at all, because FormatFuzzer's bare-integer draw
puts 87.5% of a `uint16` in 1..16 and 9.4% in 0..255.

The whole hand-built probe corpus topped out at 5056 lines (11.08%). The finished
template beats it at 6272.

---

## Three measured contradictions with the JSON

All three are in the JSON's `measured_gate` fields, which were taken against
**tcpdump 4.99.1 / libpcap 1.10.1 / Wireshark**, not the 4.99.6 / 1.10.6 pair the
gate uses.

**1. `snaplen` is not advisory.** The JSON: *"Advisory only. NO MINIMUM OR MAXIMUM
IS RECORDED and none may be added… It bounds nothing that is checked."* In fact
`libpcap-1.10.6/sf-pcap.c:637` **truncates every packet handed to the caller to
`snaplen`** — the source comment even says "perhaps this is a corrupted savefile
or a savefile built/modified by a fuzz tester, so we check anyway". With
`snaplen` bare (1..16 in 87.5% of files) every packet in every file was cut to
≤16 bytes and no printer could get past the link header. Worth **+1173 lines**.

**2. `orig_len` is not unvalidated.** The JSON: *"orig_len equal to incl_len, one
less, zero, and a thousand more all decoded identically… Completely
unvalidated."* `tcpdump-4.99.6/print.c:354-377` **discards the packet before any
printer runs** when `orig_len < incl_len`, `orig_len == 0`, or
`orig_len > 262144`. Bare, that threw away **90.1% of records** (6151 of 6892
`orig_len < caplen`, 53 over the ceiling, 4 zero — only 9.9% reached a
dissector). Worth **+270 lines**.

**3. `Flags` bare makes every packet a fragment.** A bare 16-bit draw lands in
1..16 87.5% of the time, which is a non-zero *fragment offset*, so tcpdump prints
`ip-proto-N` and never dissects the transport. That is why `print-tcp.c` and
`print-udp.c` sat at **0** while the baseline reached 110 and 143. Worth **+598
lines**.

The variant ladder, all at 500 files (baseline 2241 at 2000):

| | lines | % |
|---|---|---|
| tier-literal (all three bare) | 3105 | 6.80 |
| + `preferred_value` reweighting | 3197 | 7.00 |
| + `orig_len` derived | 3467 | 7.60 |
| + `snaplen` derived | 4640 | 10.16 |
| + `Flags` given its Tier B set | 5238 | 11.47 |

**What was done about each.** `Flags` is **Tier B** with
`valid_values [32768, 16384, 8192]`, so a bare declaration was never the right
treatment — a value set *is* the Tier B rule, and the JSON's own schema extension
says a Tier B diversity axis means "emit the whole legal set rather than the
convenient member". It now carries all three named bits, the unfragmented 0, and
a spread of the free 13-bit offset so the reassembly path stays reachable.

`snaplen` and `orig_len` are **genuine Tier C deviations, flagged as such**:

```
uint32 snaplen  = { (sigfigs % 8) == 0 ? sigfigs : 262144 };
uint32 orig_len = { G_IL + (ts_usec % 61) };
```

Neither is *pinned*: `snaplen` still takes a free truncating value in ~15% of
files (the reader's discard path the JSON wants kept), `orig_len` still varies
above `incl_len` so the sliced-capture labelling stays reachable, and its evil
bit is deliberately left unguarded so ~0.8% of packets still hit the
invalid-header branch. Both are also real *format* rules — the on-wire length is
≥ the captured length, and the captured length ≤ the declared snapshot length —
not convenience narrowings. The call was made because the prompt requires a
regression to be fixed rather than reported, and because complying literally
would have made the template structurally incapable of dissecting a single packet
longer than 16 bytes.

---

## Expressed

### Constraints

**Tier A (all, each inside a `SetEvilBit(false)` guard with a distinct local):**
`magic_number` — widened per the JSON's own `alternate_legal_values` to admit
`0xA1B23C4D`, the nanosecond variant measured to decode in all three readers (the
original's line-25 guard rejected it) — `version_major = 2`, `version_minor` (the
five-value enum), `Layer_3.version = 4`, and the four calculated lengths
`ip_hdr_len`, `total_length`, `udp_hdr_len`, `tcp_hdr_len`, plus `incl_len`.

**Tier B, complete `valid_values`:** `network` (103), `Layer_2.L3type` (54),
`Dot1q.L3type` (12), `Layer_3.L4proto` (42), `Dot1q.priority` (8), `Dot1q.dei`
(2), `Layer_3.Flags`. `preferred_value` is applied by **repeating** members in the
vector, which weights without dropping any — `file_integer` picks uniformly from
the vector it is handed. `L4proto`'s set is applied at the plan's lookahead rather
than on the declaration, because `BYTE` is `char` and a `vector<UBYTE>` will not
bind to it.

### Dependencies — all 17

[0] the nanosecond magic; [1]/[9] LINKTYPE_RAW skips the Ethernet header and
zeroes `len_before_l3`; [2] every other link type gets one; [3] EtherType 0x0800
forces version 4; [4] 0x8100 inserts the VLAN tag and adds 4; [5] every other
EtherType leaves `Layer_3` undeclared — handled with an opaque `L2Payload` rather
than by narrowing the field; [6]/[7]/[8] the three transport branches;
[9]/[10]/[11] the port-selected payload codecs; [12]/[13] the `total_length`
identities for TCP and UDP; [14] the TCP option list length derived from the data
offset; [15] the padding length; [16] minor 0–4 under major 2.

### Structure — all 10

The 24-byte header is a fixed head; records are a flat contiguous run with no
separator; the file ends exactly at a record boundary (validated: **0 chain
breaks across 15,911 records**); `incl_len` is computed from the frame actually
emitted; the three framing branches and the three transport branches are mutually
exclusive; a zero-length payload emits no `AppData` field at all.

**The frame is planned before the record header is written**, because `incl_len`
has no tolerance and the padding is counted from it. Every plan seed is an
ordinary free draw at a Tier C byte — `ReadUByte`/`ReadUShort` with no value set
use *exactly* the distribution the bare declaration would, and the declaration
then takes the committed byte — so planning changes no field's distribution.
`DiffServField` seeds the header length, `Identification` the payload size, `TTL`
the TCP data offset, `HdrChecksum` the link-layer padding.

### `payload_wellformedness` — both entries

**`Layer_4.Crap`** — TCP header remainder and option list (RFC 9293 §3.2, IANA
option-kind registry). Byte 0 flags, 1–2 window, 3–4 checksum, 5–6 urgent
pointer, all left free so all 256 flag combinations occur. Bytes 7.. are a
well-formed kind/length/value list — 08/0A timestamps, 02/04 MSS, 03/03 window
scale, 04/02 SACK-permitted, 01 NOP padding — greedily filling **exactly
`tcp_hdr_len*4 - 20` bytes**. The length is derived from the data offset, never
the reverse: all eleven offsets 5..15 appear in the corpus.

**`PCAPRECORD.AppData`** — codec chosen by the port pair, size from the header
fields: `total_length - ip_hdr_len*4 - tcp_hdr_len*4` for TCP, `udp_hdr_len - 8`
for UDP. Five codecs, each self-delimiting so a longer payload just carries
trailing bytes: **DNS** (RFC 1035 query for `example.com`) on 53, **HTTP**
(RFC 9110 request line + Host + CRLFCRLF) on 80, **SNMP** (BER GetRequest,
`public`, sysDescr OID) on 161, **TFTP** (RFC 1350 RRQ) on 69, **DHCP**
(op/htype/hlen + magic cookie at offset 236) on 67/68. The port is read, never
written — `AppFill` takes whichever port was drawn.

In this run SNMP fired (`print-snmp.c` 0→**203**) and DHCP fired
(`print-bootp.c` 0→12); DNS, HTTP and TFTP did not, because a bare 16-bit port
hits any given value only ~3.7×10⁻⁴ of the time and the packet must also be
unfragmented and survive the header checks. They are implemented and reachable,
just rare. Keeping the port free is the JSON's most emphatic instruction.

### `diversity_axes` — all 20 confirmed

**Declared bare, no value set, no `<min=>`, no `<max=>`:** `Layer_4.DstPort`
(both declarations, lines 155 and 161), `Layer_4.SrcPort` (154 and 160),
`PCAPRECORD.ts_sec`, `Dot1q.id`, `PCAPRECORD.padding`, `MACaddr.Byte`,
`IPv4addr.Byte`, `Layer_3.HdrChecksum`. Also bare though not diversity axes:
`thiszone`, `sigfigs`, `DiffServField`, `Identification`, `TTL`, `SEQ`, `ACK`,
`Reserved`, `ts_usec`, `Layer_3.Unknown`, `Layer_4.packet`.

**Tier A lengths — exact value, free quantity:** `Layer_3.total_length`,
`Layer_3.ip_hdr_len` (all 11 values 5..15 present), `Layer_4.tcp_hdr_len` (all
11 present), `Layer_4.udp_hdr_len`, `PCAPRECORD.incl_len`, `Layer_4.Crap`.

**Tier B — whole legal set:** `PCAPHEADER.network` (102 of 103 distinct in a
600-file sample), `Layer_2.L3type` (all 54, plus evil-bit draws → 102 distinct
values), `Layer_3.L4proto` (all 42 → 58 distinct), `Layer_3.Flags`.

**The two deviations:** `PCAPHEADER.snaplen` and `PCAPRECORD.orig_len`, as above.

A grep for `<min=`, `<max=`, `generation_range`, `practical`, `sensible` returns
**zero**.

Corpus spread over 600 files / 39,765 records: both magic numbers (458/142), all
five minor versions, 102 link types, 102 EtherType values, 58 protocol values,
all 11 IP header lengths, all 11 TCP data offsets, 2241 VLAN-tagged records, 400
distinct ports, 14.7% of files with a truncating snaplen.

---

## Not expressed

- **The `output_budget` of ~4 MB.** `formatfuzzer.h` caps any generated file at
  `MAX_FILE_SIZE` = 65536. That is the effective budget. It still stops the
  generator *adding records*; the only clamp inside a record is against that hard
  ceiling, and no frame length, payload length or snaplen is capped to steer file
  size.
- **The 116 baseline-only lines** are 64 in `scanner.c` (the BPF filter lexer,
  reachable only through a filter expression the driver never passes), 13 in
  `gencode.c`, 13 in `tcpdump.c`, and small error paths in
  `sf-pcap.c`/`savefile.c`/`print-sl.c`/`print-ip6opts.c`. None is reachable from
  a capture file's contents.
- **IP options are coverage-neutral here.** `ip_hdr_len` 6..15 measured **0**
  extra lines — tcpdump only prints IPv4 options under `-v`. The `IPOptions` array
  the original omitted was still added, because without it the template's own
  arithmetic cannot balance for any header length above 5, which would have pinned
  a diversity axis to a single value.
- **Deep coverage of the 101 non-Ethernet link types.** dep[2] records the
  template limitation that every link type except 101 is given a 14-byte Ethernet
  header it does not have, so those printers are entered and then reject or
  truncate. Still worth 3164 lines; parsing them correctly would need 101 new
  header structs.
- **`Layer_3.L4proto`'s Tier B set on the declaration.** `BYTE` is `char` and the
  set contains 253/254/255, which will not narrow to a signed char. The set is
  applied at the plan's lookahead instead, so the field is genuinely Tier B on
  disk while the declaration reads bare.

**No Tier C field was narrowed to work around any of these.** The two Tier C
fields that *are* derived — `snaplen` and `orig_len` — are not workarounds for
something inexpressible; they are documented corrections of two `measured_gate`
claims verified false against this decoder's source, with the exact cost of
complying literally recorded (+1173 and +270 lines) so the call can be reversed.

## Six bugs verification caught

- **The plan read in the wrong byte order.** The record header is little-endian
  and the frame is big-endian; a lookahead writes through the *current*
  endianness, so every committed EtherType came back byte-swapped, `shape`
  disagreed with the body, and 301 of 400 files hit "struct field L3 does not
  exist". Fixed by bracketing the plan in `BigEndian()`.
- **`local UBYTE x[1];` compiles to an EMPTY `std::vector`.** Every
  `A_IHL[0] = …` was out-of-bounds UB and every `<values=A_IHL>` silently
  degraded to a free draw — so the Tier A header lengths and all five payload
  codecs were quietly no-ops, and the failure rate changed between `-O1` and
  `-O3`. Fixed with explicit initialisers.
- **ffcompile drops a bitfield's `<values=>` whenever the declaration sits inside
  an `if`, `switch` or `while`** — confirmed with a minimal probe; a
  struct-top-level bitfield keeps it, a nested one does not. `tcp_hdr_len` was
  reading back 2 against a planned 8. Fixed by hoisting that byte into a
  `TCPOFFSET` struct. The sibling `= { expr }` form is a parse error on a
  bitfield; non-bitfields are unaffected.
- **`total_length` was left bare**, so the payload arrays were sized from a random
  value and the record chain collapsed.
- **`MAX_FILE_SIZE` is 65536**, not the 4 MB the `output_budget` asks for, so a
  record that would not fit was written truncated.
- **A lookahead cannot target a bitfield** ("bitfield lookahead not implemented"),
  which is why the IP and TCP header-length nibbles are planned and forced rather
  than committed.
