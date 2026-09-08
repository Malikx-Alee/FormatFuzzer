#!/usr/bin/env python3
"""Run time-boxed AFL+FFMut campaigns using LLM-generated templates
(templates_llm/llm_<model>/<fmt>-llm.bt), measuring real-world target-program
(gcov/lcov) code coverage in periodic batched snapshots.

This is the sibling of target_coverage_afl_ffmut.py (see its module docstring
for the full design, flag set, and known gaps) - the only difference is which
FormatFuzzer template/.so gets fuzzed. This script builds
<fmt>-llm-<model>.so via `LLM_MODEL=<model> ./build_new.sh <fmt>-llm` instead
of <fmt>.so via ./build.sh <fmt>, and writes results under an
"-llm-<model>-afl-ffmut" suffix instead of "-afl-ffmut".

templates_llm/ holds one subdirectory per model that generated the templates
(llm_opus4.7/, llm_opus5/, ...). Pick one with --llm-model, or change the
LLM_MODEL constant at the top of target_coverage_afl_ffmut.py. Because the
model tag is part of every output path, campaigns for different models - and
the optimized campaign - are fully isolated and safe to run at the same time:

    python3 scripts/target_coverage_afl_ffmut_llm.py png --llm-model opus5
    python3 scripts/target_coverage_afl_ffmut_llm.py png --llm-model opus4.7
    python3 scripts/target_coverage_afl_ffmut.py     png

all three can run concurrently, writing to coverage_results/png-llm-opus5-afl-ffmut/,
coverage_results/png-llm-opus4.7-afl-ffmut/ and coverage_results/png-afl-ffmut/.

Choose formats by editing the FORMATS list at the top of
target_coverage_afl_ffmut.py (both scripts share it), or by naming them on
the command line, which always wins:

    python3 scripts/target_coverage_afl_ffmut_llm.py png
    python3 scripts/target_coverage_afl_ffmut_llm.py png zip gif
    python3 scripts/target_coverage_afl_ffmut_llm.py --all

Use --list to see supported formats and the available model template sets.

Everything else (CLI flags, snapshot mechanics, deferred/untested caveats)
is identical and lives in target_coverage_afl_ffmut.py, which this script
imports and reuses rather than duplicating.
"""
from target_coverage_afl_ffmut import llm_variant_for, main

if __name__ == "__main__":
    main(llm_variant_for)
