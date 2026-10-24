Rewrite the 010 Editor binary template `templates_originals/{format}-orig.bt` into a
generative specification for FormatFuzzer, guided by the constraints in
`llm_learned_specification/opus5-tiered/llm_reterived_constraints_{format}-llm_opus5-tiered.json`.

Save the result to `templates_llm/llm_opus5-tiered-unrestricted/{format}-llm.bt` (create
the directory if needed). Do not modify the original under `templates_originals/`.

This is the **size-unrestricted** variant of the tiered rewrite. The constraints JSON is
the same file the size-restricted variant consumed; it has not been regenerated. The only
thing that differs is this prompt: the earlier variant capped the template at 1.5× the
original's line count, and this one does not. Read §"No template-size ceiling" before you
start, because it says what the extra room is for and what it is not for.

## Independence requirement

Do NOT read `templates/{format}.bt`, nor any subdirectory of `templates_llm/`. In
particular do not read `templates_llm/llm_opus5-tiered/{format}-llm.bt`, which is the
size-restricted answer to this same task. Those files hold a hand-optimized version and
previous models' versions of this format, and this task is measuring what can be derived
from the original plus the extracted constraints alone. Your inputs are exactly two files:
the original template and the tiered constraints JSON.

## What you are optimising

`ffcompile` compiles a .bt into C++ that is BOTH a generator and a parser. Every random
choice routes through `rand_int()`. When a field declares a set of good known values the
generator picks uniformly from that set; otherwise it emits uniformly random bytes of the
field's width.

The generated files are fed to a real decoder and **line coverage of that decoder is
measured. Coverage is the objective; validity is only a means to it.**

Coverage needs two things at once, and they pull against each other:

- **Depth** — the file must get past the decoder's front gate. A wrong magic number, a
  broken length, a bad CRC or a malformed compressed payload, and the decoder exits
  having executed almost nothing.
- **Diversity** — files must differ from each other in ways the decoder's control flow
  can feel. A thousand near-identical valid files reach the same lines a thousand times.

Declaring a value set buys depth and costs diversity. The JSON has already decided which
fields deserve that trade, and recorded it as a `tier` on every entry. **Your job is to
honour the tiers, not to second-guess them.**

Two properties must also hold in the output:

1. It must still PARSE real files of this format. The same .bt drives both directions —
   breaking the parser breaks round-tripping and the AFL+FFMut mutator.
2. It must TERMINATE. Generated-file size is bounded by `output_budget` (see below),
   never by capping the fields that make files different. Template size is not bounded
   at all.

## Tier-driven emission — the core of this task

### Tier A → pin exactly, and protect from the evil bit

FormatFuzzer emits an out-of-set "evil" value with probability 1/128. For a Tier A field
that is fatal, so every Tier A declaration is wrapped:

    local int evil_sig = SetEvilBit(false);
    CHAR bfType[2] = { "BM" };
    SetEvilBit(evil_sig);

Use a distinct local name per guard (`evil_sig`, `evil_len`, `evil_crc`) so nested guards
restore correctly.

### Tier B → emit every legal value

    ubyte bits = { 1, 2, 4, 8, 16 };

or, where `value_names` is present, an enum type — more readable and what FormatFuzzer's
value mining works best with:

    typedef enum <WORD> bpp { One=1, Four=4, Eight=8, Sixteen=16, Thirtytwo=32 } E_BPP;
    E_BPP biBitCount;

**Emit the complete `valid_values` array.** Do not drop a value because it looks
unproductive, rare, or likely to make the decoder bail — each one is usually a distinct
branch, and reaching branches is the objective. If `preferred_value` is present, use the
preferred/possible split so the preferred values are reachable first; that is a
weighting, not a filter, and the other values must still be emitted.

### Tier C → declare bare

    ushort ImageWidth;
    ushort ImageHeight;

No `= { ... }`. No `<min=>`. No `<max=>`. Nothing.

This is not an oversight to be tidied up later — it is the point. A Tier C entry in the
JSON carries `"type": "unconstrained"` and exists specifically to instruct you to leave
the field alone. Every field named in `diversity_axes` with
`must_remain_unconstrained: true` is in this category, and the rewrite is wrong if any of
them carries a value set or a bound.

