Extract the complete generative specification of the 010 Editor binary template
`templates_originals/{format}-orig.bt` and save it as JSON to
`llm_learned_specification/llm_reterived_constraints_{format}-llm_opus5.json`
(create the `llm_learned_specification/` directory if it does not exist).

## Independence requirement — read this first

This extraction is an input to a model-vs-model comparison. Do NOT open, read, search
for, or consult any pre-existing constraints file, in `results_ai/` or anywhere else,
and do not look at `templates/` or `templates_llm/` (which contain already-optimized
versions of this format). Your only inputs are `templates_originals/{format}-orig.bt`
and your own knowledge of the format specification. Consulting prior outputs would
contaminate the comparison and invalidate the result.

## Why this matters

This JSON is the machine-readable input to a second step that rewrites this same
template into a _generative_ specification for FormatFuzzer, which compiles a .bt into
a C++ file generator. Anything you fail to record gets filled with uniformly random
bytes. For a structural anchor (magic number, marker, terminator) that single omission
makes 100% of generated files invalid. Completeness on anchors outranks entry count.

Three consequences shape the whole task:

1. The source template is a _passive parser_, and parsers are lax — they accept far
   more than the format permits. You are specifying what makes a file VALID, not what
   this parser tolerates. Where the published specification is stricter than the
   template's own checks, record the specification's rule and mark its source.

2. Validity is not only per-field. A file whose every field is individually legal is
   still garbage if sections appear in the wrong order, a required section is missing,
   or a length field disagrees with the bytes it describes. Capture those relationships
   as first-class data, never as prose buried inside a description string.

3. Spec-legal is not the same as generation-practical. A field the spec allows to reach
   2^31-1 (an image dimension, a repeat count, a chunk length) will, if generated
   uniformly, produce enormous files that dominate runtime and reduce the number of
   test inputs produced. Where a field is like this, record BOTH the true spec bound
   and a sane generation bound (see `generation_range`).

## Method

1. Read `templates_originals/{format}-orig.bt` in full before writing anything.
2. Enumerate every `struct`, `union`, `typedef enum`, and every field within them.
3. For each field decide whether it is genuinely free-form (payload bytes, pixel data,
   free text, timestamps) or constrained. Emit an entry only for constrained fields.
4. Separately, walk the file's top-level parse flow and record document-level structure:
   what must come first, what must come last, what repeats and how often, what is
   mutually exclusive, what is required only under a condition.

This is an exhaustive extraction, not a representative sample. Do not stop at the
"interesting" fields.

Harvest evidence from BOTH sources:

**A. The template itself**

- `typedef enum` blocks — each becomes `enumerated_values` for every field of that type.
- `Assert(...)`, and any `if (x != ...) { error_message(...) / Warning / Exit(...) }`
  guard — the compared literal is a `fixed_value`.
- Any comparison of a field against a literal, including inside `while` / `switch`
  conditions and lookahead calls.
- `ReadUByte()` / `ReadUShort()` / `ReadByte()` / `ReadBytes()` lookahead calls compared
  against literals. These are exactly the "good known values" FormatFuzzer mines at
  compile time, so they are the highest-value entries in the file — record the full
  compared set and the call site in `lookahead` (see schema).
- Comments stating "must be", "always", "reserved", "fixed", "ignored", "should be 0".
- Reserved/padding fields → `fixed_value` 0.
- `FTell()` / `FSeek()` arithmetic, `sizeof(...)`, and any field used as a loop bound
  or array size → a length/offset/count that is a `calculated_value`.
- `local` variables are computed at parse time and never written to the file. Do NOT
  emit `constraints` entries for them. Do use them as evidence: a `local` holding a
  computed length or a value set usually reveals a `calculated_value` or a dependency.

**B. The published specification for this format**
Add what the format mandates but the parser never checks, with `"source": "spec"`.

## Output schema

A single JSON object with four top-level sections. `constraints` is a map; the other
three are arrays.

