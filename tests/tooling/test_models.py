# SPDX-License-Identifier: Apache-2.0
"""Tests that the sample config and the sources agree with `wio.models`."""

import tomllib
from pathlib import Path

from wio.models.config import Config

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"


def test_the_sample_config_holds_the_default_results_vocabulary() -> None:
    """`[gates] results` of the repository's config is the default of `Config`."""
    # Given the sample config of the repository
    text = (ROOT / ".agents" / "wio" / "config.toml").read_text(encoding="utf-8")

    # When its `[gates]` table is read
    table = tomllib.loads(text)["gates"]

    # Then it holds the same vocabulary as the default Config
    assert tuple(table["results"]) == Config().gates.results


def test_one_helper_holds_the_only_pyrefly_suppression() -> None:
    """One suppression in `src` names `bad-argument-count`, in the `freeze` helper."""
    # Given the pyrefly suppressions of the source tree
    marker = "pyrefly: " + "ignore"
    hits = [
        (path, line)
        for path in SRC.rglob("*.py")
        for line in path.read_text(encoding="utf-8").splitlines()
        if marker in line
    ]

    # When the files that hold them are listed
    files = sorted({path.name for path, _ in hits})

    # Then there is one, in `frozen.py`, naming bad-argument-count and the issue
    assert len(hits) == 1
    assert files == ["frozen.py"]
    path, line = hits[0]
    assert "bad-argument-count" in line
    assert "known-issues.md" in path.read_text(encoding="utf-8")
