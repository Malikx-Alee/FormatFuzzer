Extract the complete generative specification of the 010 Editor binary template
`templates_originals/{format}-orig.bt` and save it as JSON to
`llm_learned_specification/llm_reterived_constraints_{format}-llm_opus5-tiered.json`
(create the `llm_learned_specification/` directory if it does not exist).

## Independence requirement — read this first

This extraction is an input to a model-vs-model comparison. Do NOT open, read, search
for, or consult any pre-existing constraints file, in `llm_learned_specification/`,
`results_ai/`, or anywhere else, and do not look at `templates/` or `templates_llm/`
(which contain already-optimized versions of this format produced by other runs). Your
only inputs are `templates_originals/{format}-orig.bt` and your own knowledge of the
format specification. Consulting prior outputs would contaminate the comparison and
invalidate the result.

## What this is for, and the one mistake that matters

This JSON is the machine-readable input to a second step that rewrites this same
template into a _generative_ specification for FormatFuzzer, which compiles a .bt into a
C++ file generator. The generated files are then fed to a real decoder and line coverage
of that decoder is measured. **Coverage is the objective. Validity is only a means to
it.**

Coverage requires two things at once:

- **Depth** — a file must get past the decoder's front gate. A wrong magic number, a
  broken length, a bad CRC, or a malformed compressed payload and the decoder exits
  having executed almost nothing.
- **Diversity** — the files must differ from each other in ways the decoder's control
  flow can feel. A thousand near-identical valid files reach the same lines a thousand
  times.

Constraining a field buys depth and costs diversity. The entire job of this document is
to say *which* fields to constrain, not *how much* to constrain in general.

Two measured results define the target. Both come from the same model following the
previous version of this prompt on two formats:

- On PNG it recorded that the `IDAT` payload must be a real zlib stream. The rewrite
  emitted real zlib. libpng got past `IDAT: invalid window size` into the pixel
  pipeline. **Coverage rose 8.2 points.** This is depth, correctly bought.
- On GIF it recorded a "sensible generation range" for the image dimensions. The rewrite
  emitted `ushort ImageWidth = { 1, 2, 4, 8 };` where both the original parser and a
  hand-tuned expert leave the field bare. Every generated file came out 976 bytes and
  much like the last one. **Coverage fell 1.7 points.** This is diversity, needlessly
  sold.

Read the GIF template's own comment explaining itself:

    // a decoder allocates ImageWidth*ImageHeight index bytes per frame.
    // The set is restricted to powers of two up to 8 so the pixel count is
    // one of the seven the LZW payloads cover.

That is the mistake, stated plainly by the model that made it. It had a Tier A problem —
the LZW payload must agree with the declared dimensions — and it solved that problem by
destroying a Tier C field. It shrank the dimension space until a handful of precomputed
payloads happened to fit.

**The rule this yields, which outranks everything else in this document: when a payload
must agree with a dimension, a count, or a length, derive the payload from that value.
Never shrink the value to fit a fixed payload.** PNG and GIF posed the same problem. The
PNG answer gained 8.2 points; the GIF answer lost 1.7.

## The three tiers

Every constraint you record carries a `tier`. The tier, not your prose, decides what the
rewrite step emits.

### Tier A — pin exactly

The decoder's front gate. Apply this test, and only this test:

> **If I write a wrong value into this field, does a conforming decoder refuse the file,
> or stop before doing useful work?**

If yes, it is Tier A. If no, it is not, however important the field looks.

Tier A covers: magic numbers and signatures; section and block markers; terminators;
chunk, section and field lengths; CRCs, checksums and Adler values; version fields the
decoder validates; and **payload well-formedness** — the internal structure of a
compressed or encoded blob (zlib/deflate streams, LZW streams, Huffman tables, frame
headers). Payload well-formedness is the highest-value single thing in this file. It is
also the one most often missed, because the .bt usually declares the payload as an
opaque byte array and says nothing about its contents.

Tier A fields must never receive a FormatFuzzer "evil" value.

### Tier B — the full legal set, never a subset

Finite enumerations: enum fields, flag bytes, compression methods, colour types, filter
and interlace methods, encoding identifiers.

Record **every legal value**, including the awkward ones, the rare ones, and the ones you
suspect a decoder handles badly. Each value is usually a distinct branch. Narrowing to
"the ones that work" deletes those branches deliberately, which is the opposite of the
objective. If a value is legal but leads to a shallower parse, record it in
`valid_values` anyway and name the better ones in `preferred_value` — do not drop it.

### Tier C — leave completely free

Dimensions, widths, heights, counts, repetitions, sample rates, frequencies, channel
counts, palette entries, colour values, timestamps, durations, text, comments, padding
whose value is unchecked, and every field where a wrong value still yields a file the
decoder will process.

