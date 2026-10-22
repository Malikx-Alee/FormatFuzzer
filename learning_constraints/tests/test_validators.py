import os
import shutil
import subprocess
import tempfile
import unittest
from unittest import mock

from helpers import load_manifest, repo_path, fixture_lines, tool_available, configure

from learning_constraints.config import Config
from learning_constraints import validators
from learning_constraints.validators import FileValidator


class CommandConstructionTests(unittest.TestCase):
    def setUp(self):
        self._strict = Config.VALIDATOR_STRICT

    def tearDown(self):
        Config.VALIDATOR_STRICT = self._strict

    def test_identify_has_resource_limits_and_strict_flag(self):
        Config.VALIDATOR_STRICT = False
        cmd = FileValidator.identify_command("x.png")
        self.assertEqual(cmd[0], "identify")
        self.assertIn("-limit", cmd)
        self.assertIn("disk", cmd)
        self.assertNotIn("-regard-warnings", cmd)
        self.assertEqual(cmd[-2:], ["-verbose", "x.png"])

        Config.VALIDATOR_STRICT = True
        self.assertIn("-regard-warnings", FileValidator.identify_command("x.png"))

    def test_ffmpeg_strict_flag(self):
        Config.VALIDATOR_STRICT = False
        self.assertNotIn("-xerror", FileValidator.ffmpeg_command("x.mp4"))
        Config.VALIDATOR_STRICT = True
        cmd = FileValidator.ffmpeg_command("x.mp4")
        self.assertIn("-xerror", cmd)
        self.assertIn("-nostdin", cmd)


class RobustnessTests(unittest.TestCase):
    def test_timeout_is_reported_as_invalid_not_exception(self):
        def boom(*args, **kwargs):
            raise subprocess.TimeoutExpired(cmd=args[0], timeout=kwargs.get("timeout"))
        with mock.patch.object(validators.subprocess, "run", side_effect=boom):
            self.assertFalse(FileValidator.validate_image_file("whatever.png"))
            self.assertFalse(FileValidator.validate_audio_video_file("whatever.mp4"))
            self.assertFalse(FileValidator.validate_pcap_file("whatever.pcap"))

    def test_subprocess_is_called_with_timeout_and_replacement_decoding(self):
        fake = subprocess.CompletedProcess(args=["ffmpeg"], returncode=0, stdout="", stderr="Input #0, avi, from 'x':")
        with mock.patch.object(validators.subprocess, "run", return_value=fake) as run:
            self.assertTrue(FileValidator.validate_audio_video_file("x.avi", "avi"))
            kwargs = run.call_args.kwargs
            self.assertEqual(kwargs.get("errors"), "replace")
            self.assertEqual(kwargs.get("timeout"), Config.VALIDATOR_TIMEOUT)

    def test_format_mismatch_is_invalid(self):
        fake = subprocess.CompletedProcess(args=["ffmpeg"], returncode=0, stdout="", stderr="Input #0, mov,mp4, from 'x':")
        with mock.patch.object(validators.subprocess, "run", return_value=fake):
            self.assertFalse(FileValidator.validate_audio_video_file("x.avi", "avi"))
            self.assertTrue(FileValidator.validate_audio_video_file("x.mp4"))


@unittest.skipUnless(tool_available("ffmpeg"), "ffmpeg not installed")
class FfmpegNonUtf8Test(unittest.TestCase):
    """A mutant whose bytes end up in ffmpeg's stderr must not be rejected by a decode error."""

    def test_corrupted_compressorname_is_still_valid(self):
        manifest = load_manifest()
        src = repo_path(manifest["mp4"]["primary"])
        line = next((l for l in fixture_lines("mp4") if "compressorname" in l), None)
        if line is None:
            self.skipTest("fixture has no compressorname field")
        start, end = int(line.split(",")[0]), int(line.split(",")[1])

        with tempfile.TemporaryDirectory() as tmp:
            probe = os.path.join(tmp, "probe.mp4")
            with open(src, "rb") as f:
                data = bytearray(f.read())
            data[start:end + 1] = b"\xd6" * (end - start + 1)
            with open(probe, "wb") as f:
                f.write(data)

            configure("mp4")
            Config.VALIDATOR_STRICT = False
            rc = subprocess.run(["ffmpeg", "-nostdin", "-i", probe, "-f", "null", "-"],
                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode
            self.assertEqual(FileValidator.is_valid_file(probe, "mp4"), rc == 0)
            self.assertEqual(rc, 0, "ffmpeg itself should accept this file")


if __name__ == "__main__":
    unittest.main()
