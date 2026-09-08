your_string = """
"""

lines = your_string.splitlines()

entries = []

# Step 1: Parse all lines into structured format
for line in lines:
    parts = line.split(',')
    if len(parts) < 3:
        continue  # Skip bad lines
    start, end, label = int(parts[0]), int(parts[1]), parts[2]
    entries.append((start, end, label, line))

# Step 2: Sort entries by start byte
# Step 2: Sort by start ASCENDING and end DESCENDING
entries.sort(key=lambda x: (x[0], -x[1]))

print("Sorted Entries:")
print("\n".join(line for _, _, _, line in entries))

# Step 3: Filter out child entries
filtered = []
current_parent_end = -1

for start, end, label, line in entries:

    # Split attribute into hierarchical keys
    attribute_keys = label.split("~")

                # Skip if the attribute path has only two levels (e.g., "file~GifHeader")
                # if len(attribute_keys) <= 2:
                #     continue

    if start == end and "_" in label:
        continue

    if (start > current_parent_end or end < current_parent_end) and end - start <= 8:
        # No overlap with previous parent
        filtered.append(line)
        current_parent_end = end
    else:
        # This entry is inside an earlier parent, so skip
        continue

# `filtered` now has your required lines

print("Filtered Entries:")
print("\n".join(filtered))


