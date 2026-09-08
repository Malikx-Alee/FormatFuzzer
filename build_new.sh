#!/bin/bash
#
# Build a fuzzer + shared library from an LLM-generated 010 Editor template.
#
#   ./build_new.sh png-llm                      # uses LLM_MODEL below
#   LLM_MODEL=opus4.7 ./build_new.sh png-llm    # pick a different model's set
#
# templates_llm/ holds one subdirectory per model that generated the
# templates (llm_opus4.7/, llm_opus5/, ...). The model is part of every
# artifact name - png-llm built from llm_opus5 produces
# build/png-llm-opus5{-fuzzer,.so} and png-llm-opus5.cpp - so two models'
# builds of the same format never overwrite each other and can run
# concurrently.
#
# Exits non-zero on the first failing step. It previously did not: with no
# `set -e`, a failing ./ffcompile (e.g. after templates_llm/ was reorganised
# into per-model subdirectories, invalidating the old flat path) left the
# script happily compiling whatever stale <format>.cpp was still lying around
# in the repo root, producing a fuzzer built from an outdated template while
# reporting success.
set -euo pipefail

# ---------------------------------------------------------------------------
# Which model's generated templates to build from. This is the tag appended to
# every artifact this script produces, and it selects the templates_llm/
# subdirectory to read. Edit this line to change the default, or override it
# per-invocation via the environment (see usage above).
#
# LLM_TEMPLATE_DIR is derived from it and only needs setting directly if the
# directory does not follow the llm_<model> convention.
# ---------------------------------------------------------------------------
LLM_MODEL="${LLM_MODEL:-opus5}"
LLM_TEMPLATE_DIR="${LLM_TEMPLATE_DIR:-templates_llm/llm_${LLM_MODEL}}"

list_models() {
    ls -d templates_llm/llm_* 2>/dev/null | sed 's#templates_llm/llm_##; s/^/    /' >&2
}

if [ $# -lt 1 ]; then
    echo "usage: $0 <format>-llm    (e.g. $0 png-llm)" >&2
    echo "  LLM_MODEL is currently '${LLM_MODEL}'; available models:" >&2
    list_models
    echo "  formats available in ${LLM_TEMPLATE_DIR}:" >&2
    ls "${LLM_TEMPLATE_DIR}" 2>/dev/null | sed 's/\.bt$//; s/^/    /' >&2
    exit 2
fi

if [ ! -d "${LLM_TEMPLATE_DIR}" ]; then
    echo "ERROR: no such template directory: ${LLM_TEMPLATE_DIR}" >&2
    echo "  LLM_MODEL is currently '${LLM_MODEL}'; available models:" >&2
    list_models
    exit 1
fi

TEMPLATE="${LLM_TEMPLATE_DIR}/$1.bt"
if [ ! -f "${TEMPLATE}" ]; then
    echo "ERROR: no such template: ${TEMPLATE}" >&2
    echo "  LLM_MODEL is currently '${LLM_MODEL}'; available models:" >&2
    list_models
    echo "  formats available in ${LLM_TEMPLATE_DIR}:" >&2
    ls "${LLM_TEMPLATE_DIR}" 2>/dev/null | sed 's/\.bt$//; s/^/    /' >&2
    exit 1
fi

# Every artifact carries the model tag, so opus4.7 and opus5 builds of the
# same format neither overwrite each other nor race when run concurrently.
# This includes the generated .cpp, which is written into the repo root.
OUT="$1-${LLM_MODEL}"

# Homebrew only supplies boost on macOS. Guarded so that on Linux - where
# libboost-dev installs into the standard /usr/include that g++ already
# searches - a missing `brew` is a no-op instead of aborting under `set -e`.
if command -v brew >/dev/null 2>&1; then
    export CPLUS_INCLUDE_PATH="$(brew --prefix boost)/include:${CPLUS_INCLUDE_PATH:-}"
fi

mkdir -p build

echo "[build_new] model: ${LLM_MODEL}   template: ${TEMPLATE}   artifacts: build/${OUT}*"

# Produce format-specific C++ code
./ffcompile "${TEMPLATE}" "${OUT}.cpp"
# (build.sh has a `git checkout -- png.cpp` here, needed because templates/
# png.bt's regeneration needs reverting to a hand-fixed committed png.cpp -
# not carried over here: the LLM template sets hold no bare "png.bt", only
# "png-llm.bt", so $1 is always "*-llm" and $1.cpp is never literally
# png.cpp - the line would just unconditionally stomp on an unrelated
# file on every build, including racing a concurrently-running png build.)

# Build format-specific executable.
# fuzzer.o is named per-format for the same reason as in build.sh: a single
# shared build/fuzzer.o made concurrent builds (notably build.sh png and
# build_new.sh png-llm running at once) clobber each other mid-link.
g++ -c -I . -std=c++17 -g -O3 -Wall fuzzer.cpp -o "build/fuzzer-${OUT}.o"
g++ -c -I . -std=c++17 -g -O3 -Wall "${OUT}.cpp" -o "build/${OUT}.o"
g++ -O3 "build/${OUT}.o" "build/fuzzer-${OUT}.o" -o "build/${OUT}-fuzzer" -lz

# Build format-specific shared library
g++ -I . -std=c++17 -g -O3 -Wall -shared -fPIC "${OUT}.cpp" fuzzer.cpp -o "build/${OUT}.so" -lz

echo "[build_new] built build/${OUT}-fuzzer and build/${OUT}.so from ${TEMPLATE}"
