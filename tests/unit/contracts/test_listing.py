# SPDX-License-Identifier: Apache-2.0
"""Tests of the listing of Works."""

import json
from argparse import Namespace
from pathlib import Path
from typing import TYPE_CHECKING, Literal, cast

import pytest

from tests.unit.fakes import ROOT, FakeRepository, FakeStdio, MemoryFileSystem
from wio.contracts import ContractsError, Services
from wio.contracts.hierarchy import build_hierarchy
from wio.contracts.listing import render_list, run_list
from wio.models.config import Config, HierarchyMode, Works
from wio.models.frozen import freeze
from wio.models.works import Work

if TYPE_CHECKING:
    import io
    from collections.abc import Mapping

BASE = ".agents/wio/works"


def _work(
    path: str,
    work_id: str,
    title: str | None = None,
    template: str | None = None,
    roots: tuple[str, ...] = (),
    depends_on: tuple[str, ...] = (),
    actions: Mapping[str, str | tuple[str, ...]] | None = None,
) -> Work:
    """Build a Work at `<Works directory>/<path>`.

    Args:
        path: The file, relative to the Works directory.
        work_id: The id.
        title: The title, or `None`.
        template: The template, or `None`.
        roots: The roots as written.
        depends_on: The dependencies as written.
        actions: The `[actions]` overrides.

    Returns:
        The Work.
    """
    return Work(
        id=work_id,
        title=title,
        path=Path(BASE) / path,
        template=template,
        roots=roots,
        depends_on=depends_on,
        actions=freeze(actions or {}),
    )


def _text(mode: HierarchyMode, *works: Work) -> str:
    """Render Works as text.

    Args:
        mode: The hierarchy mode.
        *works: The Works.

    Returns:
        The text.
    """
    return render_list(build_hierarchy(works, mode), as_json=False)


def test_a_parent_comes_before_its_children_and_each_child_is_indented() -> None:
    """Children follow their parent, two spaces deeper, in the order of paths."""
    # Given a parent with two children, one of which has a child, and a Work
    # whose path sorts between them
    works = [
        _work("p/README.md", "p1", "Parent"),
        _work("p/a/README.md", "c1", "First"),
        _work("p/a/x/README.md", "g1", "Grandchild"),
        _work("p/b/README.md", "c2", "Second"),
        _work("q/README.md", "q1", "Other"),
    ]

    # When the Works are rendered as text under nesting
    lines = _text("nesting", *works).splitlines()

    # Then each Work is after its parent and before the next sibling, and is
    # indented two more spaces than its parent, with its path under the title
    assert [line for line in lines if not line.lstrip().startswith(BASE)] == [
        "p1  Parent",
        "  c1  First",
        "    g1  Grandchild",
        "  c2  Second",
        "q1  Other",
    ]
    assert lines[1] == f"    {BASE}/p/README.md"
    assert lines[3] == f"      {BASE}/p/a/README.md"
    assert lines[5] == f"        {BASE}/p/a/x/README.md"


def test_the_id_column_is_as_wide_as_the_widest_id_of_the_output() -> None:
    """Every title lines up, whatever the depth of its Work."""
    # Given a short id at the top and a long one in another branch
    works = [
        _work("a/README.md", "a1", "Short"),
        _work("b/README.md", "b1", "Parent"),
        _work("b/c/README.md", "longer-id", "Long"),
    ]

    # When the Works are rendered as text under nesting
    lines = _text("nesting", *works).splitlines()

    # Then every id is padded to the widest and the details start at the title
    assert lines[0] == "a1         Short"
    assert lines[1] == f"           {BASE}/a/README.md"
    assert lines[4] == "  longer-id  Long"
    assert lines[5].startswith(" " * 13 + BASE)


def test_under_flat_every_work_is_at_the_same_indent() -> None:
    """A path that nests is no hierarchy under flat."""
    # Given Works whose paths nest
    works = [
        _work("p/README.md", "p1", "Parent"),
        _work("p/a/README.md", "c1", "Child"),
    ]

    # When the Works are rendered as text under flat
    lines = _text("flat", *works).splitlines()

    # Then both are at the left edge, in the order of their paths
    assert [line for line in lines if not line.startswith(" ")] == [
        "p1  Parent",
        "c1  Child",
    ]


