# SPDX-License-Identifier: Apache-2.0
"""Tests of the resolved view of a Work, one for each scenario of its contract."""

from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from tests.unit.fakes import ROOT, MemoryFileSystem
from wio.contracts.hierarchy import build_hierarchy
from wio.contracts.resolve import render_resolved, resolve_work
from wio.models.frozen import freeze
from wio.models.template import Template
from wio.models.works import Work

if TYPE_CHECKING:
    from collections.abc import Collection, Sequence

    from wio.models.config import HierarchyMode

INHERIT = " <!-- wio: inherit -->"
"""The directive list that marks a section of a template inheritable."""


class _Catalog:
    """A stub `TemplateCatalog` over templates whose files it writes."""

    def __init__(
        self,
        files: MemoryFileSystem,
        templates: dict[str, tuple[str, ...]],
        rejected: Collection[str] = (),
    ) -> None:
        """Write the template files and keep what the catalog answers.

        Args:
            files: The file system the template files are written to.
            templates: Each template's name and the headings of its body.
            rejected: The names `is_rejected` says are rejected.
        """
        self._found: dict[str, Template] = {}
        self._rejected = frozenset(rejected)
        for name, headings in templates.items():
            path = Path("templates") / f"{name}.md"
            block = '+++\nwio = 1\nkind = "feature"\n+++\n\n'
            files.files[ROOT / path] = block + "\n\n".join(headings) + "\n"
            self._found[name] = Template(name, "feature", None, None, path, entry=False)

    def find(self, name: str) -> Template | None:
        """Find a template.

        Args:
            name: The template's name.

        Returns:
            The template, or `None` for a name the stub does not have.
        """
        return self._found.get(name)

    def is_rejected(self, name: str) -> bool:
        """Say whether a template is rejected.

        Args:
            name: The template's name.

        Returns:
            Whether the stub was given the name as rejected.
        """
        return name in self._rejected


def _marks(*names: str) -> tuple[str, ...]:
    """Give the headings of a template that marks sections inheritable.

    Args:
        names: The sections to mark.

    Returns:
        A `## Purpose` heading and each name as a level-2 heading with `inherit`.
    """
    return ("## Purpose", *(f"## {name}{INHERIT}" for name in names))


def _add(
    files: MemoryFileSystem,
    path: str,
    work_id: str,
    body: str,
    template: str | None = None,
) -> Work:
    """Write a contract with a `+++` block and give its Work.

    Args:
        files: The file system to write to.
        path: The file, relative to the repository root.
        work_id: The id.
        body: The text after the block, written as given.
        template: The template the block names, or `None`.

    Returns:
        The Work of the file.
    """
    lines = ["+++", "wio = 1", f'id = "{work_id}"']
    if template is not None:
        lines.append(f'template = "{template}"')
    files.files[ROOT / path] = "\n".join([*lines, "+++", "", body])
    return Work(
        id=work_id,
        title=None,
        path=Path(path),
        template=template,
        roots=(),
        depends_on=(),
        actions=freeze({}),
    )


def _view(
    work: Work,
    works: Sequence[Work],
    files: MemoryFileSystem,
    catalog: _Catalog,
    mode: HierarchyMode = "nesting",
) -> str:
    """Resolve and render a Work among others.

    Args:
        work: The Work to view.
        works: Every Work of the tree.
        files: The file system.
        catalog: The stub catalog.
        mode: The hierarchy mode.

    Returns:
        The rendered view.
    """
    ancestors = build_hierarchy(works, mode).ancestors[work.path]
    return render_resolved(resolve_work(work, ancestors, catalog, ROOT, files))


def _constraints(line: str = "A line.") -> str:
    """Give a body with a title, a Purpose and a Constraints section.

    Args:
        line: The text of the Constraints section.

    Returns:
        The body.
    """
    return f"# T\n\n## Purpose\n\nWhy.\n\n## Constraints\n\n{line}\n"


