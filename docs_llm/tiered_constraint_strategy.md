# The tiered constraint strategy

Why the constraint-extraction and template-rewrite prompts were rewritten, what the
first attempt got wrong, and the model that replaces it.

Companion documents: `prompts/prompt1-constraint-extraction-tiered.md`,
`prompts/prompt2-template-rewrite-tiered.md`, and
`target_coverage_driver_audit.md` (the measurement fixes that had to land first).

---

## 1. What we were trying to do

FormatFuzzer compiles a 010 Editor `.bt` template into a C++ file generator. A template
written as a *passive parser* — which is what `templates_originals/<fmt>-orig.bt` is —
describes how to read a file, not how to write one. Any field it leaves undescribed gets
filled with uniformly random bytes at generation time.

The two-prompt pipeline turns a parser into a generator:

1. **Prompt 1** reads the parser template and extracts a machine-readable constraint
   specification as JSON.
2. **Prompt 2** consumes that JSON and rewrites the template into a generative one.

The output is measured by generating files, feeding them to a real decoder (libpng,
giflib, WavPack, …) and recording line coverage of that decoder.

## 2. What the first attempt did, and what it cost

The original Prompt 1 asked for a `generation_range` on any field whose spec bound was
larger than what "a generator should produce":

> *Spec-legal is not the same as generation-practical. A field the spec allows to reach
> 2^31-1 (an image dimension, a repeat count, a chunk length) will, if generated
> uniformly, produce enormous files that dominate runtime and reduce the number of test
> inputs produced.*
>
> — `prompts/prompt1-constraint-extraction.md`, lines 35–39

The reasoning is not obviously wrong. It is, however, wrong in a way that the measurement
exposed sharply. Results from the same model (Opus 5) on two formats:

| format | hand-optimized | opus5 | Δ |
|---|---:|---:|---:|
| png | 21.3% | **29.5%** | **+8.2** |
| gif | 25.1% | **23.4%** | **−1.7** |

*(Generation-only measurement, 2,000-file corpora. The gif figures are means of three
repetitions — spreads 0.2 and 0.1 respectively, so the 1.7-point gap is far outside
run-to-run noise. These were diagnostic runs and are not persisted in
`coverage_results/`; re-running the generation-only matrix is outstanding work.)*

Same model, same prompt, opposite signs. The supporting numbers make the mechanism plain:

| format | variant | valid % | avg file size |
|---|---|---:|---:|
| gif | hand | 1.7% | 5,919 B |
| gif | opus5 | **99.1%** | **976 B** |
| png | hand | 0.0% | 284 B |
| png | opus5 | **95.7%** | 3,317 B |

opus5's gif corpus is **99.1% valid and covers less** than a hand corpus that is 1.7%
valid. Validity and coverage are not monotonically related, and optimising for the former
is not the same as optimising for the latter.

### The two failures have one root cause

**png.** The hand template writes random bytes into `IDAT`. Random bytes are never a
valid zlib stream, so libpng stops at `IDAT: invalid window size` before the pixel
pipeline runs at all. opus5 recorded that `IDAT` must contain a real zlib stream, the
rewrite emitted one, and the decoder actually executed. That is the +8.2.

**gif.** opus5 emitted `ushort ImageWidth = { 1, 2, 4, 8 };` where both the original
parser and the hand-tuned expert leave the field bare. Every file came out 976 bytes and
much like the last one. That is the −1.7.

The gif template explains itself in a comment:

```c
// C16/C17/DEV05: a decoder allocates ImageWidth*ImageHeight index
// bytes per frame.  The set is restricted to powers of two up to 8
// so the pixel count is one of the seven the LZW payloads cover.
```

— `templates_llm/llm_opus5/gif-llm.bt`, lines 462–466

This is the whole finding in three lines. The model faced the *same* problem on both
formats: **a payload must agree with a declared dimension.** On png it generated the
payload from the data. On gif it shrank the data until a handful of precomputed payloads
fit. One answer gained 8.2 points; the other lost 1.7.

### Secondary faults found alongside it

| fault | cost |
|---|---|
| No size or complexity budget — opus5's gif template is 4.8× the original's length | structural; more template means more pinned fields |
| No measurement gate — templates went from generation straight to an 8h campaign | 8h per undetected regression |
| Validity used as a proxy for coverage | directional error, as the table above shows |
| The evil bit investigated as a lever | no-op: `allow_evil_values` already defaults true; toggling moves validity ≤2.7 points |

## 3. The framing

### Coverage needs depth × diversity

Line coverage of a decoder requires two things simultaneously:

- **Depth** — a file must get past the decoder's front gate. A wrong magic number, a
  broken length, a bad CRC or a malformed compressed payload, and the decoder exits
  having executed almost nothing.
- **Diversity** — the files must differ from each other in ways the decoder's control
  flow can feel. A thousand near-identical valid files reach the same lines a thousand
  times.

**Constraining a field buys depth and costs diversity.** Neither is free, and neither is
universally correct. png was depth correctly bought; gif was diversity needlessly sold.

The question is therefore not *how much* to constrain. It is *which fields*.

### A one-dimensional accuracy axis is the wrong model

The natural framing — "how accurate should the template be?" — cannot express either
result. It predicts that more accuracy monotonically helps (contradicted by gif) or that
it monotonically hurts (contradicted by png). The fields have to be separated by *kind*.

This also sharpens the claim available to the thesis. "Over-restriction does not yield
good results" is contradicted by the png row of our own table. The defensible claim is:

> **Restriction helps at the decoder's gate and hurts past it. The question is not how
> much to constrain, but what.**

### The three tiers

**Tier A — pin exactly.** The decoder's front gate. One mechanical test decides
membership:

