#!/usr/bin/env python3
"""Add required_value_hex and required_value_ascii to every fixed_value entry
in the results_ai/*/llm_reterived_constraints_*_opus4.7.json files."""

import json
import os
from collections import OrderedDict

FORMATS = ["gif", "bmp", "avi", "midi", "jpg", "png", "mp3", "mp4", "pcap", "wav", "zip"]
ROOT = os.path.join(os.path.dirname(__file__), "..", "results_ai")

# On-disk byte order used by each format's binary template. This determines
# how multi-byte integer required_values are rendered in ASCII so that the
# byte sequence matches what actually appears in the file.
ENDIAN = {
    "gif":  "little",
    "bmp":  "little",
    "avi":  "little",
    "wav":  "little",
    "zip":  "little",
    "pcap": "little",
    "midi": "big",
    "jpg":  "big",
    "png":  "big",
    "mp3":  "big",
    "mp4":  "big",
}


def render_bytes(b: bytes) -> str:
    """Render bytes as a printable string with \\xNN escapes for non-printable bytes."""
    out = []
    for c in b:
        if 32 <= c < 127 and c != ord("\\"):
            out.append(chr(c))
        else:
            out.append("\\x{:02X}".format(c))
    return "".join(out)


def fully_printable(b: bytes) -> bool:
    return len(b) > 0 and all(32 <= c < 127 for c in b)


def derive(value, endian):
    """Return (hex_str, ascii_str) for a required_value rendered with the
    given on-disk byte order."""
    if isinstance(value, str):
        raw = value.encode("utf-8", errors="replace")
        hex_str = "0x" + raw.hex().upper()
        return hex_str, value

    if isinstance(value, bool):
        return ("0x01", "True") if value else ("0x00", "False")

    if isinstance(value, int):
        if value < 0:
            return "-0x" + format(-value, "X"), ""
        # Pad hex literal to byte-aligned width.
        nibbles = max(2, ((value.bit_length() + 7) // 8) * 2)
        hex_str = "0x" + format(value, "0{}X".format(nibbles))
        if value == 0:
            return hex_str, "\\x00"
        byte_len = max(1, (value.bit_length() + 7) // 8)
        # Render the integer as the byte sequence the parser actually sees on
        # disk, then escape any non-printable bytes.
        on_disk = value.to_bytes(byte_len, endian)
        return hex_str, render_bytes(on_disk)

    return None, None


def update_entry(entry, endian):
    if not isinstance(entry, dict):
        return entry
    if "required_value" not in entry:
        return entry
    hex_str, ascii_str = derive(entry["required_value"], endian)
    if hex_str is None:
        return entry
    new_entry = OrderedDict()
    for k, v in entry.items():
        if k in ("required_value_hex", "required_value_ascii"):
            continue
        new_entry[k] = v
        if k == "required_value":
            new_entry["required_value_hex"] = hex_str
            new_entry["required_value_ascii"] = ascii_str
    return new_entry


def process_file(path, endian):
    with open(path, "r") as f:
        data = json.load(f, object_pairs_hook=OrderedDict)
    out = OrderedDict()
    for key, entry in data.items():
        out[key] = update_entry(entry, endian)
    with open(path, "w") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)
        f.write("\n")
    print(f"updated {path} ({endian}-endian)")


def main():
    for fmt in FORMATS:
        path = os.path.join(ROOT, fmt, f"llm_reterived_constraints_{fmt}_opus4.7.json")
        if not os.path.exists(path):
            print(f"missing {path}")
            continue
        process_file(path, ENDIAN[fmt])


if __name__ == "__main__":
    main()