def test_the_view_holds_the_work_and_what_its_parent_passes_on() -> None:
    """AC-1: a child of a parent."""
    # Given a parent that marks Glossary and Constraints inherit, and a child
    files = MemoryFileSystem()
    catalog = _Catalog(files, {"t": _marks("Glossary", "Constraints")})
    parent_body = (
        "# Parent\n\n## Purpose\n\nWhy.\n\n## Glossary\n\n- **Term**: a word.\n\n"
        "## Constraints\n\nA line.\n\n### Detail\n\nMore.\n"
    )
    parent = _add(files, "p/README.md", "p5n2hv", parent_body, "t")
    child_body = (
        "# Child\n\n## Purpose\n\nOwn text.\n\n## Constraints\n\nOwn constraint.\n"
    )
    child = _add(files, "p/c/README.md", "c", child_body)

    # When the view of the child is rendered
    text = _view(child, [parent, child], files, catalog)

    # Then it is exactly the text of AC-1, ending in one line ending
    assert text == (
        "# Child\n\n## Purpose\n\nOwn text.\n\n## Constraints\n\nOwn constraint.\n\n"
        "## Inherited from: Parent (p5n2hv)\n\n### Glossary\n\n- **Term**: a word.\n\n"
        "### Constraints\n\nA line.\n\n#### Detail\n\nMore.\n"
    )


def _three_levels(
    parent_template: str, mode: HierarchyMode = "nesting"
) -> tuple[dict[str, str], Work, Work]:
    """Build the tree of AC-2 and view `c` and `solo`.

    Args:
        parent_template: The template `p` follows.
        mode: The hierarchy mode.

    Returns:
        The view of `c` and of `solo` by name, and the Works `g` and `p`.
    """
    files = MemoryFileSystem()
    catalog = _Catalog(files, {"t.marks": _marks("Constraints"), "t.plain": ("## X",)})
    g = _add(files, "g/README.md", "g", _constraints().replace("# T", "# G"), "t.marks")
    p = _add(files, "g/p/README.md", "p", _constraints(), parent_template)
    c = _add(files, "g/p/c/README.md", "c", "# C\n")
    solo = _add(files, "solo/README.md", "solo", "# Solo\n")
    works = [g, p, c, solo]
    views = {
        "c": _view(c, works, files, catalog, mode),
        "solo": _view(solo, works, files, catalog, mode),
        "g": _view(g, works, files, catalog, mode),
        "p": _view(p, works, files, catalog, mode),
    }
    return views, g, p


def test_the_nearest_ancestor_that_passes_comes_first_and_the_others_are_skipped() -> (
    None
):
    """AC-2: three levels."""
    # Given a grandparent that marks Constraints, a parent that marks nothing, a
    # child and a Work with no parent
    # When the views of the child and of the lone Work are rendered
    views, _, _ = _three_levels("t.plain")

    # Then the child has one `## Inherited from:` section, the grandparent's, and
    # the lone Work has its own contract only
    assert views["c"].count("## Inherited from:") == 1
    assert "## Inherited from: G (g)" in views["c"]
    assert views["solo"] == "# Solo\n"


def test_two_ancestors_that_pass_come_nearest_first() -> None:
    """AC-2: two ancestors that pass."""
    # Given the same tree with the parent marking Constraints too
    # When the view of the child is rendered
    views, _, _ = _three_levels("t.marks")

    # Then the section for the parent comes before the one for the grandparent
    text = views["c"]
    assert text.index("(p)") < text.index("(g)")


def test_under_flat_every_view_is_the_own_contract_only() -> None:
    """AC-2: under flat."""
    # Given `hierarchy = "flat"` and the same tree
    # When the views of g, p and c are rendered
    views, _, _ = _three_levels("t.marks", "flat")

    # Then each is its own contract only
    assert "Inherited from" not in views["c"] + views["p"] + views["g"]
    assert views["c"] == "# C\n"