def test_only_the_overrides_of_a_work_show() -> None:
    """A preset, a list and an empty list are written as the contract says."""
    # Given a Work whose `[actions]` hold a preset, a list and an empty list
    work = _work(
        "a/README.md",
        "k3m9xq",
        "Title",
        "feature.leaf",
        actions={"deliver": ("build", "run"), "define": "define-feature", "x": ()},
    )

    # When it is rendered as text
    lines = _text("flat", work).splitlines()

    # Then the line is in the order written, with `none` for the empty list
    assert lines[0] == "k3m9xq  Title  [feature.leaf]"
    assert lines[2] == (
        "        actions: deliver = [build, run], define = define-feature, x = none"
    )
    assert len(lines) == 3


def test_a_dependency_shows_its_title_or_says_why_not() -> None:
    """The `after:` lines read the title, `(no title)` and `(not found)`."""
    # Given a Work that lists a Work with a title, one with none, an id that no
    # Work has, and the first one again
    works = [
        _work("a/README.md", "a1", depends_on=("t1", "n1", "zz", "t1")),
        _work("n/README.md", "n1"),
        _work("t/README.md", "t1", "Titled"),
    ]

    # When the Works are rendered as text under flat
    lines = _text("flat", *works).splitlines()

    # Then each dependency is a line in the order listed, as many times as listed
    after = [line.strip() for line in lines if line.strip().startswith("after:")]
    assert after == [
        "after: t1 Titled",
        "after: n1 (no title)",
        "after: zz (not found)",
        "after: t1 Titled",
    ]


def test_a_work_with_nothing_to_say_has_its_path_only() -> None:
    """No roots, dependencies or actions give no line."""
    # Given a Work with a title and a template and nothing else
    work = _work("a/README.md", "a1", "Title")

    # When it is rendered
    text = _text("flat", work)

    # Then it is two lines and no template brackets
    assert text == f"a1  Title\n    {BASE}/a/README.md\n"


def _array(mode: HierarchyMode, *works: Work) -> list[dict[str, object]]:
    """Render Works as JSON and read it back.

    Args:
        mode: The hierarchy mode.
        *works: The Works.

    Returns:
        The objects of the array.
    """
    text = render_list(build_hierarchy(works, mode), as_json=True)
    assert text.endswith("\n")
    assert "\n" not in text[:-1]
    return cast("list[dict[str, object]]", json.loads(text))


def test_json_is_one_array_in_the_order_of_the_paths() -> None:
    """The array is sorted by path alone, so a child can come before its parent."""
    # Given a parent whose file sorts after the directory of its child
    works = [
        _work("p/spec.md", "p1", "Parent"),
        _work("p/a/README.md", "c1", "Child"),
    ]

    # When the Works are rendered as JSON and as text under nesting
    array = _array("nesting", *works)
    text = _text("nesting", *works)

    # Then the JSON has the child first with its parent's id, and the text has
    # the parent first
    assert [obj["id"] for obj in array] == ["c1", "p1"]
    assert array[0]["parent"] == "p1"
    assert array[1]["parent"] is None
    assert text.splitlines()[0] == "p1  Parent"


def test_the_fields_of_an_object_are_in_a_fixed_order() -> None:
    """Each object has the eight fields in the order of the contract."""
    # Given a Work with every field
    work = _work(
        "a/README.md",
        "a1",
        "Title",
        "feature.leaf",
        ("api",),
        ("b1",),
        {"deliver": ("x",), "define": "d"},
    )

    # When it is rendered as JSON
    [obj] = _array("flat", work)

    # Then the keys are in order, the lists are lists and the path has `/`
    assert list(obj) == [
        "id",
        "title",
        "path",
        "template",
        "roots",
        "depends_on",
        "actions",
        "parent",
    ]
    assert obj["actions"] == {"deliver": ["x"], "define": "d"}
    assert obj["path"] == f"{BASE}/a/README.md"


def test_a_tree_with_no_work_renders_nothing_or_an_empty_array() -> None:
    """The two forms of an empty tree."""
    # Given no Work
    found = build_hierarchy([], "nesting")

    # When it is rendered in each form
    text = render_list(found, as_json=False)
    array = render_list(found, as_json=True)

    # Then the text is empty and the JSON is `[]`
    assert (text, array) == ("", "[]\n")


class _Settings:
    """A `Settings` that gives a config under the default Works directory."""

    def __init__(self, hierarchy: HierarchyMode) -> None:
        """Keep the mode.

        Args:
            hierarchy: The hierarchy mode of the config.
        """
        self._config = Config(works=Works(hierarchy=hierarchy))

    def load(self) -> Config:
        """Give the config.

        Returns:
            The settings.
        """
        return self._config