The one exception: a `dependencies` rule may constrain a Tier C field _when another field
has a particular value_, because that is a real format rule. "Indexed colour permits bit
depths 1/2/4/8" is such a rule. "Small dimensions keep files fast" is not, and no such
rule will appear in the JSON.

## `payload_wellformedness` → the highest-value thing you will emit

A compressed or encoded payload emitted as random bytes is never valid, and the decoder
stops at it before doing any real work. Emitting a _correct_ stream is what moves coverage
most. The stored/uncompressed form of a codec is valid, trivial to construct for any
size, and gets the decoder all the way in.

### The rule that governs this

> **Derive the payload from the fields in `derives_from`. Never constrain those fields to
> suit a fixed payload.**

If the payload must cover `width * height * channels` bytes, write an emitter that
produces that many bytes for whatever width and height the generator chose. Do not pin
width and height so that one precomputed payload happens to fit. A previous attempt did
exactly that and lost coverage; it is the single mistake this prompt exists to prevent.

### Worked recipe: a zlib/deflate stored stream

`Checksum()` offers no `CHECKSUM_ADLER32`, so compute Adler-32 in closed form. For a
payload of `n` **zero** bytes, `s1` stays 1 and `s2` accumulates 1 per byte, giving:

    adler = ((n % 65521) << 16) | 1

The `% 65521` matters: `s2` is taken modulo 65521, so the naive `(n << 16) | 1` is wrong
once `n` reaches 65521 and the stream is silently rejected at exactly the sizes a freed
dimension produces.

A stored deflate block carries a 16-bit LEN, so a payload longer than 65535 needs several
blocks, with `BFINAL` set only on the last:

    // A zlib (RFC 1950) stream wrapping as many stored DEFLATE (RFC 1951) blocks
    // as `rawLen` requires. rawLen is COMPUTED from the image dimensions, so the
    // dimensions stay free.
    struct ZLIB_ZERO_STREAM (int64 rawLen) {
        local int evil_z = SetEvilBit(false);
        ubyte  zCmf = { 0x78 };          // CM=8 (deflate), CINFO=7 (32K window)
        ubyte  zFlg = { 0x01 };          // FDICT=0, FLEVEL=0; 0x7801 % 31 == 0
        local int64 zRemain = rawLen;
        while (zRemain > 0) {
            local int32 zBlk = 65535;
            if (zRemain < 65535) zBlk = (int32)zRemain;
            local ubyte zFinal = 0;
            if (zRemain - zBlk == 0) zFinal = 1;
            ubyte  zBhdr = { zFinal };               // BFINAL, BTYPE=00 (stored)
            LittleEndian();                          // LEN/NLEN are little-endian
            uint16 zLen  = { (uint16)zBlk };
            uint16 zNlen = { (uint16)(65535 - zBlk) };
            BigEndian();
            local int32 zi = 0;
            while (zi < zBlk) { ubyte zRaw = { 0 }; zi++; }
            zRemain -= zBlk;
        }
        uint32 zAdler = { (uint32)(((rawLen % 65521) << 16) | 1) };
        SetEvilBit(evil_z);
    };

Called with a length derived from the free dimensions, not from a cap:

    local int64 rawLen = height * (1 + width * channels);   // +1 filter byte per row
    ZLIB_ZERO_STREAM idat(rawLen);

All-zero data is what makes the closed-form Adler possible, and filter type 0 (None) with
zero samples decodes to a valid black image. `content_is_free: true` in the JSON means
those inner bytes could be anything; zeros are simply the cheapest choice that keeps the
checksum expressible.

### Other codecs — one emitter per codec variant, not one per format

Apply the same shape: find the codec's "no compression" escape, emit its framing exactly,
and size it from `derives_from`. For GIF LZW that is a clear code followed by literal
codes and an end code, at the minimum code size the colour table implies. For any codec,
if `generation_strategy` in the JSON spells out the byte layout, follow it.

In this variant there is room for more than the single cheapest escape. Where a Tier B
field selects between codecs or compression methods (`biCompression`, a ZIP `method`, a
WAV `wFormatTag`, a sample-entry type), write a well-formed emitter for **each** value
whose payload can be constructed in closed form — stored deflate, a fixed-Huffman deflate
block of literals only, LZW clear/literal/end, RLE4/RLE8 runs, uncompressed PCM of any
bit depth, a stored ZIP entry. Each such emitter walks the decoder into a different
codec's code, which is coverage no header field can buy.

