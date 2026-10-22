#!/usr/bin/env python3
"""Set differences of target-program line coverage between template strategies.

Two campaigns that report the same coverage percentage can cover different
lines; two that differ by 0.2 points can differ by a single error path. This
script compares the *sets* of covered lines, not the counts, so that

    hand - tiered      lines only the hand-tuned template reached
    tiered - hand      lines only the tiered template reached
    union / intersection across every variant

are first-class numbers, with each differing line attributed to its source
file and function (from the lcov FN: records).

Variants are discovered from the result directory names, so a new template
set (a new templates_llm/llm_<model>/) shows up here as soon as its campaign
finishes - nothing to register.

    python3 scripts/coverage_diff.py                      # every format, AFL results
    python3 scripts/coverage_diff.py gif png              # just these
    python3 scripts/coverage_diff.py gif --detail         # also write per-pair line lists
    python3 scripts/coverage_diff.py --mode gen           # generation-only results instead
    python3 scripts/coverage_diff.py --variants hand,opus5-tiered

Outputs a summary per format on stdout. With --detail, writes
coverage_diff/<fmt>/<A>_minus_<B>.txt (lines grouped by file and function)
and coverage_diff/<fmt>/unique_to_<A>.txt (lines no other variant reaches),
plus coverage_diff/<fmt>/summary.json.

Reads lcov .info files; works on this machine or on the server, wherever the
results are. Does not need the target sources - function names come from the
.info itself.
"""
import argparse
import bisect
import json
import os
import re
import sys
from collections import defaultdict
from itertools import combinations
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

REPO_ROOT = Path(__file__).resolve().parent.parent

# Where results live. The server pull lands under coverage_results_server/;
# local runs under coverage_results/. First existing one wins unless overridden.
RESULT_DIRS = [
    REPO_ROOT / "coverage_results_server" / "coverage_results",
    REPO_ROOT / "coverage_results",
]
OUT_DIR = REPO_ROOT / "coverage_diff"

Line = Tuple[str, int]          # (source file basename, line number)


class Coverage:
    """One lcov trace: which lines were hit, and where functions start."""

    def __init__(self, info: Path):
        self.info = info
        self.hit: Set[Line] = set()
        self.instrumented: Set[Line] = set()
        # file -> sorted list of (start_line, function_name), for attribution
        self._fn_starts: Dict[str, List[Tuple[int, str]]] = defaultdict(list)
        self._parse()

    def _parse(self) -> None:
        cur: Optional[str] = None
        with open(self.info) as fh:
            for raw in fh:
                ln = raw.strip()
                if ln.startswith("SF:"):
                    cur = os.path.basename(ln[3:])
                elif ln.startswith("FN:") and cur:
                    # FN:<start_line>,<name>   (newer lcov: FN:<start>,<end>,<name>)
                    parts = ln[3:].split(",")
                    self._fn_starts[cur].append((int(parts[0]), parts[-1]))
                elif ln.startswith("DA:") and cur:
                    num, cnt = ln[3:].split(",")[:2]
                    key = (cur, int(num))
                    self.instrumented.add(key)
                    if int(cnt) > 0:
                        self.hit.add(key)
                elif ln == "end_of_record":
                    cur = None
        for f in self._fn_starts:
            self._fn_starts[f].sort()

    def function_of(self, line: Line) -> str:
        """Name of the function containing this line: the function in the same
        file with the greatest start line not after it. Lines before the first
        function (globals, static tables) attribute to '<file scope>'."""
        f, n = line
        starts = self._fn_starts.get(f)
        if not starts:
            return "<file scope>"
        i = bisect.bisect_right([s for s, _ in starts], n) - 1
        return starts[i][1] if i >= 0 else "<file scope>"


# ---------------------------------------------------------------------------
# Discovery
# ---------------------------------------------------------------------------

_AFL = re.compile(r"^(?P<fmt>[a-z0-9]+)(?:-llm-(?P<model>[A-Za-z0-9.\-]+?))?-afl-ffmut$")
_GEN = re.compile(r"^(?P<fmt>[a-z0-9]+)(?:-llm-(?P<model>[A-Za-z0-9.\-]+))?$")


