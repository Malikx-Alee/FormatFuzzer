#!/bin/bash
#
# Build a fuzzer + shared library from a FormatFuzzer-optimized template.
#
#   ./build.sh png
#
# Exits non-zero on the first failing step. Without `set -e` a failing
# ./ffcompile leaves the script compiling whatever stale <format>.cpp is still
# in the repo root, producing a fuzzer built from an outdated template while
# reporting success.
set -euo pipefail

if [ $# -lt 1 ]; then
    echo "usage: $0 <format>    (e.g. $0 png)" >&2
    echo "available in templates/:" >&2
    ls templates/*.bt 2>/dev/null | sed 's#templates/##; s/\.bt$//; s/^/  /' >&2
    exit 2
fi

if [ ! -f "templates/$1.bt" ]; then
    echo "ERROR: no such template: templates/$1.bt" >&2
    echo "  available:" >&2
    ls templates/*.bt 2>/dev/null | sed 's#templates/##; s/\.bt$//; s/^/    /' >&2
    exit 1
fi

# Homebrew only supplies boost on macOS. Guarded so that on Linux - where
# libboost-dev installs into the standard /usr/include that g++ already
# searches - a missing `brew` is a no-op instead of aborting under `set -e`.
if command -v brew >/dev/null 2>&1; then
    export CPLUS_INCLUDE_PATH="$(brew --prefix boost)/include:${CPLUS_INCLUDE_PATH:-}"
fi

mkdir -p build

# Produce format-specific C++ code
./ffcompile "templates/$1.bt" "$1.cpp"
# Only touch png.cpp when actually building png - this used to run
# unconditionally for every format, which is harmless when nothing else is
# building concurrently but races against a concurrently-running `build.sh
# png` (or target_coverage*.py invocation that shells out to it): an
# unrelated format's build would revert png.cpp to its last-committed state
# mid-build, right as the real png build might be about to compile it.
if [ "$1" = "png" ]; then
    # `|| true`: not being in a git checkout (e.g. an unpacked release tarball)
    # must not abort the build now that `set -e` is in force.
    git checkout -- png.cpp || true
fi

# Build format-specific executable.
# fuzzer.o is named per-format even though its content is format-independent:
# build.sh and build_new.sh both used to write a single build/fuzzer.o, so
# building two formats concurrently (e.g. the optimized and llm AFL campaigns
# for one format, started together) had them truncate each other's object file
# mid-link. Per-format names cost a little redundant compilation and make
# concurrent builds safe.
g++ -c -I . -std=c++17 -g -O3 -Wall fuzzer.cpp -o build/fuzzer-$1.o
g++ -c -I . -std=c++17 -g -O3 -Wall $1.cpp -o build/$1.o
g++ -O3 build/$1.o build/fuzzer-$1.o -o build/$1-fuzzer -lz

# Build format-specific shared library
g++ -I . -std=c++17 -g -O3 -Wall -shared -fPIC $1.cpp fuzzer.cpp -o build/$1.so -lz
