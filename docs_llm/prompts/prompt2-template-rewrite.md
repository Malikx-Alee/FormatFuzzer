Rewrite the 010 Editor binary template `templates_originals/{format}-orig.bt` into a
generative specification for FormatFuzzer, guided by the constraints in
`llm_learned_specification/llm_reterived_constraints_{format}-llm_opus5.json`.

Save the result to `templates_llm/{format}-llm.bt` (create the directory if needed).
Do not modify the original under `templates_originals/`.

## Independence requirement

Do NOT read `templates/{format}.bt`. That directory holds a hand-optimized version of
this same format, and this task is measuring what can be derived from the original plus
the extracted constraints alone. Reading it would invalidate the comparison. Your inputs
are exactly two files: the original template and the constraints JSON.

## Background: what FormatFuzzer does with this file

`ffcompile` compiles a .bt into C++ that is BOTH a generator and a parser. Every random
choice routes through `rand_int()`. When a field declares a set of good known values,
the generator picks uniformly from that set; otherwise it emits uniformly random bytes
of the field's width. So the entire job is: convert knowledge into declared value sets,
declared ranges, and declared structure.

Two properties must hold in the output, and the second is the one most easily lost:

1. It must still PARSE real files of this format correctly. The same .bt drives both
   directions — breaking the parser breaks round-tripping and the AFL+FFMut mutator.
2. It must TERMINATE and produce small files. An unbounded `while` or an uncapped
   length field yields multi-gigabyte outputs that stall the campaign.

## The FormatFuzzer idioms to use

Good known values on a field declaration — the primary mechanism:
UBYTE GIFTrailer = { 0x3B };
char Version[3] = { {"87a"}, {"89a"} };
CHAR bfType[2] = { "BM" };
DWORD biSize = { 40 };
ubyte bits = { 1, 2, 4, 8, 16 };

Value set held in a local array, applied via an attribute:
local UBYTE possible_values[] = { 0, 1 };
UBYTE LocalColorTableFlag : 1 <values=possible_values>;

Numeric bounds as attributes:
LONG biWidth <min=1>;
uint32 width <min=1, max=24>; // note the deliberately small generation cap
DWORD biClrUsed <max=256>;

Enum type, declared then used as the field's type:
typedef enum <WORD> bpp { One=1, Four=4, Eight=8, Sixteen=16, Thirtytwo=32 } E_BPP;
E_BPP biBitCount;

Protecting a magic value from the evil bit (FormatFuzzer otherwise emits an out-of-set
value with probability 1/128 — fatal for a signature, useful elsewhere):
local int evil = SetEvilBit(false);
CHAR bfType[2] = { "BM" };
SetEvilBit(evil);

Clearing ffcompile's auto-mined global lookahead values, so per-call-site sets win:
const local UBYTE ReadUByteInitValues[0];

Per-call-site lookahead value sets, and preferred-vs-possible sets:
local UBYTE values[] = { 0x2C, 0x21 };
while (ReadUByte(FTell(), values) != 0x3B) { ... }

    local string preferred_chunks[] = { "IHDR" };
    local string possible_chunks[]  = { "IHDR" };
    while (ReadBytes(chunk_type, FTell() + 4, 4, preferred_chunks, possible_chunks)) { ... }

Marking a field as the length of what follows:
uint32 length <arraylength=true>;

Backpatching a calculated field — record position, emit the data, seek back, rewrite:
uint32 length <arraylength=true>;
local int64 pos_start = FTell();
... emit type and data ...
local int64 pos_end = FTell();
local uint32 correct_length = pos_end - pos_start - 4;
if (length != correct_length) {
FSeek(pos_start - 4);
local int evil = SetEvilBit(false);
uint32 length = { correct_length };
SetEvilBit(evil);
FSeek(pos_end);
}
local uint32 crc_calc = Checksum(CHECKSUM_CRC32, pos_start, data_size);
uint32 crc = { crc_calc };

Bounding a repeating section so files stay small:
local int count = 0;
while (...) {
...
count += size;
if (count > 1500) {
local UBYTE values[] = { 0, 255 }; // steer the loop toward its terminator
}
}

Growing a value set once a precondition is met — this is how you express "the terminator
only becomes legal after at least one data block":
local int has_data = false;
...
if (!has_data) { has_data = true; possible += 0x3B; }

## How to consume each section of the JSON

**`constraints`**

- `fixed_value` → declare with `= { required_value }`, and wrap in
  `SetEvilBit(false)` / restore when `evil_bit_safe` is false or `corruption_risk`
  is "high". Signatures, markers and terminators always get this treatment.