A method value whose payload you genuinely cannot construct (arithmetic-coded JPEG, real
AAC frames) is still worth emitting as a header value: the decoder reaches that method's
entry point before rejecting the data. Keep it in the value set, give it the best payload
you can, and say in your report which values have a well-formed emitter and which do not.

If a payload cannot be constructed for arbitrary sizes, say so in your report rather than
solving it by narrowing a Tier C field. A correct payload for a restricted size range plus
free dimensions that sometimes miss is still better than pinned dimensions, because the
decoder at least sees varied headers.

## `output_budget` → the only size-control mechanism

A repeating structure gets a running byte counter that steers the loop toward its
terminator once the budget is spent:

    local int count = 0;
    while (...) {
        ...
        count += size;
        if (count > 1500) {
            local UBYTE values[] = { 0, 255 };   // steer toward the terminator
        }
    }

Take the number from the `output_budget` on that `structure` entry. Never bound total
size by capping a dimension, a count, or a repetition field — that is the mistake this
whole strategy exists to avoid, and it shows up as a corpus of near-identical files.

The budget bounds the **generated files**. It says nothing about the template. There is
no template-size limit in this variant.

## No template-size ceiling — and what the room is for

The size-restricted variant of this prompt capped the output at 1.5× the original's line
count. Nine of the ten templates written under it landed within 0.03 of that cap, which
means the cap was deciding what got left out. This variant removes it: there is no limit
on the template's line count.

Size is not a goal either. The room is for **breadth** — things that put the decoder on
a branch it would not otherwise see:

- **Every element the original template parses, generated.** The original is a parser
  and handles many optional sections, chunk types, box types, markers, events or records.
  Walk its `switch` arms and `if` branches: each arm the generator can produce is a branch
  the decoder has too. Do not cherry-pick the common ones; the size-restricted variant had
  to, and that is the hypothesis this run tests.
- **Every element the JSON's `structure` lists**, present in part of the corpus. An
  element the JSON does not mark `required` is optional, not forbidden: put it in the
  possible set so some files carry it and some do not.
- **Every `valid_values` entry of every Tier B field**, and the `dependencies` branch
  each one implies. A dependency with three cases is three branches, not one.
- **One well-formed payload emitter per codec variant** the JSON names, per the section
  above — not only the stored escape.
- **Every extension mechanism the format defines** that the original parses: extra
  fields, APPn segments, application extensions, meta events, ancillary chunks, ZIP64
  records, data descriptors. Decoders have dedicated code for each.

What the room is **not** for:

- pinning a Tier C field — still wrong, see §Tier C;
- hand-expanding a loop into cases, or duplicating a struct per value of a field — put
  the value in a set and let one struct serve every value;
- re-emitting the same section with trivially different constants;
- speculative structures the format does not define.

Those four are what filled the earlier 4.8× template, and the tiers already forbid the
first. A practical test for every addition: **name the decoder branch it reaches.** If you
cannot, delete it. Put that name in a comment on the addition, because the report asks
for the list.

## The FormatFuzzer idioms

Good known values on a declaration — the primary mechanism:

    UBYTE GIFTrailer = { 0x3B };
    char  Version[3] = { {"87a"}, {"89a"} };
    DWORD biSize     = { 40 };

Value set in a local array, applied via an attribute:

    local UBYTE possible_values[] = { 0, 1 };
    UBYTE LocalColorTableFlag : 1 <values=possible_values>;

Clearing ffcompile's auto-mined global lookahead values so per-call-site sets win:

    const local UBYTE ReadUByteInitValues[0];

Per-call-site lookahead sets, and preferred-vs-possible:

    local UBYTE values[] = { 0x2C, 0x21 };
    while (ReadUByte(FTell(), values) != 0x3B) { ... }

    local string preferred_chunks[] = { "IHDR" };
    local string possible_chunks[]  = { "IHDR" };
    while (ReadBytes(chunk_type, FTell() + 4, 4, preferred_chunks, possible_chunks)) { ... }

Marking a field as the length of what follows:

    uint32 length <arraylength=true>;

