# Bug: `identify -verbose` false-negatives valid PNGs (and potentially bmp/gif/jpg)

## Summary

The PNG validator reported **0/10000 (0.00%) valid** for both `png` and
`png-orig` even after the template was rebuilt. This looked like a genuine
template bug but wasn't: the validator command itself was rejecting files
that real-world PNG decoders (Apple's ImageIO — what Preview.app and
QuickLook use — and plain `identify` without `-verbose`) open without any
error. The `-verbose` flag added to the `identify`-based validators (see
[identify_validator_resource_exhaustion.md](identify_validator_resource_exhaustion.md))
turned out to force a stricter, full-pixel-decode code path in this
ImageMagick build that fails on PNGs whose zlib/CRC framing isn't
byte-perfect, even when the image content itself is completely decodable.

## Symptom

- User manually generated PNG files with `png-fuzzer` and opened them in a
  previewer — they displayed fine.
- Automated validation (`identify -limit ... -verbose - <file | grep -q
  Elapsed`) reported them all invalid.

## Root cause

Isolated by comparing four ways of checking the same generated files:

| Check | Result on 10-file sample |
|---|---|
| Apple ImageIO (`sips -s format jpeg file.png --out ...`, same decoder as Preview/QuickLook) | 7/10 pass |
| `identify file.png` (bare, no `-verbose`, no stdin) | 7/10 pass — same 7 |
| `identify -verbose file.png` (bare, filename, `-verbose` added) | 0/10 pass |
| `identify -verbose - <file.png` (stdin, matches old validator) | 0/10 pass |

`-verbose` alone (independent of stdin vs filename, independent of the
`-limit` flags) is what flips every result from pass to fail. The failures
are all libpng-level errors surfaced only during a full decode, e.g.:

```
identify: IDAT: incorrect header check `...' @ error/png.c/MagickPNGError/1305.
identify: IDAT: invalid window size (libpng) `...' @ error/png.c/MagickPNGError/1305.
```

Plain `identify` (no `-verbose`) only needs to read IHDR to report
dimensions/type, so it doesn't hit this path. Re-validated at scale (500
`png-fuzzer` outputs): `-verbose` → 0/500 pass; bare `identify` (same
`-limit` caps, no `-verbose`) → 391/500 (78.2%) pass, matching a plausible
real fuzzer yield.

Note: Python's Pillow (`Image.load()`) was *also* tried as an independent
check and failed on all 10 samples, including ones ImageIO/bare-identify
pass — Pillow's PNG decoder is evidently even stricter than
`identify -verbose` here, so it was **not** adopted as the validator.

This is PNG/zlib-specific (IDAT chunk CRC/deflate-header strictness), which
is consistent with `bmp`/`jpg` — which don't use zlib-compressed chunked
data the same way — showing plausible (`bmp`/`jpg`: 100%) rather than
zero results even under the old `-verbose` command. `gif` (uses LZW, not
zlib) sat at ~49%, which was suspected of being partially undercounted by
the same mechanism and was re-verified alongside png/bmp/jpg when fixing
this.

## Fix

Applied in [fuzz_manager.py](../scripts/fuzz_manager.py): dropped `-verbose` (and
the now-unnecessary `| grep -q Elapsed`, which only matched text that
`-verbose` printed) from the `bmp`, `gif`, `jpg`, `png` validators. The
`-limit memory/map/disk/time` flags from the resource-exhaustion fix are
kept — they're independent of `-verbose` and still needed. Validity is now
just `identify`'s own exit code:

```
identify -limit memory 512MiB -limit map 512MiB -limit disk 2GiB -limit time 10 - <{file} >/dev/null 2>&1
```

## Verification

- 10-file and 500-file samples cross-checked against Apple ImageIO
  (`sips -s format jpeg ...`) with 100% agreement using the bare-exit-code
  method.
- `bmp`/`jpg` were already at 100% under the old strict method, so they
  can't be undercounted by dropping `-verbose` (a stricter check can only
  produce a subset of what a looser check passes); re-run anyway for
  completeness.

## Notes for future work

- If precise root-causing of the specific libpng CRC/window-size failures
  is ever needed, this ImageMagick build's PNG delegate is worth comparing
  against a vanilla libpng build — the strictness may be a
  ImageMagick-bundled-libpng vs. system-libpng version difference rather
  than something meaningful about the fuzzed files.
- Any future validator command should be sanity-checked against a
  known-good file *and* against an independent decoder (not just "does the
  tool exit 0"), since a validator that's simply wrong reads identically to
  a template that's genuinely broken — this was the second time in this
  project a "0% valid" result turned out to be a tooling bug (see also the
  `mpg321` SIGABRT issue for mp3, documented in the conversation but not
  yet split into its own file here).