class _NoCatalog:
    """A catalog that is never asked."""

    def find(self, name: str) -> None:
        """Fail, because the listing needs no template.

        Args:
            name: The name asked for.

        Raises:
            AssertionError: Always.
        """
        raise AssertionError(name)

    def is_rejected(self, name: str) -> bool:
        """Fail, because the listing needs no template.

        Args:
            name: The name asked for.

        Raises:
            AssertionError: Always.
        """
        raise AssertionError(name)


def _marked(block: str) -> str:
    """Write a file with a metadata block.

    Args:
        block: The lines of the block.

    Returns:
        The text of the file.
    """
    return f"<!-- wio\n{block}\n-->\n\n# Title\n"


def _list(
    files: Mapping[str, str],
    *,
    as_json: bool = False,
    mode: Literal["flat", "nesting"] = "flat",
) -> tuple[int, str]:
    """Run the command on files under the Works directory.

    Args:
        files: The files, by path relative to the Works directory.
        as_json: Whether `--json` is given.
        mode: The hierarchy mode.

    Returns:
        The exit code and what was written to standard output.
    """
    disk = MemoryFileSystem({ROOT / BASE / name: text for name, text in files.items()})
    services = Services(_Settings(mode), FakeRepository(), disk, _NoCatalog())
    stdio = FakeStdio()
    code = run_list(services, Namespace(json=as_json), stdio)
    return code, cast("io.StringIO", stdio.stdout).getvalue()


@pytest.mark.parametrize("form", ["text", "json"])
def test_an_incomplete_tree_is_refused_with_its_errors_and_the_hint(form: str) -> None:
    """A shared id and a Work left out refuse the listing and say where to look."""
    # Given a tree with two Works that share an id, and another with a Work
    # whose block has no id
    shared = {
        "s/README.md": _marked('id = "a7b2c4"'),
        "t/README.md": _marked('id = "a7b2c4"'),
    }
    left_out = {"a/README.md": _marked('id = "k3m9xq"'), "b/README.md": _marked("")}

    # When the command runs on each
    refusals = []
    for files in (shared, left_out):
        with pytest.raises(ContractsError) as raised:
            _list(files, as_json=form == "json")
        refusals.append(raised.value)

    # Then each carries the errors, which its message renders one to a line, and
    # ends with the hint
    assert [e.diagnostics[0].where for e in refusals] == [
        f"{BASE}/s/README.md, {BASE}/t/README.md",
        f"{BASE}/b/README.md",
    ]
    for error in refusals:
        lines = str(error).splitlines()
        assert lines[0].startswith("error: ")
        assert lines[-1] == "`wio contracts check` shows every problem."
        assert len(lines) == len(error.diagnostics) + 1


def test_errors_that_leave_the_tree_complete_do_not_stop_the_listing() -> None:
    """An undeclared root, a wrong type, an unknown dependency and a cycle list."""
    # Given Works with each of those
    files = {
        "a/README.md": _marked('id = "k3m9xq"\nroots = ["nosuch"]'),
        "b/README.md": _marked('id = "n5p7qr"\nroots = "api"'),
        "c/README.md": _marked('id = "a7b2c4"\ndepends_on = ["y4k2mq", "zzzzzz"]'),
        "d/README.md": _marked('id = "y4k2mq"\ndepends_on = ["a7b2c4"]'),
    }

    # When the command runs, as text and with `--json`
    text_code, text = _list(files)
    json_code, array = _list(files, as_json=True)

    # Then every Work is written and the exit code is 0
    assert (text_code, json_code) == (0, 0)
    assert [obj["id"] for obj in json.loads(array)] == [
        "k3m9xq",
        "n5p7qr",
        "a7b2c4",
        "y4k2mq",
    ]
    assert "roots: nosuch" in text
    assert "after: zzzzzz (not found)" in text
    assert "roots:" not in text.split("n5p7qr")[1].split("a7b2c4")[0]


def test_the_hierarchy_mode_of_the_config_decides_the_indent() -> None:
    """The same files are nested under `nesting` and flat under `flat`."""
    # Given a parent and a child, and a config for each mode
    files = {
        "p/README.md": _marked('id = "p1"'),
        "p/c/README.md": _marked('id = "c1"'),
    }

    # When the command runs under each mode
    _, nested = _list(files, mode="nesting")
    _, flat = _list(files, mode="flat")

    # Then the child is indented under `nesting` and is not under `flat`
    assert [line for line in nested.splitlines() if "  c1" in line] == ["  c1  Title"]
    assert [line for line in flat.splitlines() if "c1" in line] == ["c1  Title"]