def test_a_template_marks_sections_matched_by_text_and_a_stray_mark_is_ignored() -> (
    None
):
    """AC-3: a template and a text match."""
    # Given an ancestor whose `## constraints` differs in case and has a trailing
    # space, and a stray inherit on its Purpose
    files = MemoryFileSystem()
    catalog = _Catalog(files, {"t": _marks("Constraints")})
    body = f"# P\n\n## Purpose{INHERIT}\n\nWhy.\n\n## constraints \n\nA line.\n"
    parent = _add(files, "p/README.md", "p", body, "t")
    child = _add(files, "p/c/README.md", "c", "# Child\n")

    # When the view of its child is rendered
    text = _view(child, [parent, child], files, catalog)

    # Then it holds `### constraints` and not the Purpose
    assert "\n### constraints\n" in text
    assert "Purpose" not in text


def test_without_a_template_the_ancestors_own_headings_mark_and_a_repeat_passes() -> (
    None
):
    """AC-3: no template and a repeated section."""
    # Given an ancestor with no template and `## Rules` marked inherit twice
    files = MemoryFileSystem()
    catalog = _Catalog(files, {})
    body = (
        f"# P\n\n## Rules{INHERIT}\n\nOne.\n\n## Notes\n\nNote.\n\n"
        f"## Rules{INHERIT}\n\nTwo.\n"
    )
    parent = _add(files, "p/README.md", "p", body)
    child = _add(files, "p/c/README.md", "c", "# Child\n")

    # When the view of its child is rendered
    text = _view(child, [parent, child], files, catalog)

    # Then it holds `### Rules` twice, in order, without the comment, no Notes
    assert text.endswith("### Rules\n\nOne.\n\n### Rules\n\nTwo.\n")
    assert "Notes" not in text
    assert "wio:" not in text


def test_an_ancestor_whose_template_cannot_be_used_passes_nothing_and_stops_nothing() -> (  # noqa: E501
    None
):
    """AC-4: three ancestors."""
    # Given children of a missing, a rejected and an unreadable template, under a
    # grandparent with an inheritable Constraints
    files = MemoryFileSystem()
    catalog = _Catalog(
        files,
        {
            "t.marks": _marks("Constraints"),
            "t.rejected": _marks("Constraints"),
            "t.broken": _marks("Constraints"),
        },
        rejected=["t.rejected"],
    )
    files.broken[ROOT / "templates/t.broken.md"] = UnicodeDecodeError(
        "utf-8", b"", 0, 1, "bad"
    )
    g = _add(files, "g/README.md", "g", _constraints().replace("# T", "# G"), "t.marks")
    names = {"a": "t.missing", "b": "t.rejected", "c": "t.broken"}
    parents = [
        _add(files, f"g/{n}/README.md", n, _constraints(), t) for n, t in names.items()
    ]
    kids = [_add(files, f"g/{n}/k/README.md", f"k{n}", "# K\n") for n in names]
    works = [g, *parents, *kids]

    # When the three views are rendered
    views = [_view(kid, works, files, catalog) for kid in kids]

    # Then each holds the child's contract and one section for the grandparent
    for view in views:
        assert view.startswith("# K\n\n## Inherited from: G (g)\n")
        assert view.count("## Inherited from:") == 1


def _front_matter_child(files: MemoryFileSystem) -> Work:
    """Write the CRLF child of AC-5.

    Args:
        files: The file system to write to.

    Returns:
        The child's Work.
    """
    body = (
        "# Child\n\n<!-- Write ## X here. -->\n\n## Goals <!-- wio: required -->\n\n"
        "Goal text.\n"
    )
    child = _add(files, "p5/c/README.md", "c", body)
    files.files[ROOT / child.path] = files.files[ROOT / child.path].replace(
        "\n", "\r\n"
    )
    return child


