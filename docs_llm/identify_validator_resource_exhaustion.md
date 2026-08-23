# Bug: `identify` (ImageMagick) resource exhaustion on fuzzed PNGs

## Summary

The PNG validator used by [fuzz_manager.py](../scripts/fuzz_manager.py) /
[validate_all_templates.py](../validate_all_templates.py) — ImageMagick's
`identify` — can go into a pathological allocation/disk-spill state when fed
certain fuzzer-generated PNGs (from both `png` and `png-orig` templates).
Instead of failing fast, it allocates and writes a multi-gigabyte pixel-cache
temp file to `$TMPDIR`. Combined with a validator timeout that didn't kill
the whole process tree, this crashed the host machine three times in one
session (system ran out of disk / memory and force-rebooted) while running
10k-file validation batches.

## Symptom

- `df` free space dropped from ~140GB to single-digit GB within ~15 minutes
  of starting png/png-orig validation, with no corresponding growth in this
  project's own `output/` directory (which stayed ~1.4GB throughout).
- Found via `du -sh /private/var/folders/*/T/*` (`$TMPDIR`): three leaked
  files named `magick-<random>` totaling ~124GB, one alone at 68GB.
- `ps aux` showed a live orphaned `identify -verbose -` process still
  actively writing to one of those temp files, well after the Python driver
  process that spawned it had already died in an earlier crash — i.e. the
  validator outlived its own timeout and kept consuming disk unattended.

## Root cause

Two independent problems stacked:

1. **ImageMagick itself.** Certain malformed PNGs (plausibly ones with a
   corrupted/huge IHDR width or height field — not confirmed byte-for-byte
   since the triggering files were consumed and cleaned up before this was
   diagnosed) make `identify`'s PNG decoder try to materialize a huge pixel
   cache. ImageMagick backs large pixel caches with a disk-mapped temp file
   rather than erroring out immediately, so the process just keeps writing
   until it's killed or the disk fills.
2. **Timeout didn't kill the process tree.** The old `run_validation()` in
   fuzz_manager.py called:
   ```python
   subprocess.run(cmd, shell=True, stdout=DEVNULL, stderr=DEVNULL, timeout=30)
   ```
   `cmd` is `identify ... | grep -q Elapsed`, run via `shell=True`. On
   `TimeoutExpired`, `subprocess.run` only kills the immediate child (the
   shell) — not the shell's children (`identify`, `grep`). Once the shell
   died, `identify` was reparented and kept running/growing completely
   outside our control, even surviving a full crash-and-reboot of the
   parent Python process.

This is arguably a genuine fuzzing finding in its own right: the png
templates can produce inputs that trigger resource-exhaustion behavior in a
real-world PNG consumer (ImageMagick), separate from the normal
valid/invalid classification.

## Fix

Applied in [fuzz_manager.py](../scripts/fuzz_manager.py):

1. `run_validation()` now launches the validator with
   `subprocess.Popen(..., start_new_session=True)` and, on timeout, kills
   the entire process group with `os.killpg(proc.pid, signal.SIGKILL)`
   instead of relying on `subprocess.run`'s single-process kill.
2. The `identify`-based validators (`bmp`, `gif`, `jpg`, `png` in
   `VALIDATORS`) now pass explicit resource caps:
   ```
   identify -limit memory 512MiB -limit map 512MiB -limit disk 2GiB -limit time 10 -verbose - ...
   ```
   so a pathological input makes ImageMagick self-abort (`-limit` triggers
   its own cache-resource-exhausted error) well before it can leak
   gigabytes, and `-limit time 10` bounds wall-clock time independent of
   our own 30s outer timeout.

## Verification

Regenerated 300 fresh `png-orig` fuzzer outputs and validated them all with
the capped `identify` command while watching `df` and `$TMPDIR`: no
`magick-*` temp files appeared and free disk didn't move. The subsequent
full 10k-file `png-orig` validation run completed without incident.

## Notes for future work

- If this needs to be root-caused precisely, capture a copy of the
  triggering fuzzer output *before* validating it (e.g. `cp` each generated
  file aside prior to running `identify`) so a reproducer survives even if
  the validator run crashes.
- The same `identify`-based validator is shared by `bmp`, `gif`, and `jpg`
  templates — worth keeping an eye on those too, though only `png`/`png-orig`
  have triggered this so far.
- Applies to any other validator invoked via `shell=True` with a pipeline
  (`cmd | grep ...`): the process-group timeout fix in `run_validation()`
  now covers all of them, not just `identify`.
