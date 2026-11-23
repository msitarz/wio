# SPDX-License-Identifier: Apache-2.0
"""Tests of the joined report of `wio rules check`."""

from pathlib import Path

from tests.unit.fakes import ROOT, MemoryFileSystem
from wio.models.config import Config, Root, Stage
from wio.models.diagnostics import sort_diagnostics
from wio.models.frozen import freeze
from wio.rules import check_errors, check_rules, check_warnings, discover

_DIR = ROOT / ".agents" / "wio" / "rules" / "demo"


def _disk() -> MemoryFileSystem:
    """Build a ruleset with a warning, an error of a file and an open block.

    Returns:
        A file system of one ruleset `demo`.
    """
    keyed = '<!-- wio\ncode = "ARC001"\nname = "keep"\nowner = "me"\n-->\n\nBody.\n'
    opened = '<!-- wio\ncode = "ARC002"\n'
    return MemoryFileSystem(
        {
            _DIR / "ruleset.toml": '[families]\nARC = "Topic"\n',
            _DIR / "ARC001-keep.md": keyed,
            _DIR / "ARC002-open.md": opened,
        }
    )


def _config() -> Config:
    """Build a config whose only stage includes a family that does not exist.

    Returns:
        The config.
    """
    stage = Stage("g", None, None, ("demo.XYZ",), ())
    return Config(
        roots=freeze({"code": Root(("src",), ())}), stages=freeze({"s": stage})
    )


def test_the_report_is_the_two_lists_in_one_order() -> None:
    """The faults of the discovery come once, through the list of their severity."""
    # Given rules with a warning and an error, and a reference that fails
    disk, config = _disk(), _config()

    # When the rules are checked
    found = check_rules(ROOT, config, disk)

    # Then it holds each fault once, errors and warnings, in the shared order
    discovery = discover(ROOT, _disk())
    both = (*check_errors(config, discovery), *check_warnings(config, discovery))
    assert found == sort_diagnostics(both)
    assert len(found) == len(set(found)) == 3
    assert sorted(d.severity for d in found) == ["error", "error", "warning"]


def test_the_report_reads_once_and_writes_nothing() -> None:
    """One discovery reads the files, and nothing is appended or written."""
    # Given the same rules, and the reads that one discovery makes
    disk, alone = _disk(), _disk()
    discover(ROOT, alone)

    # When the rules are checked
    check_rules(ROOT, _config(), disk)

    # Then the reads are those of one discovery, and nothing was written
    assert disk.calls == alone.calls
    assert disk.appends == []
    assert set(disk.files) == {Path(p) for p in alone.files}