### 1. `meta` (object)

"format" the {format} string
"source_template" "templates_originals/{format}-orig.bt"
"model" the model that produced this file
"spec_reference" the format specification relied on, named and versioned
"schema_extensions" array of {"name", "where", "why"}, one per key or section you
added beyond this document. Empty array if none.
"structure_note" one sentence on the format's overall shape (e.g. "fixed header
followed by a chunk stream terminated by IEND")

### 2. `constraints` (object) — per-field, keyed `STRUCT_TYPENAME.field_name`

Use the exact identifiers as spelled in the .bt (case-sensitive). For nested structs use
the innermost enclosing struct's typename. Use `STRUCT.field[i]` only when individual
array elements carry different constraints (e.g. a multi-word signature). Order entries
in template document order, top of file to bottom.

REQUIRED on every entry:
"type" fixed_value | enumerated_values | range_constraint |
calculated_value | pattern_constraint | bitmask_constraint
"description" one sentence: what the field is and what makes it valid
"corruption_risk" "high" — wrong value makes the file unparseable or rejected
"medium" — corrupts a section but the file still opens
"low" — cosmetic/metadata; tools tolerate a wrong value
"field_type" as declared in the .bt, e.g. "uint32", "char[4]", "ubyte", "WORD"
"source" "template" | "spec" | "both"
"evidence" {"line": <int>, "snippet": "<the .bt line, verbatim, trimmed>"}
for source "template"/"both"; for "spec", {"note": "<the rule>"}
"confidence" "high" | "medium" | "low"

REQUIRED per type:
fixed_value "required_value" (JSON number, or string for char[])
"required_value_hex" (width matches the field, e.g. "0x8950")
"required_value_ascii" (printable; non-printables as \\xNN)
enumerated_values "valid_values" (array of numbers or strings)
"value_names" (parallel array; include whenever the
enum has real names in the .bt)
range_constraint "min", "max" (inclusive; the TRUE spec bounds)
pattern_constraint "pattern" (regex or explicit textual rule)
bitmask_constraint "valid_bits", "valid_values"
calculated_value "algorithm" e.g. "CRC-32/ISO-HDLC", "byte count",
"absolute offset from file start", "sum mod 256"
"covers" exactly which bytes, in template terms, e.g.
"the chunk_type field plus chunk_data, excluding
the length field and the CRC itself"
"includes_self" true | false
"endianness" "big" | "little" | "n/a"
"depends_on" array of field keys whose values change it

OPTIONAL but high-value wherever they apply:
"generation_range" {"min": n, "max": n, "rationale": "..."}. Use when the spec bound
is far larger than what a generator should produce — dimensions,
counts, lengths, repeat bounds. `range_constraint.min/max` stays
the true spec bound; this is the practical bound for generation.
Getting this right is one of the highest-impact things in the
file: uncapped values produce huge, slow files and cut throughput.
"endianness" for multi-byte numeric fields
"evil_bit_safe" true | false. FormatFuzzer emits an out-of-set "evil" value with
probability 1/128. false means this field must NEVER receive one
(magic numbers, terminators, signatures); true means an invalid
value here still yields a file worth testing and may reach error
paths in the decoder.
"preferred_value" when generating, the value most likely to let a real decoder
reach deep parsing rather than bail early (e.g. compression
method 0 / stored). Use for enums whose options are not equally
productive; FormatFuzzer supports a preferred set distinct from
the merely-legal set.
"lookahead" {"function": "ReadUByte"|"ReadUShort"|"ReadByte"|"ReadBytes",
"call_site_line": N, "values": [...], "preferred": [...]}
when this field is decided by a lookahead call — FormatFuzzer
needs the per-call-site value set, not one global set
"notes" anything a template author would need that has no other home

### 3. `dependencies` (array) — conditional constraints across fields

One object per rule of the form "when some field has some value, another field's legal
set changes". This is what a flat per-field map cannot express, and what the rewrite step
turns into conditional declarations.

