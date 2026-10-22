"""Shared helpers for the learning_constraints test-suite.

Run the suite from the repository root with:

    python3 -m unittest discover -s learning_constraints/tests -v

Tests that need a fuzzer binary look for ``build/<fmt>-fuzzer`` and skip when it is missing.
"""
import json
import os
import sys

TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(os.path.dirname(TESTS_DIR))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

FIXTURES_DIR = os.path.join(TESTS_DIR, "fixtures")
BUILD_DIR = os.path.join(REPO_ROOT, "build")

from learning_constraints.config import Config  # noqa: E402


def load_manifest():
    with open(os.path.join(FIXTURES_DIR, "manifest.json")) as f:
        return json.load(f)


def fixture_lines(fmt):
    with open(os.path.join(FIXTURES_DIR, f"{fmt}.parse.txt")) as f:
        return f.read().splitlines()


def repo_path(relative):
    return os.path.join(REPO_ROOT, relative)


def fuzzer_available(fmt):
    return os.path.exists(os.path.join(BUILD_DIR, f"{fmt}-fuzzer"))


def tool_available(name):
    from shutil import which
    return which(name) is not None


def configure(fmt):
    """Point Config at the format and at the built fuzzers."""
    Config.set_file_type(fmt)
    Config.FUZZER_DIR = BUILD_DIR
    Config.FFCOMPILE_PATH = repo_path("ffcompile")
    Config.TEMPLATES_DIR = repo_path("templates")


def leaf_map(nested):
    """{cleaned_path: set(values)} for a nested value dictionary."""
    from learning_constraints.utils import iter_leaf_paths
    return {path: set(values) for path, values in iter_leaf_paths(nested)}