> *If I write a wrong value into this field, does a conforming decoder refuse the file,
> or stop before doing useful work?*

Magic numbers, signatures, markers, terminators, lengths, CRCs and checksums — and
**payload well-formedness**, the internal structure of a compressed or encoded blob. The
last of these is the highest-value item and the most often missed, because a `.bt`
typically declares such a payload as an opaque byte array and says nothing about its
contents.

**Tier B — the full legal set, never a subset.** Finite enumerations: enums, flag bytes,
compression methods, colour types, filter and interlace methods. Every value is usually a
distinct branch in the decoder, so narrowing to "the ones that work" deletes branches on
purpose. Values that lead to shallower parses are still emitted; a `preferred_value` names
the better ones without removing the rest.

**Tier C — leave completely free.** Dimensions, counts, repetitions, sample rates,
colours, text, timestamps. No value set, no minimum, no maximum. This is where diversity
comes from and the only place it can come from.

Ties break toward C. Over-constraining is the documented failure; under-constraining a
Tier C field costs nothing, because a strange dimension still produces a file the decoder
will read.

### The payload-derivation rule

The rule that unifies both measurements, and the highest-priority instruction in the new
prompts:

> **When a payload must agree with a dimension, a count or a length, derive the payload
> from that value. Never shrink the value to fit a fixed payload.**

The corollary that makes it affordable: the bytes *inside* a well-formed stream are
unconstrained even though the stream's framing is Tier A. **Pin the envelope, free the
contents.** A deflate *stored* block or an LZW clear-code run is valid, trivial to emit
for any size, and carries arbitrary bytes — which is how a format gets depth and
diversity at the same time.

### Size is bounded by output budget, never by field caps

Total output size is controlled by a running byte budget on the repeating structure that
actually produces the bytes, checked and stopped at during generation. It is never
controlled by narrowing the fields that make files different from one another. This is
the mechanism that replaces `generation_range` — it addresses the same legitimate concern
(runaway file sizes) without paying in diversity.

## 4. What changed in the prompts

Both original prompts are retained unchanged; the tiered versions sit alongside them as a
separate strategy, so the comparison can be run as **opus5 vs opus5-tiered** with the
prompt as the only variable.

| | original | tiered |
|---|---|---|
| `generation_range` | requested, "one of the highest-impact things in the file" | **removed and explicitly forbidden**, with four synonyms named |
| tier | — | `tier` + `tier_rationale` required on every entry |
| compressed payloads | not modelled | `payload_wellformedness` entry type with `codec`, `decoder_gate`, byte-level `generation_strategy`, `derives_from`, `content_is_free` |
| what must stay free | not expressed | `diversity_axes` section |
| size control | per-field `generation_range` | `output_budget` on repeating structures only |
| Tier C fields | omitted entirely ("emit an entry only for constrained fields") | emitted as `"type": "unconstrained"` so the rewrite has a positive instruction to leave them alone |
| template size | unbounded | ceiling of 1.5× the original's length |
| verification | none | mandatory rebuild-and-measure gate that rejects regressions |

## 5. How this gets measured

**Line coverage stays the primary metric. Time-to-coverage is secondary.** The re-run of
gif and wav on fixed drivers exposed a limit in the primary metric that the secondary one
covers.

On gif, all three template variants converge on **exactly 624 of 2,138 lines** by
t = 10,800 s in an 8-hour AFL campaign, and then do not move for five more hours —
despite running 7.3M, 17.5M and 4.7M executions. The endpoint reports a perfect
three-way tie. At t = 300 s the same three sit at 563, 559 and **536** lines, with opus5
measurably behind, consistent with its over-constrained template.

On wav the endpoints (22.5 / 22.5 / 22.3%) differ by what looks like a rounding error,
but the hand template reaches 2,275 lines in **1,500 s** where opus5 needs **27,300 s** —
eighteen times longer for the same coverage. That ordering is not a throughput artifact:
opus5 executed the *most* test cases of the three on wav.

Two consequences for how the tiered templates are validated:

1. **Validate on generation-only coverage, not on 8-hour AFL campaigns.** AFL's own
   mutation erases the template's contribution on small targets. An 8h gif run would
   return a three-way tie and tell us nothing.
2. **Report the saturation curve**, not only the endpoint — coverage at 100 / 500 /
   2,000 / 10,000 files. A template that saturates early is diversity-poor even when its
   endpoint looks respectable, and the curve exposes it from a five-minute run instead of
   an eight-hour one.

## 6. What would falsify this

The model makes specific, checkable predictions. Validation runs on three formats chosen
so each can break a different part of it:

| format | tests | fails if |
|---|---|---|
| **gif** | that loosening Tier C recovers diversity | gif does not recover ≥1.0 point |
| **png** | that the Tier A win survives the loosening | png does not hold ≥+6 |
| **zip** | the hardest structural case — nested lengths, CRCs, a central directory that must agree with what precedes it | the tiers cannot express the dependency |

If gif recovers but png collapses, the tiers interfere and the boundary between A and C
is drawn in the wrong place. If neither moves, the mechanism is not what we think it is
and the diagnosis in §2 is wrong. Either outcome is a result worth reporting; the model
is stated this way so that it can produce one.

## 7. Status

- Prompt 1 (tiered): written — `prompts/prompt1-constraint-extraction-tiered.md`
- Prompt 2 (tiered): written — `prompts/prompt2-template-rewrite-tiered.md`
- Driver audit and re-runs: complete, see `target_coverage_driver_audit.md`
- Generation-only baseline on audited drivers: **outstanding**. The png and gif figures
  in §2 are diagnostic measurements, not a persisted result set, and the existing
  `coverage_results/*-orig` directories predate both the model axis and the driver fixes.
- Three-format validation: not started.