def test_the_metadata_block_and_directive_lists_are_cleaned_and_the_text_repeats() -> (
    None
):
    """AC-5: cleaning."""
    # Given a CRLF child with front matter and a parent with a comment-only
    # Glossary and a stray inherit on Purpose
    files = MemoryFileSystem()
    catalog = _Catalog(files, {"t": _marks("Glossary", "Constraints")})
    parent_body = (
        f"# Parent\n\n## Purpose{INHERIT}\n\nWhy.\n\n## Glossary\n\n<!-- g -->\n\n"
        "## Constraints\n\nA line.\n\n<!-- c -->\n\n"
        "### Detail <!-- wio: required -->\n\nDeep.\n"
    )
    parent = _add(files, "p5/README.md", "p5n2hv", parent_body, "t")
    child = _front_matter_child(files)

    # When the view of the child is rendered, and rendered again
    first = _view(child, [parent, child], files, catalog)
    second = _view(child, [parent, child], files, catalog)

    # Then both are the text of AC-5, with LF endings only
    assert first == second
    assert first == (
        "# Child\n\n<!-- Write ## X here. -->\n\n## Goals\n\nGoal text.\n\n"
        "## Inherited from: Parent (p5n2hv)\n\n### Constraints\n\nA line.\n\n"
        "<!-- c -->\n\n#### Detail\n\nDeep.\n"
    )
    assert "\r" not in first


def test_a_level_six_heading_stays_and_a_bad_directive_list_is_left_as_written() -> (
    None
):
    """AC-5: a deep heading and a bad list."""
    # Given an ancestor with a level-6 heading and `## Rules` with a bad list
    files = MemoryFileSystem()
    catalog = _Catalog(files, {"t": _marks("Constraints", "Rules")})
    body = (
        "# P\n\n## Constraints\n\n###### Deep\n\nText.\n\n"
        "## Rules <!-- wio: mandatory -->\n\nRule.\n"
    )
    parent = _add(files, "p/README.md", "p", body, "t")
    child = _add(files, "p/c/README.md", "c", "# Child\n")

    # When the view of a child is rendered
    text = _view(child, [parent, child], files, catalog)

    # Then the level-6 heading stays at 6 and the bad list stays in its heading
    assert "\n###### Deep\n" in text
    assert "\n### Rules <!-- wio: mandatory -->\n\nRule.\n" in text


def test_files_that_cannot_be_read_pass_nothing_and_raise_nothing() -> None:
    """AC-5: files that cannot be read."""
    # Given a file system that raises OSError on the resolver's own read of one
    # parent's template and of another parent's file
    files = MemoryFileSystem()
    catalog = _Catalog(
        files, {"t.b": _marks("Constraints"), "t.marks": _marks("Constraints")}
    )
    files.broken[ROOT / "templates/t.b.md"] = PermissionError("no")
    g = _add(files, "g/README.md", "g", _constraints().replace("# T", "# G"), "t.marks")
    b = _add(files, "g/b/README.md", "b", _constraints(), "t.b")
    c = _add(files, "g/c/README.md", "c", _constraints(), "t.marks")
    files.broken[ROOT / c.path] = PermissionError("no")
    kids = [_add(files, f"g/{n}/k/README.md", f"k{n}", "# K\n") for n in "bc"]

    # When the views of the two children are rendered
    views = [
        render_resolved(resolve_work(kid, (parent, g), catalog, ROOT, files))
        for kid, parent in zip(kids, (b, c), strict=True)
    ]

    # Then each holds the child's contract and one section for the grandparent
    for view in views:
        assert view.startswith("# K\n\n## Inherited from: G (g)\n")
        assert view.count("## Inherited from:") == 1


def _parent_view(parent_body: str, marks: tuple[str, ...]) -> str:
    """View a child with an empty own contract under a parent.

    Args:
        parent_body: The parent's body.
        marks: The sections the parent's template marks.

    Returns:
        The child's view.
    """
    files = MemoryFileSystem()
    catalog = _Catalog(files, {"t": _marks(*marks)})
    parent = _add(files, "p/README.md", "p5n2hv", parent_body, "t")
    child = _add(files, "p/c/README.md", "c", "")
    return _view(child, [parent, child], files, catalog)


def test_a_section_runs_to_the_next_heading_of_level_one_or_two() -> None:
    """AC-6: the extent of a section."""
    # Given a parent whose Constraints holds only a level-3 heading and a `# Next`
    # that ends it, then Notes
    body = (
        "# Parent\n\n## Constraints\n\n### Detail\n\nMore.\n\n# Next\n\n"
        "## Notes\n\nNote.\n"
    )

    # When the view of a child with an empty own contract is rendered
    text = _parent_view(body, ("Constraints", "Notes"))

    # Then it is exactly the text of AC-6
    assert text == (
        "## Inherited from: Parent (p5n2hv)\n\n### Constraints\n\n#### Detail\n\n"
        "More.\n\n### Notes\n\nNote.\n"
    )


