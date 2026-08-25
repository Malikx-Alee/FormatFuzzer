#!/bin/bash

# Check benchmark progress
echo "=== Benchmark Progress ==="
echo "Active processes:"
ps aux | grep -E "python3|g\+\+|ffcompile" | grep -v grep | wc -l

echo -e "\nFuzzer binaries created:"
ls -1 *-fuzzer 2>/dev/null | wc -l

echo -e "\nOutput directories:"
find output -maxdepth 2 -type d -name "20*" | wc -l

echo -e "\nRecent report files:"
find output -name "report.json" -type f -mmin -30 | wc -l

echo -e "\nReport file exists:"
[ -f BENCHMARK_REPORT.md ] && echo "✅ BENCHMARK_REPORT.md found" || echo "❌ Still generating..."