**Tier C fields get no value set, no minimum, and no maximum.** Not a "sensible range",
not a "practical bound", not a set of "representative" values. This is where diversity
comes from, and it is the only place it can come from.

Total output size is controlled by `output_budget` on the repeating structure that
actually produces the bytes (see `structure`), never by narrowing the fields that make
files different from each other.

### When you cannot decide

If a field could be argued into Tier B or Tier C, **choose Tier C**. If it could be
argued into Tier A or Tier B, apply the Tier A test literally; if a wrong value does not
make the decoder refuse the file, it is Tier B. Over-constraining is the documented
failure mode of this task. Under-constraining a Tier C field costs nothing, because a
generator that emits a strange dimension still produces a file the decoder will read.

## Method

1. Read `templates_originals/{format}-orig.bt` in full before writing anything.
2. Enumerate every `struct`, `union`, `typedef enum`, and every field within them.
3. Assign each field a tier using the tests above.
4. Emit a `constraints` entry for every Tier A and Tier B field. Also emit an entry for
   any Tier C field that a careful reader would be **tempted** to constrain — dimensions,
   counts, repeat bounds, anything that feeds an allocation or a loop bound. For those,
   the entry exists specifically to say "leave this alone", and it is as important as any
   Tier A entry. Do not emit entries for ordinary free-form payload bytes.
5. Walk the top-level parse flow and record document-level structure: what must come
   first, what must come last, what repeats and how often, what is mutually exclusive,
   what is conditionally required.
6. Identify the `diversity_axes` — the handful of fields whose variation actually moves
   the decoder through different code.

This is an exhaustive extraction, not a representative sample.

Harvest evidence from BOTH sources:

**A. The template itself**

- `typedef enum` blocks — each becomes a Tier B `enumerated_values` entry for every field
  of that type.
- `Assert(...)`, and any `if (x != ...) { error_message(...) / Warning / Exit(...) }`
  guard — the compared literal is a Tier A `fixed_value`.
- Any comparison of a field against a literal, including inside `while` / `switch`
  conditions and lookahead calls.
- `ReadUByte()` / `ReadUShort()` / `ReadByte()` / `ReadBytes()` lookahead calls compared
  against literals. These are exactly the "good known values" FormatFuzzer mines at
  compile time — record the full compared set and the call site in `lookahead`.
- Comments stating "must be", "always", "reserved", "fixed", "ignored", "should be 0".
- Reserved/padding fields the decoder validates → Tier A `fixed_value` 0. Reserved fields
  nobody checks → Tier C.
- `FTell()` / `FSeek()` arithmetic, `sizeof(...)`, and any field used as a loop bound or
  array size → a Tier A `calculated_value`.
- **Opaque byte arrays.** Any field declared as a raw byte run whose contents the parser
  does not inspect — `ubyte data[len]`, `char payload[n]`. Ask what the format says must
  be inside it. If the answer is a compressed or encoded stream, that is a Tier A
  `payload_wellformedness`, and the .bt will give you no hint of it.
- `local` variables are computed at parse time and never written to the file. Do NOT emit
  `constraints` entries for them. Do use them as evidence: a `local` holding a computed
  length or a value set usually reveals a `calculated_value` or a dependency.

**B. The published specification for this format**
Add what the format mandates but the parser never checks, with `"source": "spec"`.

## Output schema

A single JSON object with five top-level sections. `constraints` is a map; the others are
arrays.

### 1. `meta` (object)

    "format"             the {format} string
    "source_template"    "templates_originals/{format}-orig.bt"
    "model"              the model that produced this file
    "strategy"           "tiered"
    "spec_reference"     the format specification relied on, named and versioned
    "schema_extensions"  array of {"name", "where", "why"}, one per key or section you
                         added beyond this document. Empty array if none.
    "structure_note"     one sentence on the format's overall shape
    "tier_counts"        {"A": n, "B": n, "C": n}

### 2. `constraints` (object) — per-field, keyed `STRUCT_TYPENAME.field_name`

Use the exact identifiers as spelled in the .bt (case-sensitive). For nested structs use
the innermost enclosing struct's typename. Use `STRUCT.field[i]` only when individual
array elements carry different constraints. Order entries in template document order.

