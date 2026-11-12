# SPDX-License-Identifier: Apache-2.0
"""Tests of the discovery of Works on a real disk."""

from pathlib import Path

from wio.contracts.discovery import discover_works, explain_not_a_work
from wio.io.adapters import LocalFileSystem
from wio.models.config import Works

COMMENT = '<!-- wio\nid = "{id}"\n-->\n\n# {id}\n'
FRONT = '+++\nwio = 1\nid = "{id}"\n+++\n\n# {id}\n'


def _write(path: Path, text: str) -> Path:
    """Write a file, making its directories.

    Args:
        path: The file.
        text: Its text.

    Returns:
        The file.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def _snapshot(root: Path) -> dict[str, bytes]:
    """Read every file below a directory, following no link.

    Args:
        root: The directory.

    Returns:
        The bytes of each regular file, by its path below the directory.
    """
    return {
        p.relative_to(root).as_posix(): p.read_bytes()
        for p in sorted(root.rglob("*"))
        if p.is_file() and not p.is_symlink()
    }


def test_a_real_symbolic_link_is_not_followed_and_a_real_tree_is_walked(
    tmp_path: Path,
) -> None:
    """AC-1: a link to a marked file is no Work, and no file is written."""
    # Given a repository on disk with Works in both block forms, a symbolic link
    # to a marked file and a hidden directory with a marked file
    works = tmp_path / "works"
    _write(works / "a" / "README.md", COMMENT.format(id="k3m9xq"))
    _write(works / "b" / "spec.md", FRONT.format(id="a7b2c4"))
    _write(works / ".hidden" / "README.md", COMMENT.format(id="hidden"))
    target = _write(tmp_path / "elsewhere.md", COMMENT.format(id="linked"))
    (works / "c").mkdir()
    (works / "c" / "link.md").symlink_to(target)
    before = _snapshot(tmp_path)

    # When the Works are discovered through the real file system
    found = discover_works(
        tmp_path, Works(dir="works", hierarchy="nesting"), LocalFileSystem()
    )

    # Then the Works are those of the files that are not links or hidden, and
    # the files on disk are as they were
    assert [w.id for w in found.works] == ["k3m9xq", "a7b2c4"]
    assert found.diagnostics == ()
    assert _snapshot(tmp_path) == before


def test_a_real_works_directory_that_is_a_symbolic_link_is_refused(
    tmp_path: Path,
) -> None:
    """AC-7: the directory is judged before it is walked."""
    # Given a repository whose configured Works directory is a symbolic link to
    # a directory of Works
    _write(tmp_path / "real" / "a" / "README.md", COMMENT.format(id="k3m9xq"))
    (tmp_path / "works").symlink_to(tmp_path / "real")

    # When the Works are discovered through the real file system
    found = discover_works(
        tmp_path, Works(dir="works", hierarchy="nesting"), LocalFileSystem()
    )

    # Then there is no Work and one error that begins `The Works directory`
    assert found.works == ()
    assert [d.message.startswith("The Works directory") for d in found.diagnostics] == [
        True
    ]


def test_a_real_empty_works_directory_holds_no_works(tmp_path: Path) -> None:
    """AC-7: an empty Works directory gives no Work and no diagnostic."""
    # Given a repository with an empty configured Works directory
    (tmp_path / "works").mkdir()

    # When the Works are discovered through the real file system
    found = discover_works(
        tmp_path, Works(dir="works", hierarchy="nesting"), LocalFileSystem()
    )

    # Then there is no Work and no diagnostic
    assert (found.works, found.diagnostics) == ((), ())


def test_real_symbolic_links_and_hidden_directories_are_reasons(
    tmp_path: Path,
) -> None:
    """AC-8: a link, a path through a link and a hidden directory, on disk."""
    # Given a repository with a symbolic link to a marked file, a symbolic link
    # to a directory with one, a hidden directory with one, and a directory
    works = tmp_path / "works"
    target = _write(tmp_path / "elsewhere.md", COMMENT.format(id="linked"))
    _write(tmp_path / "other" / "inner.md", COMMENT.format(id="inner"))
    _write(works / ".h" / "m.md", COMMENT.format(id="hidden"))
    (works / "link.md").symlink_to(target)
    (works / "lnk").symlink_to(tmp_path / "other")
    settings = Works(dir="works", hierarchy="flat")

    # When the reason each is not a Work is asked for through the real file system
    paths = ("link.md", "lnk/inner.md", ".h/m.md", "lnk")
    reasons = [
        explain_not_a_work(tmp_path, Path("works") / p, settings, LocalFileSystem())
        for p in paths
    ]

    # Then the link and the path through it name a symbolic link, the hidden
    # directory is named, and a directory is not a file
    assert "symbolic link" in str(reasons[0])
    assert "symbolic link" in str(reasons[1])
    assert "hidden" in str(reasons[2])
    assert "not a file" in str(reasons[3])
