#!/usr/bin/env python3
"""Debug script to verify blacklist fix in parallel processing."""
import sys
sys.path.insert(0, '.')

from learning_constraints.utils import (
    clean_attribute_key, clean_keys_list, insert_nested_dict,
    convert_sets_to_lists, filter_blacklisted_attributes
)
from learning_constraints.config import GlobalState, Config
from learning_constraints.parallel import merge_global_states, _enforce_unique_values_limit
import json

print("=== Testing parallel processing blacklist fix ===\n")
print(f"MAX_UNIQUE_VALUES_PER_ATTRIBUTE: {Config.MAX_UNIQUE_VALUES_PER_ATTRIBUTE}")

# Create main state (simulating main process)
main_state = GlobalState()

# Simulate 40 workers each adding 1 unique value for timeYear
print(f"\n=== Simulating 40 workers each adding 1 value ===")

for worker_id in range(40):
    # Simulate a worker's state
    worker_state = GlobalState()

    # Each worker adds 1 unique value for timeYear
    attr = "file~chunk~time~timeYear"
    attr_keys = attr.split("~")
    hex_val = f"{worker_id:04x}"
    insert_nested_dict(worker_state.nested_values_hex, attr_keys, hex_val)

    # Convert to dict (as happens when returning from worker)
    worker_dict = worker_state.to_dict()

    # Merge into main state (as happens in main process)
    merge_global_states(main_state, worker_dict)

    # Track what happens at each step
    vals = main_state.nested_values_hex.get('file', {}).get('chunk', {}).get('time', {}).get('timeYear', set())
    count = len(vals) if isinstance(vals, set) else 0
    if worker_id >= 28 and worker_id <= 35:
        print(f"  After worker {worker_id}: values={count}, blacklisted={main_state.blacklisted_by_count}")

# Check the results
print(f"\n=== After merging all 40 workers ===")
print(f"Blacklisted by count: {main_state.blacklisted_by_count}")
vals = main_state.nested_values_hex.get('file', {}).get('chunk', {}).get('time', {}).get('timeYear', set())
count = len(vals) if isinstance(vals, set) else 0
print(f"Values remaining in timeYear: {count}")

if count == 0:
    print(f"\n✅ FIX VERIFIED: No values remain after blacklisting!")
    print(f"   - Workers 31-40 values were correctly SKIPPED during merge")
else:
    print(f"\n❌ FIX NOT WORKING: {count} values still remain after blacklisting")

# Also test the filter function (belt and suspenders)
print(f"\n=== Testing filter_blacklisted_attributes ===")
final_stats = convert_sets_to_lists(main_state.nested_values_hex)
filtered_stats = filter_blacklisted_attributes(final_stats, main_state.blacklisted_attributes)
print(f"Before filter: {json.dumps(final_stats, indent=2)[:500]}")
print(f"After filter:  {json.dumps(filtered_stats, indent=2)[:500]}")

print("\n=== Summary ===")
print("✅ Fix implemented in two places:")
print("   1. _merge_nested_values() now skips blacklisted attributes during merge")
print("   2. save_results() now filters blacklisted attributes before saving to JSON")

