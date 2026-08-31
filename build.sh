#!/bin/bash

export CPLUS_INCLUDE_PATH=$(brew --prefix boost)/include:$CPLUS_INCLUDE_PATH

mkdir -p build

# Produce format-specific C++ code
./ffcompile templates/$1.bt $1.cpp
# Only touch png.cpp when actually building png - this used to run
# unconditionally for every format, which is harmless when nothing else is
# building concurrently but races against a concurrently-running `build.sh
# png` (or target_coverage*.py invocation that shells out to it): an
# unrelated format's build would revert png.cpp to its last-committed state
# mid-build, right as the real png build might be about to compile it.
if [ "$1" = "png" ]; then
    git checkout -- png.cpp
fi

# Build format-specific executable
g++ -c -I . -std=c++17 -g -O3 -Wall fuzzer.cpp -o build/fuzzer.o
g++ -c -I . -std=c++17 -g -O3 -Wall $1.cpp -o build/$1.o
g++ -O3 build/$1.o build/fuzzer.o -o build/$1-fuzzer -lz

# Build format-specific shared library
g++ -I . -std=c++17 -g -O3 -Wall -shared -fPIC $1.cpp fuzzer.cpp -o build/$1.so -lz