def test_a_title_with_a_directive_list_is_named_without_it() -> None:
    """AC-6: an ancestor whose title carries a directive list."""
    # Given a parent whose title is `# Parent <!-- wio: required -->`
    body = "# Parent <!-- wio: required -->\n\n## Constraints\n\nA line.\n"

    # When the view of a child with an empty own contract is rendered
    text = _parent_view(body, ("Constraints",))

    # Then it begins with `## Inherited from: Parent (p5n2hv)`
    assert text.startswith("## Inherited from: Parent (p5n2hv)\n")


def test_an_ancestor_without_a_level_one_heading_is_named_by_its_first_heading() -> (
    None
):
    """AC-6: an ancestor named by its first heading."""
    # Given a parent whose body starts with `## Purpose`
    body = "## Purpose\n\nWhy.\n\n## Constraints\n\nA line.\n"

    # When the view of a child with an empty own contract is rendered
    text = _parent_view(body, ("Constraints",))

    # Then it begins with `## Inherited from: Purpose (p5n2hv)`
    assert text.startswith("## Inherited from: Purpose (p5n2hv)\n")


@pytest.mark.parametrize(
    ("body", "expected"),
    [
        ("# P\n\n    ## Constraints\n\nA line.\n", ""),
        ("# P\n\n## Constraints\n\n<!-- only -->\n\n  \n", ""),
    ],
)
def test_an_indented_heading_and_a_section_with_no_content_pass_nothing(
    body: str, expected: str
) -> None:
    """An indented heading never matches, and a comment-only section is dropped."""
    # Given a parent with an indented `## Constraints` or a comment-only one
    # When the view of a child with an empty own contract is rendered
    text = _parent_view(body, ("Constraints",))

    # Then nothing is passed
    assert text == expected


def test_closing_marks_are_not_part_of_a_title_or_of_the_text_a_section_matches() -> (
    None
):
    """A closing sequence of `#` marks is left out of the title and of the match."""
    # Given a parent titled `# Parent ##` whose `## Constraints ##` the template
    # marks as `## Constraints ## <!-- wio: inherit -->`
    files = MemoryFileSystem()
    catalog = _Catalog(files, {"t": ("## Constraints ##" + INHERIT,)})
    body = "# Parent ##\n\n## Constraints ##\n\nA line.\n"
    parent = _add(files, "p/README.md", "p5n2hv", body, "t")
    child = _add(files, "p/c/README.md", "c", "")

    # When the view of a child with an empty own contract is rendered
    text = _view(child, [parent, child], files, catalog)

    # Then the ancestor is named `Parent` and the section passes
    assert text == (
        "## Inherited from: Parent (p5n2hv)\n\n### Constraints ##\n\nA line.\n"
    )


def test_a_closing_sequence_before_a_directive_list_is_left_out_of_the_title() -> None:
    """A title with a closing sequence and then a readable list is named plainly."""
    # Given a parent titled `# Parent # <!-- wio: required -->`
    body = "# Parent # <!-- wio: required -->\n\n## Constraints\n\nA line.\n"

    # When the view of a child with an empty own contract is rendered
    text = _parent_view(body, ("Constraints",))

    # Then it begins with `## Inherited from: Parent (p5n2hv)`
    assert text.startswith("## Inherited from: Parent (p5n2hv)\n")


def test_the_works_own_file_that_cannot_be_read_is_not_swallowed() -> None:
    """A failed read of the Work's own file reaches the caller."""
    # Given a Work whose file raises an OSError
    files = MemoryFileSystem()
    catalog = _Catalog(files, {})
    child = _add(files, "c/README.md", "c", "# C\n")
    files.broken[ROOT / child.path] = PermissionError("no")

    # When the Work is resolved
    # Then the error is raised
    with pytest.raises(PermissionError):
        resolve_work(child, (), catalog, ROOT, files)
