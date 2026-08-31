#!/usr/bin/env python3
"""Run a time-boxed AFL+FFMut campaign for one FormatFuzzer format, using the
pre-optimization templates (templates_llm/<fmt>-llm.bt), measuring
real-world target-program (gcov/lcov) code coverage in periodic batched
snapshots.

This is the sibling of target_coverage_afl_ffmut.py (see its module
docstring for the full design, flag set, and known gaps) - the only
difference is which FormatFuzzer template/.so gets fuzzed: this script
builds <fmt>-llm.so via ./build_new.sh <fmt>-llm instead of <fmt>.so via
./build.sh <fmt>, and writes results under an "-llm-afl-ffmut" suffix
instead of "-afl-ffmut", mirroring the existing
target_coverage.py / target_coverage_llm.py optimized-vs-llm split.

Run once per format:

    python3 scripts/target_coverage_afl_ffmut_llm.py png

Everything else (CLI flags, snapshot mechanics, deferred/untested caveats)
is identical and lives in target_coverage_afl_ffmut.py, which this script
imports and reuses rather than duplicating.
"""
from target_coverage_afl_ffmut import LLM, main

if __name__ == "__main__":
    main(LLM)