{"when": {"field": "PNG_CHUNK_IHDR.color_type", "equals": 3},
"then": {"field": "PNG_CHUNK_IHDR.bits",
"type": "enumerated_values", "valid_values": [1, 2, 4, 8]},
"description": "Indexed-colour images permit bit depths 1/2/4/8 only",
"source": "spec", "confidence": "high", "corruption_risk": "high"}

`when` may use "equals", "in", "min"/"max", or "present"/"absent" for whole sections.
`then` may constrain a field's values, or mark a section required/forbidden. Cover every
such rule you find — this is usually where a passive parser is laxest, and where a
generator most often produces individually-legal but collectively-invalid files.

### 4. `structure` (array) — document-level ordering and cardinality

One object per rule about which sections may appear, how often, and in what order. This
is what lets the rewrite step replace imperative `while` loops with declarative,
well-formed generation.

{"rule": "first_element" | "last_element" | "required" | "forbidden" |
"cardinality" | "ordering" | "mutually_exclusive" | "requires" | "contiguous",
"subject": "<struct name, or a field value such as chunk type \"IHDR\">",
"detail": "<the constraint, e.g. 'min 1, no spec maximum'; or 'must immediately
follow IHDR'>",
"condition": "<optional: only applies when ...>",
"description": "<one sentence>",
"corruption_risk": "high" | "medium" | "low",
"source": "template" | "spec" | "both",
"generation_bound": "<for repeating sections: a practical cap, with rationale.
Unbounded repetition is the most common way a generated file
becomes gigabytes. Always supply one for anything that repeats.>",
"generation_note": "<how a generator should satisfy this, e.g. 'emit as a fixed head
element, then a bounded repeated array, then a fixed tail'>"}

Cover at minimum: mandatory first/last elements, required sections, conditionally
required sections, sections that must be contiguous, count limits, and any ordering the
format imposes.

## Schema latitude

The schema above is a floor, not a ceiling. If a constraint in this format is not
expressible in it, invent what you need rather than distorting the constraint to fit or
dropping it — add keys to an entry, add a member to a section, or add a fifth top-level
section. The only requirement is that every addition is recorded in
`meta.schema_extensions` with its rationale, so the file stays self-describing. Prefer
extending over omitting. Do not rename or drop anything specified above; downstream
tooling reads those names.

## Hard rules

- Ground every key in the file. Never invent a struct or field name that does not appear
  in `templates_originals/{format}-orig.bt`.
- Every `evidence.line` must be a real line number, and `evidence.snippet` must be that
  line copied verbatim. If you cannot cite a line, set `"source": "spec"` and explain.
- Valid JSON, 2-space indent, no trailing commas, no comments, no markdown fences, no
  prose before or after the JSON.

## Completeness checklist — verify each before finishing

1. EVERY magic number, signature, section marker, block terminator, and field separator
   appears as a `fixed_value`. Re-scan the file specifically for these — the most
   important class, and the easiest to under-collect.
2. EVERY `typedef enum` is represented by at least one `enumerated_values` entry.
3. EVERY length, size, count, offset, CRC, checksum, or Adler field is a
   `calculated_value` with `algorithm`, `covers`, and `includes_self` filled in.
4. Every reserved/padding field is present as `fixed_value`.
5. Every field whose legal set varies with another field appears in `dependencies` —
   not only as prose inside a `description`.
6. `structure` names the mandatory first element, the mandatory last element, and every
   required section. If the format has none, say so explicitly in `meta.structure_note`.
7. Every repeating section in `structure` has a `generation_bound`, and every unbounded
   numeric field that controls a size or count has a `generation_range`.
8. Every key in `constraints` resolves to a real field in the .bt.
9. The file parses as JSON.

Then report in the chat only (not in the file): total `constraints` entries, count per
`type`, `dependencies` count, `structure` count, any schema extension made, and any
field judged constrained but deliberately excluded, with the reason.