def discover(results_dir: Path, mode: str) -> Dict[str, Dict[str, Path]]:
    """{format: {variant_label: path_to_info}} for everything under results_dir.
    The hand-optimized template set is labelled 'hand'; LLM sets by model."""
    pat = _AFL if mode == "afl" else _GEN
    found: Dict[str, Dict[str, Path]] = defaultdict(dict)
    for d in sorted(results_dir.iterdir()):
        if not d.is_dir():
            continue
        m = pat.match(d.name)
        if not m:
            continue
        fmt, model = m.group("fmt"), m.group("model")
        if mode == "afl" and model is None and d.name != f"{fmt}-afl-ffmut":
            continue
        infos = list((d / "final").glob("*_target.info")) if mode == "afl" \
            else list(d.glob("*_target.info"))
        if not infos:
            continue
        found[fmt][model or "hand"] = infos[0]
    return found


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------

def group_lines(cov: Coverage, lines: Set[Line]) -> Dict[str, Dict[str, List[int]]]:
    """{file: {function: [line numbers]}} for a set of lines, using cov's FN map."""
    out: Dict[str, Dict[str, List[int]]] = defaultdict(lambda: defaultdict(list))
    for ln in sorted(lines):
        out[ln[0]][cov.function_of(ln)].append(ln[1])
    return out


def write_line_list(path: Path, title: str, cov: Coverage, lines: Set[Line]) -> None:
    g = group_lines(cov, lines)
    with open(path, "w") as fh:
        fh.write(f"{title}\n{'=' * len(title)}\n")
        fh.write(f"{len(lines)} lines in {len(g)} files\n\n")
        for f in sorted(g, key=lambda k: -sum(len(v) for v in g[k].values())):
            fh.write(f"{f}  ({sum(len(v) for v in g[f].values())} lines)\n")
            for fn in sorted(g[f], key=lambda k: -len(g[f][k])):
                nums = g[f][fn]
                fh.write(f"    {fn:<40} {len(nums):>4}   {compress(nums)}\n")
            fh.write("\n")


def compress(nums: List[int]) -> str:
    """[379,380,381,382,390] -> '379-382, 390'"""
    if not nums:
        return ""
    out, start, prev = [], nums[0], nums[0]
    for n in nums[1:]:
        if n == prev + 1:
            prev = n
            continue
        out.append(f"{start}-{prev}" if prev > start else f"{start}")
        start = prev = n
    out.append(f"{start}-{prev}" if prev > start else f"{start}")
    return ", ".join(out)


def pct(n: int, d: int) -> str:
    return f"{100.0 * n / d:.1f}%" if d else "-"


