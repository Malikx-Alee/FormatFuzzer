your_string = """0,3,file~record~frSignature
4,4,file~record~frVersion~Version
5,5,file~record~frVersion~HostOS
4,5,file~record~frVersion
6,7,file~record~frFlags
8,9,file~record~frCompression
10,11,file~record~frFileTime
12,13,file~record~frFileDate
14,17,file~record~frCrc
18,21,file~record~frCompressedSize
22,25,file~record~frUncompressedSize
26,27,file~record~frFileNameLength
28,29,file~record~frExtraFieldLength
30,37,file~record~frFileName
FSeek from 38 to 28
28,29,file~record~frExtraFieldLength_1
FSeek from 30 to 38
38,2047,file~record~frData
FSeek from 2048 to 14
14,17,file~record~frCrc_1
FSeek from 18 to 2048
0,2047,file~record,Optional
Generated record 0
2048,2051,file~dirEntry~deSignature
2052,2052,file~dirEntry~deVersionMadeBy~Version
2053,2053,file~dirEntry~deVersionMadeBy~HostOS
2052,2053,file~dirEntry~deVersionMadeBy
2054,2054,file~dirEntry~deVersionToExtract~Version
2055,2055,file~dirEntry~deVersionToExtract~HostOS
2054,2055,file~dirEntry~deVersionToExtract
2056,2057,file~dirEntry~deFlags
2058,2059,file~dirEntry~deCompression
2060,2061,file~dirEntry~deFileTime
2062,2063,file~dirEntry~deFileDate
2064,2067,file~dirEntry~deCrc
2068,2071,file~dirEntry~deCompressedSize
2072,2075,file~dirEntry~deUncompressedSize
2076,2077,file~dirEntry~deFileNameLength
2078,2079,file~dirEntry~deExtraFieldLength
2080,2081,file~dirEntry~deFileCommentLength
2082,2083,file~dirEntry~deDiskNumberStart
2084,2085,file~dirEntry~deInternalAttributes
2086,2089,file~dirEntry~deExternalAttributes
2090,2093,file~dirEntry~deHeaderOffset
2094,2101,file~dirEntry~deFileName
2102,2103,file~dirEntry~deExtraField~efHeaderID
2104,2105,file~dirEntry~deExtraField~efDataSize
102106,2109,file~dirEntry~deExtraField~Reserved
2110,2111,file~dirEntry~deExtraField~Tag
2112,2113,file~dirEntry~deExtraField~Size
2114,2117,file~dirEntry~deExtraField~Mtime~dwLowDateTime
2118,2121,file~dirEntry~deExtraField~Mtime~dwHighDateTime
2114,2121,file~dirEntry~deExtraField~Mtime
2122,2125,file~dirEntry~deExtraField~Atime~dwLowDateTime
2126,2129,file~dirEntry~deExtraField~Atime~dwHighDateTime
2122,2129,file~dirEntry~deExtraField~Atime
2130,2133,file~dirEntry~deExtraField~Ctime~dwLowDateTime
2134,2137,file~dirEntry~deExtraField~Ctime~dwHighDateTime
2130,2137,file~dirEntry~deExtraField~Ctime
FSeek from 2138 to 2112
2112,2113,file~dirEntry~deExtraField~Size_1
FSeek from 2114 to 2138
FSeek from 2138 to 2104
2104,2105,file~dirEntry~deExtraField~efDataSize_1
FSeek from 2106 to 2138
2102,2137,file~dirEntry~deExtraField
FSeek from 2138 to 2078
2078,2079,file~dirEntry~deExtraFieldLength_1
FSeek from 2080 to 2138
2048,2137,file~dirEntry,Optional
2138,2141,file~endLocator~elSignature
2142,2143,file~endLocator~elDiskNumber
2144,2145,file~endLocator~elStartDiskNumber
2146,2147,file~endLocator~elEntriesOnDisk
2148,2149,file~endLocator~elEntriesInDirectory
2150,2153,file~endLocator~elDirectorySize
2154,2157,file~endLocator~elDirectoryOffset
2158,2159,file~endLocator~elCommentLength
2138,2159,file~endLocator,Optional
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

    # if (start > current_parent_end or end < current_parent_end) and end - start <= 8:
    #     # No overlap with previous parent
    #     filtered.append(line)
    #     current_parent_end = end
    # else:
    #     # This entry is inside an earlier parent, so skip
    #     continue

# `filtered` now has your required lines

print("Filtered Entries:")
print("\n".join(filtered))


# Filtered Entries:
# 0,3,file~record~frSignature
# 4,5,file~record~frVersion
# 4,4,file~record~frVersion~Version
# 5,5,file~record~frVersion~HostOS
# 6,7,file~record~frFlags
# 8,9,file~record~frCompression
# 10,11,file~record~frFileTime
# 12,13,file~record~frFileDate
# 14,17,file~record~frCrc
# 18,21,file~record~frCompressedSize
# 22,25,file~record~frUncompressedSize
# 26,27,file~record~frFileNameLength
# 28,29,file~record~frExtraFieldLength
# 30,37,file~record~frFileName
# 2048,2051,file~dirEntry~deSignature
# 2052,2053,file~dirEntry~deVersionMadeBy
# 2052,2052,file~dirEntry~deVersionMadeBy~Version
# 2053,2053,file~dirEntry~deVersionMadeBy~HostOS
# 2054,2055,file~dirEntry~deVersionToExtract
# 2054,2054,file~dirEntry~deVersionToExtract~Version
# 2055,2055,file~dirEntry~deVersionToExtract~HostOS
# 2056,2057,file~dirEntry~deFlags
# 2058,2059,file~dirEntry~deCompression
# 2060,2061,file~dirEntry~deFileTime
# 2062,2063,file~dirEntry~deFileDate
# 2064,2067,file~dirEntry~deCrc
# 2068,2071,file~dirEntry~deCompressedSize
# 2072,2075,file~dirEntry~deUncompressedSize
# 2076,2077,file~dirEntry~deFileNameLength
# 2078,2079,file~dirEntry~deExtraFieldLength
# 2080,2081,file~dirEntry~deFileCommentLength
# 2082,2083,file~dirEntry~deDiskNumberStart
# 2084,2085,file~dirEntry~deInternalAttributes
# 2086,2089,file~dirEntry~deExternalAttributes
# 2090,2093,file~dirEntry~deHeaderOffset
# 2094,2101,file~dirEntry~deFileName
# 2102,2103,file~dirEntry~deExtraField~efHeaderID
# 2104,2105,file~dirEntry~deExtraField~efDataSize
# 2110,2111,file~dirEntry~deExtraField~Tag
# 2112,2113,file~dirEntry~deExtraField~Size
# 2114,2121,file~dirEntry~deExtraField~Mtime
# 2114,2117,file~dirEntry~deExtraField~Mtime~dwLowDateTime
# 2118,2121,file~dirEntry~deExtraField~Mtime~dwHighDateTime
# 2122,2129,file~dirEntry~deExtraField~Atime
# 2122,2125,file~dirEntry~deExtraField~Atime~dwLowDateTime
# 2126,2129,file~dirEntry~deExtraField~Atime~dwHighDateTime
# 2130,2137,file~dirEntry~deExtraField~Ctime
# 2130,2133,file~dirEntry~deExtraField~Ctime~dwLowDateTime
# 2134,2137,file~dirEntry~deExtraField~Ctime~dwHighDateTime
# 2138,2141,file~endLocator~elSignature
# 2142,2143,file~endLocator~elDiskNumber
# 2144,2145,file~endLocator~elStartDiskNumber
# 2146,2147,file~endLocator~elEntriesOnDisk
# 2148,2149,file~endLocator~elEntriesInDirectory
# 2150,2153,file~endLocator~elDirectorySize
# 2154,2157,file~endLocator~elDirectoryOffset
# 2158,2159,file~endLocator~elCommentLength
# 102106,2109,file~dirEntry~deExtraField~Reserved