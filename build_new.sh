#!/bin/bash

export CPLUS_INCLUDE_PATH=$(brew --prefix boost)/include:$CPLUS_INCLUDE_PATH

mkdir -p build

# Produce format-specific C++ code
./ffcompile templates_originals_llm/$1.bt $1.cpp
git checkout -- png.cpp

# Build format-specific executable
g++ -c -I . -std=c++17 -g -O3 -Wall fuzzer.cpp -o build/fuzzer.o
g++ -c -I . -std=c++17 -g -O3 -Wall $1.cpp -o build/$1.o
g++ -O3 build/$1.o build/fuzzer.o -o build/$1-fuzzer -lz

# Build format-specific shared library
g++ -I . -std=c++17 -g -O3 -Wall -shared -fPIC $1.cpp fuzzer.cpp -o build/$1.so -lz