def report_format(fmt: str, infos: Dict[str, Path], variants: List[str],
                  detail: bool, out_dir: Path) -> dict:
    covs = {v: Coverage(infos[v]) for v in variants}
    sets = {v: covs[v].hit for v in variants}
    total = len(next(iter(covs.values())).instrumented)
    union = set().union(*sets.values())
    inter = set.intersection(*sets.values())

    w = max(len(v) for v in variants) + 2
    print(f"\n{'=' * 78}\n{fmt}   ({total} instrumented lines)\n{'=' * 78}")
    print(f"  {'variant':<{w}}{'covered':>9}{'pct':>8}{'unique':>9}   unique = reached by this variant and no other")
    unique: Dict[str, Set[Line]] = {}
    for v in variants:
        others = set().union(*(sets[o] for o in variants if o != v)) if len(variants) > 1 else set()
        unique[v] = sets[v] - others
        print(f"  {v:<{w}}{len(sets[v]):>9}{pct(len(sets[v]), total):>8}{len(unique[v]):>9}")
    print(f"  {'union':<{w}}{len(union):>9}{pct(len(union), total):>8}         any variant reached it")
    print(f"  {'intersection':<{w}}{len(inter):>9}{pct(len(inter), total):>8}         every variant reached it")
    print(f"  {'contested':<{w}}{len(union - inter):>9}{pct(len(union - inter), total):>8}         reached by some, missed by others")

    # pairwise matrix of |row - col|: lines ROW reaches that COL does not
    print(f"\n  |row - col|  (lines the row variant reaches that the column variant misses)")
    print(f"  {'':<{w}}" + "".join(f"{c:>{w}}" for c in variants))
    pairs = {}
    for a in variants:
        row = f"  {a:<{w}}"
        for b in variants:
            d = len(sets[a] - sets[b]) if a != b else 0
            pairs[(a, b)] = d
            row += f"{('·' if a == b else d):>{w}}"
        print(row)

    summary = {
        "format": fmt, "instrumented": total,
        "covered": {v: len(sets[v]) for v in variants},
        "unique": {v: len(unique[v]) for v in variants},
        "union": len(union), "intersection": len(inter),
        "pairwise_minus": {f"{a}-{b}": n for (a, b), n in pairs.items() if a != b},
    }

    if detail:
        d = out_dir / fmt
        d.mkdir(parents=True, exist_ok=True)
        for a, b in combinations(variants, 2):
            for x, y in ((a, b), (b, a)):
                diff = sets[x] - sets[y]
                if diff:
                    write_line_list(d / f"{x}_minus_{y}.txt",
                                    f"{fmt}: lines {x} reached that {y} did not", covs[x], diff)
        for v in variants:
            if unique[v]:
                write_line_list(d / f"unique_to_{v}.txt",
                                f"{fmt}: lines only {v} reached", covs[v], unique[v])
        never = next(iter(covs.values())).instrumented - union
        if never:
            write_line_list(d / "unreached_by_all.txt",
                            f"{fmt}: instrumented lines no variant reached", next(iter(covs.values())), never)
        (d / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
        print(f"\n  detail -> {d.relative_to(REPO_ROOT)}/")
    return summary


# ---------------------------------------------------------------------------

def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0],
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("formats", nargs="*", metavar="FORMAT", help="formats to compare (default: all found)")
    p.add_argument("--mode", choices=["afl", "gen"], default="afl",
                   help="afl: <fmt>[-llm-<model>]-afl-ffmut/final/ (default); gen: <fmt>[-llm-<model>]/")
    p.add_argument("--results-dir", type=Path, default=None,
                   help="where the result directories are (default: first of "
                        + ", ".join(str(d.relative_to(REPO_ROOT)) for d in RESULT_DIRS) + ")")
    p.add_argument("--variants", default=None,
                   help="comma-separated subset, e.g. hand,opus5,opus5-tiered (default: all found)")
    p.add_argument("--detail", action="store_true", help="write per-pair line lists under coverage_diff/")
    p.add_argument("--out-dir", type=Path, default=OUT_DIR)
    p.add_argument("--json", action="store_true", help="print one JSON summary at the end")
    args = p.parse_args(argv)

    results_dir = args.results_dir or next((d for d in RESULT_DIRS if d.is_dir()), None)
    if not results_dir or not results_dir.is_dir():
        sys.exit("no results directory found; pass --results-dir")

    found = discover(results_dir, args.mode)
    if not found:
        sys.exit(f"no {args.mode} results under {results_dir}")
    fmts = args.formats or sorted(found)
    want = args.variants.split(",") if args.variants else None

    print(f"results: {results_dir}   mode: {args.mode}")
    summaries = []
    for fmt in fmts:
        if fmt not in found:
            print(f"\n{fmt}: no results found", file=sys.stderr)
            continue
        avail = found[fmt]
        variants = [v for v in (want or sorted(avail, key=lambda v: (v != "hand", v))) if v in avail]
        missing = [v for v in (want or []) if v not in avail]
        if missing:
            print(f"\n{fmt}: skipping variants with no results: {', '.join(missing)}", file=sys.stderr)
        if len(variants) < 2:
            print(f"\n{fmt}: need at least two variants, have {variants}", file=sys.stderr)
            continue
        summaries.append(report_format(fmt, avail, variants, args.detail, args.out_dir))

    if args.json:
        print(json.dumps(summaries, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
