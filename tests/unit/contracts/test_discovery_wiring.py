# SPDX-License-Identifier: Apache-2.0
"""Tests of how the discovery of Works is composed from its leaves."""

from pathlib import Path
from typing import TYPE_CHECKING
from unittest.mock import Mock

from tests.unit.fakes import ROOT, MemoryFileSystem
from wio.contracts import discovery as module
from wio.models.config import Works
from wio.models.diagnostics import Diagnostic
from wio.models.frozen import freeze
from wio.models.works import Work

if TYPE_CHECKING:
    from collections.abc import Mapping

    import pytest

    from wio.io.ports import FileSystem

DIR = ROOT / ".agents" / "wio" / "works"
FILES = {DIR / name: "" for name in ("b.md", "a.md", "c.md", "d.md")}


def _work(name: str) -> Work:
    """Build a Work for a file of the Works directory.

    Args:
        name: The file's name.

    Returns:
        A Work whose id is the name without its suffix.
    """
    return Work(
        id=name.removesuffix(".md"),
        title=None,
        path=Path(".agents/wio/works") / name,
        template=None,
        roots=(),
        depends_on=(),
        actions=freeze({}),
    )


def _read(name: str, *, left_out: bool = False) -> module._Read:
    """Build what a leaf gives for one file.

    Args:
        name: The file's name.
        left_out: Whether the file is left out, with one error of its own.

    Returns:
        The read: a Work with a problem when it stays, or an error and no Work.
    """
    path = Path(".agents/wio/works") / name
    problem = Diagnostic("error", path.as_posix(), f"problem of {name}")
    return module._Read(  # noqa: SLF001
        path=path,
        marked=True,
        left_out=left_out,
        work=None if left_out else _work(name),
        problems=(problem,),
    )


def _reading(reads: Mapping[str, module._Read]) -> Mock:
    """Make a leaf that reads a file by giving the read prepared for its name.

    Args:
        reads: The reads, by the name of the file.

    Returns:
        A mock that takes the root, the path and the port, as the leaf does.
    """

    def read(_root: Path, path: Path, _files: FileSystem) -> module._Read:
        """Give the read of a file.

        Args:
            _root: The repository root, which is not read.
            path: The file.
            _files: The port, which is not used.

        Returns:
            The read prepared for the file's name.
        """
        return reads[path.name]

    return Mock(side_effect=read)


def test_the_result_is_assembled_from_the_leaves(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The reads, the collisions and the shared ids become one result."""
    # Given leaves that read `a` and `b` as Works, `c` as left out and `d` as a
    # file that a collision excludes, and that report a shared id
    reads = {
        n: _read(n, left_out=n == "c.md") for n in ("a.md", "b.md", "c.md", "d.md")
    }
    monkeypatch.setattr(module, "_read_file", _reading(reads))
    collision = Diagnostic("error", "collision", "two files")
    excluded = frozenset({reads["c.md"].path, reads["d.md"].path})
    monkeypatch.setattr(
        module,
        "_find_collisions",
        Mock(return_value=module._Collisions(excluded, (collision,))),  # noqa: SLF001
    )
    shared = Diagnostic("error", "shared", "one id")
    monkeypatch.setattr(module, "_shared_ids", Mock(return_value=(shared,)))

    # When the Works are discovered
    found = module.discover_works(ROOT, Works(), MemoryFileSystem(FILES))

    # Then only `a` and `b` are Works, in the order of their paths, `c` is left
    # out and `d` is excluded and not left out, the errors of the left-out file
    # and the collision are incomplete, the shared id is ambiguous, and the
    # diagnostics hold all of them and the problem of each file
    assert [work.id for work in found.works] == ["a", "b"]
    assert found.left_out == (reads["c.md"].path,)
    assert found.excluded == (reads["d.md"].path,)
    assert {d.message for d in found.incomplete} == {"problem of c.md", "two files"}
    assert found.ambiguous == (shared,)
    assert sorted(d.message for d in found.diagnostics) == [
        "one id",
        "problem of a.md",
        "problem of b.md",
        "problem of c.md",
        "problem of d.md",
        "two files",
    ]


def test_the_collisions_are_judged_by_the_hierarchy_mode_and_the_directory(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The leaf that applies the nesting rules gets the config's two settings."""
    # Given leaves that find nothing wrong and a config with nesting and its
    # own Works directory
    monkeypatch.setattr(module, "_read_file", _reading({"a.md": _read("a.md")}))
    judge = Mock(return_value=module._Collisions(frozenset(), ()))  # noqa: SLF001
    monkeypatch.setattr(module, "_find_collisions", judge)
    monkeypatch.setattr(module, "_shared_ids", Mock(return_value=()))
    settings = Works(dir="works", hierarchy="nesting")
    disk = MemoryFileSystem({ROOT / "works" / "a.md": ""})

    # When the Works are discovered
    module.discover_works(ROOT, settings, disk)

    # Then the leaf got the reads, `nesting` and the directory as written
    assert judge.call_args.args[1:] == ("nesting", "works")
    assert len(judge.call_args.args[0]) == 1


def test_a_directory_that_cannot_be_walked_reads_no_file(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The refusal comes before any file is read, and is incomplete."""
    # Given a leaf that fails the test if it reads, and a Works directory that
    # is not there
    leaf = Mock()
    monkeypatch.setattr(module, "_read_file", leaf)
    settings = Works(dir="elsewhere")

    # When the Works are discovered
    found = module.discover_works(ROOT, settings, MemoryFileSystem())

    # Then no file was read, and the one error is incomplete and not ambiguous
    leaf.assert_not_called()
    assert found.works == ()
    assert found.diagnostics == found.incomplete
    assert [d.where for d in found.diagnostics] == ["elsewhere"]
    assert found.ambiguous == ()


def test_a_missing_default_directory_holds_no_work_and_reads_no_file(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The default Works directory may be missing without a diagnostic."""
    # Given a leaf that fails the test if it reads, and no files
    leaf = Mock()
    monkeypatch.setattr(module, "_read_file", leaf)

    # When the Works are discovered with the default settings
    found = module.discover_works(ROOT, Works(), MemoryFileSystem())

    # Then nothing was read and the result is empty
    leaf.assert_not_called()
    assert found == module.WorkDiscovery((), (), (), (), (), ())
