#!/usr/bin/env python3
"""Generate a partial report from available results."""

import json
from pathlib import Path

def main():
    results = []
    output_dir = Path(__file__).resolve().parent.parent / "output"

    for report_path in sorted(output_dir.glob("*/*/report.json")):
        try:
            with open(report_path) as f:
                report = json.load(f)

            filetype = report_path.parent.parent.name
            gen = report['generation']
            val = report['validation']

            # Determine type (Original vs Optimized)
            is_orig = '-orig' in filetype
            template_type = "Optimized" if is_orig else "Original"

            results.append({
                'template': filetype,
                'type': template_type,
                'count': gen['target_count'],
                'generated': gen['generated_count'],
                'valid': val['valid_count'],
                'invalid': val['invalid_count'],
                'gen_speed': gen['generation_speed_files_per_second'],
                'gen_time': gen['generation_time_seconds'],
                'val_time': val['validation_time_seconds'],
                'total_time': report['totals']['total_time_seconds'],
                'valid_rate': val['valid_rate_percent'],
            })
        except:
            pass

    if not results:
        print("No results yet")
        return

    # Generate markdown
    md = "# Benchmark Report (In Progress)\n\n"
    md += f"Results from {len(results)} templates so far...\n\n"
    md += "| Template | Type | Generated | Valid | Invalid | Speed (f/s) | Valid % |\n"
    md += "|----------|------|-----------|-------|---------|-------------|----------|\n"

    for r in sorted(results, key=lambda x: x['template']):
        md += f"| {r['template']} | {r['type']} | {r['generated']} | {r['valid']} | {r['invalid']} | {r['gen_speed']:.0f} | {r['valid_rate']:.1f}% |\n"

    print(md)

if __name__ == "__main__":
    main()
