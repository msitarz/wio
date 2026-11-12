# SPDX-License-Identifier: Apache-2.0
"""Tests of how the discovery of Works is composed from its leaves."""

from pathlib import Path
from typing import TYPE_CHECKING
from unittest.mock import Mock

import pytest

from tests.unit.contracts.helpers import paths, where
from tests.unit.fakes import ROOT, MemoryFileSystem
from wio.contracts import discovery as module
from wio.models.config import Works
from wio.models.diagnostics import Diagnostic
from wio.models.frozen import freeze
from wio.models.works import Work

if TYPE_CHECKING:
    from collections.abc import Mapping

    from wio.io.ports import FileSystem

DIR = ROOT / ".agents" / "wio" / "works"
FILES = {DIR / name: "" for name in ("b.md", "a.md", "c.md", "d.md", "notes.md")}


def _work(name: str, work_id: str | None = None) -> Work:
    """Build a Work for a file of the Works directory.

    Args:
        name: The file's name.
        work_id: The Work's id; the name without its suffix when not given.

    Returns:
        A Work with that id.
    """
    return Work(
        id=work_id or name.removesuffix(".md"),
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


def _unmarked(name: str) -> module._Read:
    """Build what a leaf gives for a file that has no block.

    Args:
        name: The file's name.

    Returns:
        A read that is not marked, is not left out and has no Work or error.
    """
    return module._Read(  # noqa: SLF001
        path=Path(".agents/wio/works") / name,
        marked=False,
        left_out=False,
        work=None,
        problems=(),
    )


def test_the_result_is_assembled_from_the_leaves(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The reads, the collisions and the shared ids become one result."""
    # Given leaves that read `a` and `b` as Works, `c` as left out, `d` as a
    # file that a collision excludes and `notes` as a file with no block, and
    # that report a shared id
    reads = {
        n: _read(n, left_out=n == "c.md") for n in ("a.md", "b.md", "c.md", "d.md")
    }
    reads["notes.md"] = _unmarked("notes.md")
    reader = _reading(reads)
    monkeypatch.setattr(module, "_read_file", reader)
    collision = Diagnostic("error", "collision", "two files")
    excluded = frozenset({reads["c.md"].path, reads["d.md"].path})
    monkeypatch.setattr(
        module,
        "_find_collisions",
        Mock(return_value=module._Collisions(excluded, (collision,))),  # noqa: SLF001
    )
    shared = Diagnostic("error", "shared", "one id")
    judge = Mock(return_value=(shared,))
    monkeypatch.setattr(module, "_shared_ids", judge)

    # When the Works are discovered
    found = module.discover_works(ROOT, Works(), MemoryFileSystem(FILES))

    # Then only `a` and `b` are Works, in the order of their paths, `c` is left
    # out and `d` is excluded and not left out, the errors of the left-out file
    # and the collision are incomplete, the shared id is ambiguous, and the
    # diagnostics hold all of them and the problem of each file, the file with no
    # block is in no list, each file was read with the root and its own path, and
    # the shared ids were looked for among the Works that stay, in order
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
    names = ("a.md", "b.md", "c.md", "d.md", "notes.md")
    assert [c.args[:2] for c in reader.call_args_list] == [
        (ROOT, DIR / n) for n in names
    ]
    assert [w.id for w in judge.call_args.args[0]] == ["a", "b"]


def test_the_collisions_are_judged_by_the_hierarchy_mode_and_the_directory(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The leaf that applies the nesting rules gets the config's two settings."""
    # Given leaves that read a Work and a file that is left out, and a config
    # with nesting and its own Works directory
    reads = {"a.md": _read("a.md"), "b.md": _read("b.md", left_out=True)}
    monkeypatch.setattr(module, "_read_file", _reading(reads))
    judge = Mock(return_value=module._Collisions(frozenset(), ()))  # noqa: SLF001
    monkeypatch.setattr(module, "_find_collisions", judge)
    monkeypatch.setattr(module, "_shared_ids", Mock(return_value=()))
    settings = Works(dir="works", hierarchy="nesting")
    disk = MemoryFileSystem({ROOT / "works" / n: "" for n in reads})

    # When the Works are discovered
    module.discover_works(ROOT, settings, disk)

    # Then the leaf got every read, the one left out included, `nesting` and the
    # directory as written
    assert judge.call_args.args[1:] == ("nesting", "works")
    assert list(judge.call_args.args[0]) == list(reads.values())


@pytest.mark.parametrize(
    ("disk", "case"),
    [
        (MemoryFileSystem({ROOT / "x": ""}), "does not exist"),
        (MemoryFileSystem({ROOT / "elsewhere": ""}), "is not a directory"),
        (
            MemoryFileSystem(
                {ROOT / "elsewhere" / "a.md": ""}, links={ROOT / "elsewhere"}
            ),
            "must not be a symbolic link",
        ),
    ],
    ids=["missing", "a file", "a symbolic link"],
)
def test_a_directory_that_cannot_be_walked_reads_no_file(
    monkeypatch: pytest.MonkeyPatch, disk: MemoryFileSystem, case: str
) -> None:
    """The refusal comes before any file is read, and is incomplete."""
    # Given a leaf that fails the test if it reads, and a configured Works
    # directory that is missing, is a file or is a symbolic link, in a
    # repository that exists
    leaf = Mock()
    monkeypatch.setattr(module, "_read_file", leaf)
    settings = Works(dir="elsewhere")

    # When the Works are discovered
    found = module.discover_works(ROOT, settings, disk)

    # Then no file was read, and the one error is at the directory as written,
    # begins `The Works directory`, says what is wrong, and is incomplete and
    # not ambiguous
    leaf.assert_not_called()
    assert found.works == ()
    assert found.diagnostics == found.incomplete
    assert [d.where for d in found.diagnostics] == ["elsewhere"]
    message = found.diagnostics[0].message
    assert message.startswith("The Works directory")
    assert message.endswith(case)
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


def _read_at(
    relative: str, *places: str, left_out: bool = False, work_id: str | None = None
) -> module._Read:
    """Build what a leaf gives for a file at a path below the Works directory.

    Args:
        relative: The path below the Works directory.
        *places: The places of the file's own errors, in the order given.
        left_out: Whether the file is left out.
        work_id: The id of the Work, which a test sets apart from the path.

    Returns:
        The read, with a Work unless the file is left out.
    """
    path = Path(".agents/wio/works") / relative
    return module._Read(  # noqa: SLF001
        path=path,
        marked=True,
        left_out=left_out,
        work=None if left_out else _work(relative, work_id),
        problems=tuple(
            Diagnostic("error", f"{path.as_posix()}{p}", "m") for p in places
        ),
    )


def _tree_out_of_order(monkeypatch: pytest.MonkeyPatch) -> MemoryFileSystem:
    """Fake the leaves for a tree whose walk is not in the order of its paths.

    Three groups of four files share one shape: a directory is walked before the
    file that sorts first as a string, and `x-y/` sorts before `x/` as a string,
    so the order of the paths is neither that of the walk, nor of the names, nor
    of the parent directories, nor of the ids. One group are Works, one are left
    out and one are excluded by a collision. One file has errors out of order,
    and two shared ids come out of order.

    Args:
        monkeypatch: The fixture that replaces the leaves.

    Returns:
        The disk that lists the files.
    """
    works = ("a/0.md", "a/w.md", "a-b/x.md", "a.md")
    left_out = ("c/2.md", "c/v.md", "c-d/7.md", "c.md")
    excluded = ("e/3.md", "e/u.md", "e-f/6.md", "e.md")
    reads = {
        r.path.name: r
        for r in (
            _read_at("a/0.md", ":12", ":4", work_id="b"),
            _read_at("a/w.md", work_id="a"),
            _read_at("a-b/x.md", work_id="d"),
            _read_at("a.md", work_id="c"),
            *(_read_at(name, "", left_out=True) for name in left_out),
            *(_read_at(name) for name in excluded),
        )
    }
    monkeypatch.setattr(module, "_read_file", _reading(reads))
    shut = frozenset(Path(".agents/wio/works") / name for name in excluded)
    place = ", ".join(sorted(p.as_posix() for p in shut))
    collisions = module._Collisions(shut, (Diagnostic("error", place, "m"),))  # noqa: SLF001
    monkeypatch.setattr(module, "_find_collisions", Mock(return_value=collisions))
    shared = (Diagnostic("error", "s2", "m"), Diagnostic("error", "s1", "m"))
    monkeypatch.setattr(module, "_shared_ids", Mock(return_value=shared))
    return MemoryFileSystem({DIR / n: "" for n in (*works, *left_out, *excluded)})


def _in_order(
    diagnostics: tuple[Diagnostic, ...], subset: tuple[Diagnostic, ...]
) -> bool:
    """Tell whether a subset appears in a list in the same order.

    Args:
        diagnostics: The whole list.
        subset: Some of its diagnostics.

    Returns:
        Whether the members of the list that are in the subset are the subset.
    """
    return [d for d in diagnostics if d in subset] == list(subset)


def test_every_list_is_in_the_order_of_its_paths_and_places(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The walk, the ids and the parent directories are not the order of the paths."""
    # Given a tree whose walk, names, ids and parent directories are not in the
    # order of its paths, with errors and shared ids out of order
    disk = _tree_out_of_order(monkeypatch)
    base = ".agents/wio/works/"
    ordered = ("a-b/x.md", "a.md", "a/0.md", "a/w.md")
    left_out = [f"{base}{n}" for n in ("c-d/7.md", "c.md", "c/2.md", "c/v.md")]
    excluded = [f"{base}{n}" for n in ("e-f/6.md", "e.md", "e/3.md", "e/u.md")]
    collision = ", ".join(excluded)

    # When the Works are discovered
    found = module.discover_works(ROOT, Works(), disk)

    # Then each list is exactly in order: the Works and the files by the string
    # of their paths, and the diagnostics by file, then line as a number, then
    # the places that are not a file as text, with `incomplete` and `ambiguous`
    # in the same order inside `diagnostics`
    assert paths(w.path for w in found.works) == [f"{base}{n}" for n in ordered]
    assert paths(found.left_out) == left_out
    assert paths(found.excluded) == excluded
    assert where(found.diagnostics) == [
        f"{base}a/0.md:4",
        f"{base}a/0.md:12",
        *left_out,
        collision,
        "s1",
        "s2",
    ]
    assert where(found.incomplete) == [*left_out, collision]
    assert where(found.ambiguous) == ["s1", "s2"]
    assert _in_order(found.diagnostics, found.incomplete)
    assert _in_order(found.diagnostics, found.ambiguous)