REQUIRED on every entry:

    "tier"             "A" | "B" | "C"
    "tier_rationale"   one sentence. For Tier A, state what the decoder does when the
                       value is wrong. For Tier C, state why constraining it would cost
                       diversity.
    "type"             fixed_value | enumerated_values | calculated_value |
                       pattern_constraint | bitmask_constraint | payload_wellformedness |
                       unconstrained
    "description"      one sentence: what the field is and what makes it valid
    "field_type"       as declared in the .bt, e.g. "uint32", "char[4]", "ubyte", "WORD"
    "source"           "template" | "spec" | "both"
    "evidence"         {"line": <int>, "snippet": "<the .bt line, verbatim, trimmed>"}
                       for source "template"/"both"; for "spec", {"note": "<the rule>"}
    "confidence"       "high" | "medium" | "low"

REQUIRED per type:

    fixed_value            "required_value" (JSON number, or string for char[])
                           "required_value_hex" (width matches the field)
                           "required_value_ascii" (printable; non-printables as \xNN)
    enumerated_values      "valid_values"  — EVERY legal value, no exceptions
                           "value_names"   — parallel array where the enum has real names
                           "completeness"  — "exhaustive" | "partial", and if partial, why
    calculated_value       "algorithm"     e.g. "CRC-32/ISO-HDLC", "byte count"
                           "covers"        exactly which bytes, in template terms
                           "includes_self" true | false
                           "endianness"    "big" | "little" | "n/a"
                           "depends_on"    array of field keys whose values change it
    pattern_constraint     "pattern" (regex or explicit textual rule)
    bitmask_constraint     "valid_bits", "valid_values"
    payload_wellformedness see below
    unconstrained          nothing further required; this is the Tier C marker

NEVER emit for any field:

    "generation_range", "generation_min", "generation_max", "practical_range",
    "sensible_values", or any other key that narrows a Tier C field's legal span.

There is no key for this because there must be no such constraint. A field is either
pinned because the decoder checks it (Tier A), enumerated because its legal set is finite
(Tier B), or free (Tier C). Output size is bounded by `output_budget` in `structure`, and
nowhere else. If you find yourself wanting to cap a dimension because large values would
produce large files, that is precisely the instinct that cost 1.7 points on GIF — record
the budget on the repeating structure instead.

#### `payload_wellformedness` — the highest-value entry type