def test_the_errors_of_a_refusal_are_in_the_order_that_discovery_gives() -> None:
    """A file comes before an error that names several files, as in `check`."""
    # Given a shared id whose files sort before a Work that is left out
    files = {
        "s/README.md": _marked('id = "a7b2c4"'),
        "t/README.md": _marked('id = "a7b2c4"'),
        "z/README.md": _marked(""),
    }

    # When the command refuses
    with pytest.raises(ContractsError) as raised:
        _list(files)

    # Then the file that was left out is first, and the shared id follows
    assert [d.where for d in raised.value.diagnostics] == [
        f"{BASE}/z/README.md",
        f"{BASE}/s/README.md, {BASE}/t/README.md",
    ]
    assert str(raised.value).splitlines()[0].startswith(f"error: {BASE}/z/")


def test_several_roots_are_written_as_given_and_joined_by_a_comma_and_a_space() -> None:
    """The roots keep their order and repeats, and a root may hold a comma."""
    # Given a Work with several roots, one repeated and one with a comma
    work = _work("a/README.md", "a1", "Title", roots=("web", "api", "web", "a, b"))

    # When it is rendered as text and as JSON
    text = _text("flat", work).splitlines()
    [obj] = _array("flat", work)

    # Then the line joins them as written, and the JSON keeps them as a list
    assert text[2] == "    roots: web, api, web, a, b"
    assert obj["roots"] == ["web", "api", "web", "a, b"]


def test_a_title_is_written_as_it_is_whatever_it_holds() -> None:
    """Brackets, commas, quotes, accents and a long text are neither cut nor
    escaped in the text, and are escaped as `json.dumps` escapes them."""
    # Given titles with brackets, quotes, accents, a backslash and a long text
    titles = [
        "[draft] Read config.toml, then `write`",
        'He said "no" \\ and left',
        "Łódź café — naïve",
        "x" * 300,
    ]
    works = [
        _work(f"{n}/README.md", f"id{n}", title, "feature.leaf")
        for n, title in enumerate(titles)
    ]

    # When the Works are rendered as text and as JSON
    lines = _text("flat", *works).splitlines()
    array = _array("flat", *works)
    raw = render_list(build_hierarchy(works, "flat"), as_json=True)

    # Then each first line holds its title whole, and the JSON round-trips
    firsts = [line for line in lines if not line.startswith(" ")]
    assert firsts == [
        f"id{n}  {title}  [feature.leaf]" for n, title in enumerate(titles)
    ]
    assert [obj["title"] for obj in array] == titles
    assert raw == json.dumps(array) + "\n"
    assert "\\u0141" in raw


def test_a_path_with_spaces_colons_and_accents_is_written_as_it_is() -> None:
    """The path is not quoted or escaped, and keeps its `/`."""
    # Given a Work whose directory holds a space, a colon, an accent and a dot
    work = _work("my work: ł/v1.2 draft/README.md", "a1", "Title")

    # When it is rendered as text and as JSON
    text = _text("flat", work).splitlines()
    [obj] = _array("flat", work)

    # Then the path line and the field hold it as written
    assert text[1] == f"    {BASE}/my work: ł/v1.2 draft/README.md"
    assert obj["path"] == f"{BASE}/my work: ł/v1.2 draft/README.md"


def test_a_template_with_brackets_or_spaces_is_written_between_brackets() -> None:
    """The template is the text between the brackets, whatever it holds."""
    # Given a Work whose template name holds a bracket and a space
    work = _work("a/README.md", "a1", "Title", "odd [name] x")

    # When it is rendered as text
    first = _text("flat", work).splitlines()[0]

    # Then the brackets enclose it as it is
    assert first == "a1  Title  [odd [name] x]"


def test_a_dependency_on_a_work_with_an_odd_title_shows_the_title_whole() -> None:
    """The `after:` line holds the title as it is."""
    # Given a Work that lists a Work whose title has brackets and a comma
    works = [
        _work("a/README.md", "a1", depends_on=("b1",)),
        _work("b/README.md", "b1", "[x], y"),
    ]

    # When the Works are rendered as text
    text = _text("flat", *works)

    # Then the line holds the id and the title
    assert "    after: b1 [x], y" in text.splitlines()
