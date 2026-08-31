#!/bin/bash

export CPLUS_INCLUDE_PATH=$(brew --prefix boost)/include:$CPLUS_INCLUDE_PATH

mkdir -p build

# Produce format-specific C++ code
./ffcompile templates_llm/$1.bt $1.cpp
# (build.sh has a `git checkout -- png.cpp` here, needed because templates/
# png.bt's regeneration needs reverting to a hand-fixed committed png.cpp -
# not carried over here: templates_llm/ has no bare "png.bt", only
# "png-llm.bt", so $1 is always "*-llm" and $1.cpp is never literally
# png.cpp - the line would just unconditionally stomp on an unrelated
# file on every build, including racing a concurrently-running png build.)

# Build format-specific executable
g++ -c -I . -std=c++17 -g -O3 -Wall fuzzer.cpp -o build/fuzzer.o
g++ -c -I . -std=c++17 -g -O3 -Wall $1.cpp -o build/$1.o
g++ -O3 build/$1.o build/fuzzer.o -o build/$1-fuzzer -lz

# Build format-specific shared library
g++ -I . -std=c++17 -g -O3 -Wall -shared -fPIC $1.cpp fuzzer.cpp -o build/$1.so -lz