Use for any field whose bytes must form a valid encoded stream. Required keys:

    "codec"               e.g. "zlib/deflate (RFC 1950 + RFC 1951)", "GIF LZW"
    "must_produce"        the exact structure required, in terms a template author can
                          emit — headers, block framing, trailing checksums
    "decoder_gate"        what the real decoder does when this is random bytes, named as
                          concretely as you can (e.g. "libpng aborts with 'IDAT: invalid
                          window size' before any pixel processing")
    "generation_strategy" the simplest correct construction, spelled out byte by byte.
                          Prefer the uncompressed/stored form where the codec has one:
                          a deflate stored block, an LZW clear-code run. It is valid,
                          trivial to emit, and gets the decoder all the way in.
    "derives_from"        array of field keys this payload's size or shape must agree
                          with (dimensions, counts, lengths). MAY BE EMPTY. When it is
                          not empty, the payload is computed from those fields — those
                          fields are NOT to be narrowed to suit the payload.
    "content_is_free"     true | false. Almost always true: the bytes *inside* a
                          well-formed stream are unconstrained even though the stream's
                          framing is Tier A. This is how a format gets depth and
                          diversity at once — pin the envelope, free the contents.

OPTIONAL but high-value wherever they apply:

    "endianness"       for multi-byte numeric fields
    "preferred_value"  for Tier B: the value(s) most likely to let a decoder reach deep
                       parsing. Does not replace or shrink "valid_values" — it names a
                       subset to favour while still emitting all of them.
    "lookahead"        {"function": "ReadUByte"|"ReadUShort"|"ReadByte"|"ReadBytes",
                        "call_site_line": N, "values": [...], "preferred": [...]}
                       when this field is decided by a lookahead call — FormatFuzzer
                       needs the per-call-site value set, not one global set
    "notes"            anything a template author would need that has no other home

### 3. `dependencies` (array) — conditional constraints across fields

One object per rule of the form "when some field has some value, another field's legal
set changes".

    {"when": {"field": "PNG_CHUNK_IHDR.color_type", "equals": 3},
     "then": {"field": "PNG_CHUNK_IHDR.bits",
              "tier": "B", "type": "enumerated_values", "valid_values": [1, 2, 4, 8]},
     "description": "Indexed-colour images permit bit depths 1/2/4/8 only",
     "source": "spec", "confidence": "high"}

`when` may use "equals", "in", "min"/"max", or "present"/"absent" for whole sections.
`then` may constrain a field's values, or mark a section required/forbidden.

A dependency may legitimately restrict a field that is Tier C in general — a dimension
constrained *by another field's value* is a real format rule, not an arbitrary narrowing.
The test is whether the rule comes from the format. "Indexed colour permits these bit
depths" is a rule. "Small dimensions keep files fast" is not.

### 4. `structure` (array) — document-level ordering, cardinality, and size budget

    {"rule": "first_element" | "last_element" | "required" | "forbidden" |
             "cardinality" | "ordering" | "mutually_exclusive" | "requires" | "contiguous",
     "subject": "<struct name, or a field value such as chunk type \"IHDR\">",
     "detail": "<the constraint>",
     "condition": "<optional: only applies when ...>",
     "description": "<one sentence>",
     "source": "template" | "spec" | "both",
     "output_budget": "<REQUIRED for anything that repeats. A total-bytes budget for
                        this structure across the whole file, with a rationale. This is
                        the ONLY size-control mechanism in this schema. Express it as a
                        running total the generator checks and stops at — not as a cap
                        on any individual field's value.>",
     "generation_note": "<how a generator should satisfy this, e.g. 'emit as a fixed head
                         element, then a repeated array bounded by output_budget, then a
                         fixed tail'>"}

Cover at minimum: mandatory first/last elements, required sections, conditionally
required sections, sections that must be contiguous, count limits the format imposes,
and any ordering the format requires.

### 5. `diversity_axes` (array) — what must stay free

The fields whose variation actually drives the decoder down different paths. This section
exists so the rewrite step knows what it must protect.

    {"field": "GIF_IMAGE_DESCRIPTOR.ImageWidth",
     "why": "sets the LZW decode loop bounds and the row-stride handling; narrow and wide
             images take different paths through the de-interlacing and row-copy code",
     "decoder_paths": "<what differs in the decoder across this field's range>",
     "must_remain_unconstrained": true,
     "interacts_with": ["GIF_IMAGE_DATA.lzw_stream"]}

Name every field that a size-conscious author would be tempted to pin. For each, if it
interacts with a payload, list that payload in `interacts_with` — that pairing is the
instruction to the rewrite step to *derive the payload from the field*, not the reverse.

Include at least every field that appears in any `payload_wellformedness.derives_from`.

## Hard rules

- Ground every key in the file. Never invent a struct or field name that does not appear
  in `templates_originals/{format}-orig.bt`.
- Every `evidence.line` must be a real line number, and `evidence.snippet` must be that
  line copied verbatim. If you cannot cite a line, set `"source": "spec"` and explain.
- Every entry has a `tier` and a `tier_rationale`.
- No key anywhere narrows a Tier C field's numeric span.
- Valid JSON, 2-space indent, no trailing commas, no comments, no markdown fences, no
  prose before or after the JSON.

## Schema latitude

The schema above is a floor, not a ceiling. If a constraint in this format is not
expressible in it, invent what you need rather than distorting the constraint to fit or
dropping it. Record every addition in `meta.schema_extensions` with its rationale. Do not
rename or drop anything specified above; downstream tooling reads those names. The one
thing you may not add is a generation-range key of any name — see above.

## Completeness checklist — verify each before finishing

1. EVERY magic number, signature, section marker, block terminator, and field separator
   is present as a Tier A `fixed_value`. Re-scan specifically for these.
2. EVERY length, size, count, offset, CRC, checksum, or Adler field is a Tier A
   `calculated_value` with `algorithm`, `covers`, and `includes_self` filled in.
3. EVERY opaque byte array has been asked the question "what must be inside this?", and
   every compressed or encoded payload is a Tier A `payload_wellformedness` with a
   concrete `generation_strategy`. If this format has no such payload, say so explicitly
   in `meta.structure_note`.
4. EVERY `typedef enum` is a Tier B `enumerated_values` entry with
   `"completeness": "exhaustive"`, or a stated reason why not.
5. No Tier B entry omits a legal value because it seemed unproductive.
6. EVERY dimension, count, and repeat-controlling field appears as a Tier C entry with
   `"type": "unconstrained"`, and also in `diversity_axes`.
7. NO entry anywhere carries a generation range, practical bound, or narrowed value set
   for a Tier C field. Search your own output for "range", "practical", "sensible",
   "reasonable" and check each hit.
8. Every repeating section in `structure` has an `output_budget`, and no field was capped
   to achieve the same effect.
9. Every field in any `payload_wellformedness.derives_from` also appears in
   `diversity_axes` with `must_remain_unconstrained: true`.
10. Every key in `constraints` resolves to a real field in the .bt.
11. The file parses as JSON.

Then report in the chat only (not in the file): total `constraints` entries; the count
per tier and per type; `dependencies`, `structure` and `diversity_axes` counts; every
`payload_wellformedness` found, with its codec; any schema extension made; and any field
you judged a close call between two tiers, with which way you went and why.