Backpatching a calculated field — record position, emit, seek back, rewrite:

    uint32 length <arraylength=true>;
    local int64 pos_start = FTell();
    ... emit type and data ...
    local int64 pos_end = FTell();
    local uint32 correct_length = pos_end - pos_start - 4;
    if (length != correct_length) {
        FSeek(pos_start - 4);
        local int evil_len = SetEvilBit(false);
        uint32 length = { correct_length };
        SetEvilBit(evil_len);
        FSeek(pos_end);
    }
    local uint32 crc_calc = Checksum(CHECKSUM_CRC32, pos_start, data_size);
    uint32 crc = { crc_calc };

Growing a value set once a precondition is met — how to express "the terminator only
becomes legal after at least one data block":

    local int has_data = false;
    ...
    if (!has_data) { has_data = true; possible += 0x3B; }

`<min=>` / `<max=>` attributes exist, but in this strategy they are used **only** where a
`dependencies` rule or the format itself requires a bound. They are not a size-control
tool.

## How to consume each section of the JSON

**`constraints`** — dispatch on `tier` first, then `type`:

- `fixed_value` (Tier A) → `= { required_value }` inside a `SetEvilBit(false)` guard.
- `enumerated_values` (Tier B) → the complete set, as an enum type where `value_names`
  exists, otherwise `= { v1, v2, ... }`.
- `calculated_value` (Tier A) → never a free field. `<arraylength=true>` for
  length-of-what-follows, otherwise the backpatch pattern, driven by `covers`,
  `includes_self` and `algorithm`.
- `payload_wellformedness` (Tier A) → an emitter parameterised by `derives_from`, per the
  recipe above — one per codec variant where the variant is constructible.
- `pattern_constraint` / `bitmask_constraint` → the closest declarative equivalent.
- `unconstrained` (Tier C) → a bare declaration. This is an instruction, not a gap.
- `lookahead` → the value set as a `local` array at that call site, plus
  `const local <TYPE>ReadInitValues[0];` at the top if global mined values would override
  it.

**`dependencies`** → conditional declarations. Both forms work:

    if (biBitCount == 8) { E_COMPRESSIONS8BPP biCompression; }
    else                 { E_COMPRESSIONS1BPP biCompression; }

    switch (ReadByte(FTell() + 1, color_types)) {
        case Indexed:   ubyte bits = { 1, 2, 4, 8 }; break;
        case TrueColor: ubyte bits = { 8, 16 };      break;
    }

The second reads the _upcoming_ discriminator so the dependent field is constrained
before either is emitted — use it when the dependency runs forward in the file. Every
entry in `dependencies` must appear somewhere in the output, with every case it names.

**`structure`** → drives the refactor from passive parsing to generation:

- `first_element` / `last_element` → a fixed head/tail declaration outside the loop.
- `required` / `requires` → unconditional, or inside the named `condition`.
- everything else the list names → optional: in the possible set, so it appears in part
  of the corpus.
- `cardinality` / `contiguous` → a repeated array bounded by `output_budget`.
- `ordering` → the preferred/possible split, so the generator walks the format's legal
  state machine rather than picking sections at random.
- `mutually_exclusive` / `forbidden` → branches, not post-hoc checks.

**`diversity_axes`** → a checklist of what you must NOT constrain. Before finishing, look
up every field listed there in your own output and confirm it is declared bare.

**`meta.schema_extensions`** → read it; extensions carry real constraints.

## Rules

- Keep the original's identifiers, field order, comments and formatting, so a reviewer
  can map every struct in your output back to the original. Beyond that, add structs,
  emitters and branches as the format requires; a diff that shows substantial additions
  is expected in this variant.
- **There is no ceiling on the output's line count.** The ratio to the original is
  reported, not judged. What is judged is whether each addition reaches a decoder branch
  (§"No template-size ceiling").
- Do not delete parser-side validation (`Assert`, `error_message`, warnings) — harmless
  during generation, and they keep the parse direction honest.
- Add a short comment on each non-obvious edit naming the constraint it implements, and
  on each addition naming the decoder branch or format element it is for.
- Keep every `struct`/field identifier from the original unless a structural rule
  genuinely requires a new one.

## Verify before you finish

Run from the repo root and fix anything that fails.

**1. It compiles**

    ./ffcompile templates_llm/llm_opus5-tiered-unrestricted/{format}-llm.bt /tmp/{format}-check.cpp
      # must exit 0 and print "Finished creating cpp generator".
      # "*ERROR:"/"*WARNING:" lines from the template's own error_message() calls are
      # EXPECTED — ffcompile parses against empty dummy input, so every validity check
      # fires. Judge by the exit code.

