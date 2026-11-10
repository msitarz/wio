# SPDX-License-Identifier: Apache-2.0
"""Tests of the discovery of templates in `wio.templates`."""

from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from tests.unit.fakes import ROOT, MemoryFileSystem
from wio.models.config import Templates
from wio.models.frozen import freeze
from wio.templates import discover

if TYPE_CHECKING:
    from wio.templates import Discovery

DIR = ROOT / ".agents" / "wio" / "templates"


def _block(*lines: str) -> str:
    """Write a template whose comment block holds the given lines.

    Args:
        *lines: The lines of TOML, one per argument.

    Returns:
        The text of a Markdown file that opens with that block.
    """
    return "\n".join(["<!-- wio", *lines, "-->", "", "# Title", ""])


def _find(disk: MemoryFileSystem, settings: Templates | None = None) -> Discovery:
    """Find the templates of the disk.

    Args:
        disk: The files.
        settings: The `[templates]` table; the defaults when not given.

    Returns:
        What the walk found.
    """
    return discover(ROOT, settings or Templates(), disk)


def test_the_walk_finds_the_marked_files_and_names_them_by_their_file() -> None:
    """AC-1: only marked `.md` files outside hidden directories are templates."""
    # Given a directory with two templates, a file with no block, a hidden
    # directory, an upper-case extension and a symbolic link
    marked = _block('kind = "feature"')
    disk = MemoryFileSystem(
        {
            DIR / "feature.leaf.md": marked,
            DIR / "notes.md": "# Notes\n",
            DIR / "sub" / "feature.parent.md": marked,
            DIR / ".hidden" / "x.md": marked,
            DIR / "Upper.MD": marked,
            DIR / "link.md": marked,
        },
        links={DIR / "link.md"},
    )

    # When the templates are found
    found = _find(disk)

    # Then they are the two, by their files, and nothing raised an error
    assert [t.name for t in found.templates] == ["feature.leaf", "feature.parent"]
    assert found.diagnostics == ()


def test_a_template_has_its_kind_shape_description_path_and_entry_mark() -> None:
    """AC-2: each field of a template is what its block and the config say."""
    # Given the kind `feature` with its entry and two templates, one with a shape
    # and a description and one with neither
    disk = MemoryFileSystem(
        {
            DIR / "feature.draft.md": _block(
                'kind = "feature"', 'shape = "draft"', 'description = "A draft."'
            ),
            DIR / "feature.leaf.md": _block('kind = "feature"'),
        }
    )
    kinds = freeze({"feature": "feature.draft"})

    # When the templates are found
    found = _find(disk, Templates(kinds=kinds))

    # Then the draft is the entry with its shape and description, the leaf is
    # not and has neither, and each has its path from the root
    draft, leaf = found.templates
    assert (draft.kind, draft.shape, draft.description, draft.entry) == (
        "feature",
        "draft",
        "A draft.",
        True,
    )
    assert (leaf.shape, leaf.description, leaf.entry) == (None, None, False)
    assert draft.path == Path(".agents/wio/templates/feature.draft.md")


@pytest.mark.parametrize(
    ("text", "place", "message"),
    [
        (_block("kind ="), ".agents/wio/templates/a.md:2", "Invalid value"),
        ("<!-- wio\nkind = 1\n", ".agents/wio/templates/a.md:1", "does not close"),
        (_block('shape = "leaf"'), ".agents/wio/templates/a.md", "needs a `kind`"),
        (_block("kind = 1"), ".agents/wio/templates/a.md", "`kind` must be a string"),
        (
            _block('kind = "k"', "shape = 1"),
            ".agents/wio/templates/a.md",
            "`shape` must be a string",
        ),
        (
            _block('kind = "k"', "description = 1"),
            ".agents/wio/templates/a.md",
            "`description` must be a string",
        ),
    ],
    ids=["toml", "unclosed", "no-kind", "kind-type", "shape-type", "description-type"],
)
def test_a_file_with_a_problem_is_an_error_and_the_other_templates_stay(
    text: str, place: str, message: str
) -> None:
    """AC-3: each file problem is an error that names the file."""
    # Given a file with the problem and a valid template
    disk = MemoryFileSystem(
        {DIR / "a.md": text, DIR / "b.md": _block('kind = "feature"')}
    )

    # When the templates are found
    found = _find(disk)

    # Then one error names the file and the valid template is still returned
    assert [(d.severity, d.where) for d in found.diagnostics] == [("error", place)]
    assert message in found.diagnostics[0].message
    assert [t.name for t in found.templates] == ["b"]


@pytest.mark.parametrize(
    ("error", "message"),
    [
        (UnicodeDecodeError("utf-8", b"\xff", 0, 1, "bad"), "not valid UTF-8"),
        (PermissionError(13, "Permission denied"), "cannot be read"),
    ],
    ids=["encoding", "permission"],
)
def test_a_file_that_cannot_be_read_is_an_error(error: Exception, message: str) -> None:
    """AC-3: a file that cannot be read or decoded is an error that names it."""
    # Given a file that raises when it is read, and a valid template
    disk = MemoryFileSystem(
        {DIR / "a.md": "x", DIR / "b.md": _block('kind = "feature"')},
        broken={DIR / "a.md": error},
    )

    # When the templates are found
    found = _find(disk)

    # Then one error names the file and the valid template is still returned
    assert [d.where for d in found.diagnostics] == [".agents/wio/templates/a.md"]
    assert message in found.diagnostics[0].message
    assert [t.name for t in found.templates] == ["b"]


def test_two_files_with_one_name_are_one_error_that_names_both() -> None:
    """AC-3: a shared name is an error naming both files, and neither is kept."""
    # Given two templates named `a.md` in different directories and another one
    marked = _block('kind = "feature"')
    disk = MemoryFileSystem(
        {DIR / "x" / "a.md": marked, DIR / "y" / "a.md": marked, DIR / "b.md": marked}
    )

    # When the templates are found
    found = _find(disk)

    # Then one error names both files, and only `b` is returned
    assert [d.where for d in found.diagnostics] == [
        ".agents/wio/templates/x/a.md, .agents/wio/templates/y/a.md"
    ]
    assert "`a`" in found.diagnostics[0].message
    assert [t.name for t in found.templates] == ["b"]


@pytest.mark.parametrize(
    ("kind", "message"),
    [
        ("missing", "does not exist"),
        ("file", "not a directory"),
        ("link", "symbolic link"),
    ],
)
def test_a_templates_directory_that_cannot_be_walked_is_an_error(
    kind: str, message: str
) -> None:
    """AC-3: a set directory that is missing, a file or a link is one error."""
    # Given `[templates] dir = "t"` that is missing, a file or a symbolic link
    marked = _block('kind = "feature"')
    disk = MemoryFileSystem(
        {
            "missing": {},
            "file": {ROOT / "t": "text"},
            "link": {ROOT / "t" / "a.md": marked},
        }[kind],
        links={ROOT / "t"} if kind == "link" else set(),
    )

    # When the templates are found
    found = _find(disk, Templates(dir="t"))

    # Then one error names the directory and no template is returned
    assert [d.where for d in found.diagnostics] == ["t"]
    assert message in found.diagnostics[0].message
    assert found.templates == ()


def test_a_missing_default_directory_holds_no_templates() -> None:
    """AC-3: the default directory may be absent, and no diagnostic is given."""
    # Given a repository with no templates directory and no `[templates] dir`
    disk = MemoryFileSystem({ROOT / "README.md": "# x\n"})

    # When the templates are found
    found = _find(disk)

    # Then there are none and no diagnostic
    assert (found.templates, found.diagnostics) == ((), ())
