# SPDX-License-Identifier: Apache-2.0
"""Tests of showing a template as a skeleton in `wio.templates`."""

lazy from pathlib import Path

import pytest

from tests.unit.fakes import ROOT, MemoryFileSystem
from wio.formats import prepare_skeleton
from wio.models.config import Templates
from wio.templates import Discovery, TemplatesError, discover, show_skeleton

DIR = ROOT / ".agents" / "wio" / "templates"
LEAF = (
    '<!-- wio\nkind = "feature"\n[contract]\nroots = []\n-->\n\n'
    "## A <!-- wio: required -->\n"
)
PARENT = '<!-- wio\nkind = "feature"\n[contract]\nroots = ["x"]\n-->\n\n# P\n'


def _show(name: str, files: dict[Path, str]) -> str:
    """Find the templates over files and show one.

    Args:
        name: The name to show.
        files: The stored files.

    Returns:
        The skeleton.
    """
    memory = MemoryFileSystem(files)
    found = discover(ROOT, Templates(), memory)
    assert found.diagnostics == ()
    return show_skeleton(name, found, ROOT, memory)


def _project() -> dict[Path, str]:
    """Give the files of a project with two templates.

    Returns:
        The stored files.
    """
    return {DIR / "feature.leaf.md": LEAF, DIR / "feature.parent.md": PARENT}


def test_the_skeleton_of_the_named_template_is_what_the_skeleton_function_gives() -> (
    None
):
    """AC-1: the text is the skeleton of that file under the template's name."""
    # Given a project with the templates `feature.leaf` and `feature.parent`
    files = _project()

    # When the skeleton of `feature.leaf` is shown, and again
    first = _show("feature.leaf", files)
    second = _show("feature.leaf", files)

    # Then it is what the skeleton function gives for that file's text under that
    # name, and the two results are equal
    assert first == prepare_skeleton("feature.leaf", LEAF)
    assert first == second


@pytest.mark.parametrize(
    "name", ["nosuch", "Feature.Leaf", "feature", "feature.leaf.md"]
)
def test_a_name_that_no_template_has_lists_the_names_that_exist(name: str) -> None:
    """AC-2: an unknown name, another case and a kind are refused with the names."""
    # Given a project with two templates of the kind `feature`
    files = _project()

    # When a name that is not a template's name is shown
    with pytest.raises(TemplatesError) as caught:
        _show(name, files)

    # Then the error names what was given and lists the names that exist
    message = str(caught.value)
    assert f"`{name}`" in message
    assert "`feature.leaf`, `feature.parent`" in message
    assert caught.value.diagnostics == ()


def test_a_project_without_templates_says_that_none_exists() -> None:
    """AC-2: with no template, the refusal says so instead of listing nothing."""
    # Given a project with no templates
    found = Discovery((), ())

    # When a name is shown
    with pytest.raises(TemplatesError) as caught:
        show_skeleton("x", found, ROOT, MemoryFileSystem())

    # Then the error names it and says that no template exists
    assert "`x`" in str(caught.value)
    assert "no template exists" in str(caught.value)


def test_a_bad_directive_list_names_the_file_the_line_and_the_column() -> None:
    """AC-3: the file is added to the error of the skeleton function."""
    # Given a template whose line 12 is `## A <!-- wio: mandatory -->`
    lines = [
        "<!-- wio",
        'kind = "feature"',
        "-->",
        *[""] * 8,
        "## A <!-- wio: mandatory -->",
    ]
    files = {DIR / "feature.leaf.md": "\n".join(lines) + "\n"}

    # When it is shown
    with pytest.raises(TemplatesError) as caught:
        _show("feature.leaf", files)

    # Then the error holds one diagnostic whose place is the file, line 12 and
    # column 16, and ends with the hint
    [found] = caught.value.diagnostics
    assert found.where == ".agents/wio/templates/feature.leaf.md:12:16"
    assert found.severity == "error"
    assert "`wio templates check` shows every problem." in str(caught.value)
    assert str(caught.value).startswith(
        "error: .agents/wio/templates/feature.leaf.md:12:16:"
    )


@pytest.mark.parametrize(
    ("text", "place", "message"),
    [
        ('<!-- wio\nkind = "k"\n', "feature.leaf.md:1", "does not close"),
        ("# No block\n", "feature.leaf.md", "not a template"),
    ],
    ids=["block-does-not-close", "no-block"],
)
def test_a_template_that_the_skeleton_function_refuses_names_its_file(
    text: str, place: str, message: str
) -> None:
    """AC-3: an error that discovery did not see names the file, with its line."""
    # Given a template that the walk found, whose text is now one that cannot be
    # prepared, so the file changed after the walk
    walked = {DIR / "feature.leaf.md": LEAF}
    found = discover(ROOT, Templates(), MemoryFileSystem(walked))
    later = MemoryFileSystem({DIR / "feature.leaf.md": text})

    # When it is shown
    with pytest.raises(TemplatesError) as caught:
        show_skeleton("feature.leaf", found, ROOT, later)

    # Then the error holds one diagnostic whose place is the file and its line
    [diagnostic] = caught.value.diagnostics
    assert diagnostic.where == f".agents/wio/templates/{place}"
    assert message in diagnostic.message


@pytest.mark.parametrize(
    ("error", "message"),
    [
        (UnicodeDecodeError("utf-8", b"\xff", 0, 1, "bad"), "not valid UTF-8"),
        (PermissionError(13, "Permission denied"), "cannot be read"),
    ],
    ids=["encoding", "permission"],
)
def test_a_file_that_cannot_be_read_after_the_walk_is_an_error_for_the_file(
    error: Exception, message: str
) -> None:
    """AC-3: a late read failure is worded as the walk words it."""
    # Given a template that was found and now cannot be read
    walked = {DIR / "feature.leaf.md": LEAF}
    found = discover(ROOT, Templates(), MemoryFileSystem(walked))
    later = MemoryFileSystem(walked, broken={DIR / "feature.leaf.md": error})

    # When it is shown
    with pytest.raises(TemplatesError) as caught:
        show_skeleton("feature.leaf", found, ROOT, later)

    # Then one diagnostic names the file
    [diagnostic] = caught.value.diagnostics
    assert diagnostic.where == ".agents/wio/templates/feature.leaf.md"
    assert message in diagnostic.message


def test_the_place_of_a_nested_template_is_its_path_from_the_root() -> None:
    """AC-3: a template below a subdirectory is named by its path with `/`."""
    # Given a template in a subdirectory whose block does not close after the walk
    nested = DIR / "sub" / "feature.leaf.md"
    found = discover(ROOT, Templates(), MemoryFileSystem({nested: LEAF}))
    later = MemoryFileSystem({nested: '<!-- wio\nkind = "k"\n'})

    # When it is shown
    with pytest.raises(TemplatesError) as caught:
        show_skeleton("feature.leaf", found, ROOT, later)

    # Then the place is the path from the root, written with `/`, and the line
    [diagnostic] = caught.value.diagnostics
    assert diagnostic.where == ".agents/wio/templates/sub/feature.leaf.md:1"