**2. It builds**

    LLM_MODEL=opus5-tiered-unrestricted ./build_new.sh {format}-llm
      # must produce build/{format}-llm-opus5-tiered-unrestricted-fuzzer and .so

**3. It generates, the files are varied, and generation is not slow**

    mkdir -p /tmp/{format}-out
    time ./build/{format}-llm-opus5-tiered-unrestricted-fuzzer fuzz /tmp/{format}-out/f{1..200}.{ext}
    ls -l /tmp/{format}-out | awk '{print $5}' | sort -n | uniq -c | sort -rn | head

      # Read that histogram. If one size dominates, the corpus is not diverse and a
      # Tier C field is still pinned somewhere — go and find it. A healthy corpus has
      # a broad spread of sizes. This check is as important as the coverage number:
      # it is what would have caught the earlier GIF regression immediately.
      # Also confirm no file is pathologically large; if any is, a repeat is unbounded.
      #
      # Keep the `time` output for the report. A larger template is allowed; a slower
      # generator costs AFL executions per second over the 8-hour campaign, so the
      # number has to be visible.

Then confirm the **structural** variety the extra room was for:

    for i in 1 2 3 4 5 6 7 8 9 10; do
      ./build/{format}-llm-opus5-tiered-unrestricted-fuzzer parse /tmp/{format}-out/f$i.{ext} 2>/dev/null \
        | awk -F, 'NF >= 3 { print $3 }' | sed 's/\[[0-9]*\]//g' | sort -u | wc -l
    done

      # `parse` prints the tree as `start,end,path` lines, one per field, e.g.
      # `24,27,file~list~avhi~id`. The pipeline counts the DISTINCT field paths in
      # each file, array indices stripped — i.e. how many different kinds of element
      # the file contains. Ten parses, ten counts. If every file reports the same
      # count, the optional elements are either always present or never present —
      # fix the possible sets. A healthy corpus shows a spread.

**4. It still parses its own output**

    ./build/{format}-llm-opus5-tiered-unrestricted-fuzzer parse /tmp/{format}-out/f1.{ext}

**5. THE MEASUREMENT GATE — it must not regress**

    python3 scripts/target_coverage.py     {format} --count 2000          # baseline
    python3 scripts/target_coverage_llm.py {format} --llm-model opus5-tiered-unrestricted --count 2000

Compare the line-coverage percentages in
`coverage_results/{format}/summary.txt` and
`coverage_results/{format}-llm-opus5-tiered-unrestricted/summary.txt`.

**If your template covers less than the hand-optimized baseline, you are not finished.**
Do not report the result and stop. Diagnose it: the likely causes, in order, are a
Tier C field you constrained, a payload emitter that is subtly malformed (the decoder
rejects every file at the same point), and an addition that breaks the parse direction.
Re-check §`diversity_axes`, the size histogram and the structural-variety counts from
step 3. Fix it and re-measure. Report the before and after.

Coverage is noisy at the tenth of a point; treat a gap of less than 0.5 points as a tie,
and anything worse than that as a regression to fix.

The gate is the hand-optimized baseline, not the size-restricted sibling. Do not go
looking for the sibling's number.

({ext} is the format's file extension — note `midi` produces `.mid` files.)

## Report

In the chat, not in the file:

- which constraints, dependencies and structure rules you implemented, and how
- every `payload_wellformedness` you emitted, with the codec and how you derived its
  size; and for every codec/method value in a Tier B set, whether it has a well-formed
  emitter or only a header value
- every field in `diversity_axes`, confirmed declared bare — list them explicitly
- output line count vs the original's, as a ratio — informational, there is no limit
- **the additions list**: every element, branch, emitter or extension you generated that
  the original parses, with the decoder branch each is for. This is the evidence the
  size-unrestricted run exists to produce; be complete.
- the file-size histogram and the `time` output from step 3, and the ten
  structural-variety counts
- the coverage numbers from step 5, baseline vs yours, and what you changed if the first
  attempt regressed
- anything in the JSON you could NOT express in the template language, with the reason —
  and confirmation that you did not work around it by constraining a Tier C field