- `enumerated_values` → if `value_names` is present, prefer emitting a
  `typedef enum <WIDTH>` and using it as the field's type; that is more readable and
  is what FormatFuzzer's mining works best with. Otherwise use `= { v1, v2, ... }`.
  If `preferred_value` is present, order or split the sets so the preferred value is
  reachable first.
- `range_constraint` → `<min=, max=>`. If `generation_range` is present, USE THE
  GENERATION RANGE in the attribute, and put the true spec bound in a trailing comment.
  This is deliberate: correctness of the file matters less than not producing a 4 GB
  output.
- `calculated_value` → never leave as a free field. Use `<arraylength=true>` for
  length-of-what-follows, or the backpatch pattern above, driven by `covers`,
  `includes_self` and `algorithm`. `Checksum(CHECKSUM_CRC32, start, size)` is
  available; see the algorithm named in the JSON.
- `pattern_constraint` / `bitmask_constraint` → the closest declarative equivalent;
  an explicit value list is usually better than an unconstrained field.
- `lookahead` → emit the value set as a `local` array at that call site, and add
  `const local <TYPE>ReadInitValues[0];` at the top if global mined values would
  otherwise override it.

**`dependencies`** → conditional declarations. Both of these forms work and both appear
in real optimized templates; pick whichever reads better for the rule:
if (biBitCount == 8) { E_COMPRESSIONS8BPP biCompression; }
else { E_COMPRESSIONS1BPP biCompression; }

    switch (ReadByte(FTell() + 1, color_types)) {
        case Indexed:   ubyte bits = { 1, 2, 4, 8 };   break;
        case TrueColor: ubyte bits = { 8, 16 };        break;
    }

Note the second form: a lookahead reads the _upcoming_ discriminator so the dependent
field can be constrained before either is emitted. Use it when the dependency runs
forward in the file. Every entry in `dependencies` must appear somewhere in the output.

**`structure`** → this drives the refactor from passive parsing to generation. For each
rule:

- `first_element` / `last_element` → emit as a fixed head/tail declaration outside the
  loop, not as another iteration the loop might or might not produce.
- `required` / `requires` → make it unconditional, or emit it inside the condition
  named by `condition`.
- `cardinality` / `contiguous` → a bounded repeated array, using `generation_bound`
  as the cap. Never leave a repeat unbounded.
- `ordering` → use the preferred/possible split so the generator walks the format's
  legal state machine rather than picking any section at random. The PNG idiom of
  switching `preferred_chunks` / `possible_chunks` as parsing advances past IHDR,
  PLTE and IDAT is the model to follow for any chunked format.
- `mutually_exclusive` / `forbidden` → express as branches, not as post-hoc checks.

**`meta.schema_extensions`** → read it. If the extraction added keys or a section, they
carry real constraints; act on them too.

## Rules

- Preserve the original's structure, naming, comments and formatting wherever a change
  is not required. This should read as a targeted edit of the original, not a rewrite
  from scratch. A reviewer must be able to diff the two files and see only optimizations.
- Do not delete parser-side validation (`Assert`, `error_message`, warnings). They are
  harmless during generation and keep the parse direction honest.
- Add a short comment on each non-obvious edit naming the constraint it implements.
- Keep every `struct`/field identifier from the original unless the JSON's structural
  rules genuinely require a new one — the generated C++, and anything keyed on those
  names, depends on them.

## Verify before you finish

Run these from the repo root and fix anything that fails:

    ./ffcompile templates_llm/{format}-llm.bt /tmp/{format}-llm-check.cpp
      # must exit 0 and print "Finished creating cpp generator".
      # "*ERROR:"/"*WARNING:" lines from the template's own error_message() calls are
      # EXPECTED here and harmless — ffcompile parses against empty dummy input, so
      # every validity check in the template fires. Judge by the exit code.

    ./build_new.sh {format}-llm
      # must produce build/{format}-llm-fuzzer and build/{format}-llm.so

    mkdir -p /tmp/{format}-llm-out
    ./build/{format}-llm-fuzzer fuzz /tmp/{format}-llm-out/f{1..200}.{ext}
      # 200 files, all produced, none pathologically large. Check with:
      #   ls -lS /tmp/{format}-llm-out | head
      # If any file exceeds a few hundred KB, a repeat or length field is still
      # unbounded — go back and apply the generation bound.

    ./build/{format}-llm-fuzzer parse /tmp/{format}-llm-out/f1.{ext}
      # the parse direction must still work on the generator's own output

    bash checkers/{format}.sh /tmp/{format}-llm-out/f1.{ext}
      # if a checker exists for this format, spot-check validity on a handful of files

({ext} is the format's file extension — note `midi` produces `.mid` files.)

Then report in the chat: which constraints, dependencies and structure rules you
implemented and how; anything in the JSON you could NOT express in the template language,
with the reason; the results of each verification command above; and the size of the
largest generated file.
