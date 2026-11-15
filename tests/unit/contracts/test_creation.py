# SPDX-License-Identifier: Apache-2.0
"""Tests of planning and reporting a new Work."""

import json
from pathlib import Path
from typing import TYPE_CHECKING, cast
from unittest.mock import Mock

import pytest

from tests.unit.fakes import ROOT, FakeEntropy, MemoryFileSystem
from wio.contracts.creation import NewArguments, plan_work, render_report
from wio.contracts.discovery import discover_works
from wio.contracts.errors import ContractsError
from wio.contracts.location import NameArguments, RandomIds
from wio.formats import read_metadata_block
from wio.models.config import Config, Root, Templates, Works
from wio.models.frozen import freeze
from wio.models.template import Template

if TYPE_CHECKING:
    from wio.contracts.ports import TemplateCatalog


def _setup() -> tuple[Config, MemoryFileSystem, TemplateCatalog]:
    """Build a project with a kind and one template.

    Returns:
        The settings, in-memory files and catalog.
    """
    config = Config(
        works=Works(hierarchy="nesting"),
        templates=Templates(kinds=freeze({"feature": "feature.draft"})),
        roots=freeze({"wio": Root(paths=("src",))}),
    )
    path = Path("templates/feature.draft.md")
    files = MemoryFileSystem(
        {
            ROOT / path: '<!-- wio\nkind = "feature"\n[contract]\n'
            "roots = []\ndepends_on = []\n-->\n\n# Old\n\n## Purpose\n"
        }
    )
    catalog = Mock()
    catalog.is_rejected.return_value = False
    catalog.find.return_value = Template(
        "feature.draft", "feature", None, None, path, entry=True
    )
    return config, files, cast("TemplateCatalog", catalog)


def test_plan_template_and_report() -> None:
    """The requested id, roots, title and report come from the composed plan."""
    # Given a kind with an entry template and a deterministic id source
    config, files, catalog = _setup()
    found = discover_works(ROOT, config.works, files)
    args = NewArguments(
        "feature",
        None,
        NameArguments(None, " Read config ", None, None),
        ("wio", "wio"),
    )

    # When a Work is planned and reported
    work = plan_work(
        args, config, found, catalog, files, ROOT, RandomIds(FakeEntropy())
    )
    report = json.loads(render_report(work, as_json=True))

    # Then the skeleton has the requested data and the report names the result
    block = read_metadata_block(work.text)
    assert block is not None
    assert block.data == {
        "id": "k3m9xq",
        "template": "feature.draft",
        "roots": ["wio"],
        "depends_on": [],
    }
    assert block.body == "\n# Read config\n\n## Purpose\n"
    assert report == {
        "id": "k3m9xq",
        "title": "Read config",
        "path": ".agents/wio/works/read-config/README.md",
        "template": "feature.draft",
        "parent": None,
    }


@pytest.mark.parametrize(
    ("kind", "roots", "title", "expected"),
    [
        ("missing", ("bad",), " ", "kind"),
        ("feature", ("bad",), " ", "root"),
        ("feature", (), " ", "title"),
    ],
)
def test_mistakes_are_reported_in_order(
    kind: str, roots: tuple[str, ...], title: str, expected: str
) -> None:
    """A prior mistake is reported before later mistakes."""
    # Given a project and arguments with more than one mistake
    config, files, catalog = _setup()
    found = discover_works(ROOT, config.works, files)
    args = NewArguments(kind, None, NameArguments("a", title, None, None), roots)

    # When the Work is planned
    with pytest.raises(ContractsError) as error:
        plan_work(args, config, found, catalog, files, ROOT, RandomIds(FakeEntropy()))

    # Then the first mistake is named
    assert expected in str(error.value).lower()


def test_bare_contract_and_human_report() -> None:
    """A bare contract requires no kinds or templates."""
    # Given a project without kinds
    config = Config(works=Works(hierarchy="nesting"))
    files = MemoryFileSystem()
    found = discover_works(ROOT, config.works, files)
    args = NewArguments(None, None, NameArguments("note", None, None, None), ())

    # When a bare Work is planned
    work = plan_work(
        args,
        config,
        found,
        cast("TemplateCatalog", Mock()),
        files,
        ROOT,
        RandomIds(FakeEntropy()),
    )

    # Then it has the id, title and human report
    assert work.text == '<!-- wio\nid = "k3m9xq"\n-->\n\n# Title\n'
    assert (
        render_report(work, as_json=False)
        == "Created Work k3m9xq  Title\n  .agents/wio/works/note/README.md\n"
    )


def test_the_shared_block_editor_receives_id_and_roots(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """AC-7: the planner writes the block through the one editor."""
    # Given a recording stand-in for the block editor
    config, files, catalog = _setup()
    found = discover_works(ROOT, config.works, files)
    args = NewArguments(
        "feature", None, NameArguments("a", "Title", None, None), ("wio",)
    )
    from wio.contracts import creation

    real = creation.set_block_keys
    editor = Mock(side_effect=real)
    monkeypatch.setattr(creation, "set_block_keys", editor)

    # When the Work is planned
    work = plan_work(
        args, config, found, catalog, files, ROOT, RandomIds(FakeEntropy())
    )

    # Then the editor receives the id and roots, and its result supplies the block
    editor.assert_called_once()
    assert editor.call_args.args[1] == {"id": "k3m9xq", "roots": ["wio"]}
    block = read_metadata_block(work.text)
    assert block is not None
    assert block.data["roots"] == ["wio"]


@pytest.mark.parametrize("problem", ["missing", "rejected", "wrong_kind"])
def test_template_problems_are_refused(problem: str) -> None:
    """AC-2 and AC-5: unusable templates are refused before placement."""
    # Given a template catalog that reports the requested problem
    config, files, catalog = _setup()
    stub = cast("Mock", catalog)
    if problem == "missing":
        stub.find.return_value = None
    elif problem == "rejected":
        stub.is_rejected.return_value = True
    else:
        stub.find.return_value = Template(
            "other.note", "other", None, None, Path("other"), entry=False
        )
    args = NewArguments(
        "feature", "other.note", NameArguments("a", None, None, None), ()
    )
    found = discover_works(ROOT, config.works, files)

    # When the Work is planned
    with pytest.raises(ContractsError) as error:
        plan_work(args, config, found, catalog, files, ROOT, RandomIds(FakeEntropy()))

    # Then the problem is named and the file system is unchanged
    assert {
        "missing": "templates list",
        "rejected": "templates check",
        "wrong_kind": "other",
    }[problem] in str(error.value)
    assert len(files.files) == 1


def test_a_title_is_inserted_in_a_crlf_template_without_a_heading() -> None:
    """AC-4: a missing title is inserted using the template's line ending."""
    # Given a CRLF template without a level-one heading
    config, files, catalog = _setup()
    path = ROOT / "templates/feature.draft.md"
    files.files[path] = (
        '<!-- wio\r\nkind = "feature"\r\n[contract]\r\n'
        "depends_on = []\r\n-->\r\n\r\n## Purpose\r\n"
    )
    args = NewArguments(
        "feature", None, NameArguments("a", "Mine", None, None), ("wio",)
    )
    found = discover_works(ROOT, config.works, files)

    # When the Work is planned
    work = plan_work(
        args, config, found, catalog, files, ROOT, RandomIds(FakeEntropy())
    )

    # Then its title is inserted and every line ending is CRLF
    assert "\r\n\r\n# Mine\r\n\r\n## Purpose\r\n" in work.text
    assert "\n" not in work.text.replace("\r\n", "")


@pytest.mark.parametrize("title", [" ", "line one\nline two", "line one\rline two"])
def test_invalid_titles_are_refused_before_placement(title: str) -> None:
    """AC-5: blank and multiline titles have the title error."""
    # Given a title that is blank or contains a line ending
    config = Config()
    files = MemoryFileSystem()
    found = discover_works(ROOT, config.works, files)
    args = NewArguments(None, None, NameArguments(None, title, None, None), ())

    # When the Work is planned
    with pytest.raises(ContractsError, match="The title must be one non-blank line"):
        plan_work(
            args,
            config,
            found,
            cast("TemplateCatalog", Mock()),
            files,
            ROOT,
            RandomIds(FakeEntropy()),
        )

    # Then no file is written
    assert not files.files


def test_a_missing_entry_template_points_to_check() -> None:
    """AC-5: a missing entry template gives the check command as its hint."""
    # Given a declared kind whose entry template is not found
    config, files, catalog = _setup()
    cast("Mock", catalog).find.return_value = None
    args = NewArguments("feature", None, NameArguments("a", None, None, None), ())
    found = discover_works(ROOT, config.works, files)

    # When the Work is planned
    with pytest.raises(ContractsError, match="wio templates check"):
        plan_work(args, config, found, catalog, files, ROOT, RandomIds(FakeEntropy()))

    # Then the template is the only file
    assert len(files.files) == 1


def test_title_after_unterminated_whitespace_body() -> None:
    """A title inserted after an unterminated blank line is a real heading."""
    # Given a template with an unterminated whitespace-only body
    config, files, catalog = _setup()
    files.files[ROOT / "templates/feature.draft.md"] = (
        '<!-- wio\nkind = "feature"\n[contract]\n-->\n\n    '
    )
    found = discover_works(ROOT, config.works, files)
    args = NewArguments("feature", None, NameArguments("a", "Mine", None, None), ())

    # When a Work is planned with a title
    work = plan_work(
        args, config, found, catalog, files, ROOT, RandomIds(FakeEntropy())
    )

    # Then the heading is recognized and the whitespace is retained
    assert work.title == "Mine"
    assert work.text.endswith("    \n# Mine")


@pytest.mark.parametrize("suffix", ["", "\n", "\n\n", "\r\n\r\n"])
def test_title_in_empty_body_keeps_final_line_endings(suffix: str) -> None:
    """A title added after a blank body keeps the skeleton's final endings."""
    # Given a contract with a whitespace-only body and varied final endings
    from wio.contracts.creation import _set_title

    text = "<!-- wio\n-->\n    " + suffix

    # When a title is inserted
    result = _set_title(text, "Mine")

    # Then the title has the same final endings as the original text
    assert result.endswith("# Mine" + suffix)


def test_title_is_trimmed_before_checking_for_line_breaks() -> None:
    """Whitespace line breaks at the ends do not make a trimmed title multiline."""
    # Given a title with line breaks surrounding its only nonblank line
    config = Config(works=Works(hierarchy="nesting"))
    files = MemoryFileSystem()
    found = discover_works(ROOT, config.works, files)
    args = NewArguments(None, None, NameArguments("note", "\n Mine \n", None, None), ())

    # When the Work is planned
    work = plan_work(
        args,
        config,
        found,
        cast("TemplateCatalog", Mock()),
        files,
        ROOT,
        RandomIds(FakeEntropy()),
    )

    # Then the new heading contains the trimmed title
    assert work.title == "Mine"
    assert "# Mine\n" in work.text


def test_replacing_title_keeps_inline_authoring_comments() -> None:
    """A title replacement retains authoring comments on the heading."""
    # Given a template whose heading has an authoring comment
    config, files, catalog = _setup()
    files.files[ROOT / "templates/feature.draft.md"] = (
        '<!-- wio\nkind = "feature"\n[contract]\n-->\n\n'
        "# Old <!-- Keep this note. -->\n"
    )
    found = discover_works(ROOT, config.works, files)
    args = NewArguments("feature", None, NameArguments("a", "New", None, None), ())

    # When the Work is planned with a new title
    work = plan_work(
        args, config, found, catalog, files, ROOT, RandomIds(FakeEntropy())
    )

    # Then the heading changes and its authoring comment remains
    assert "# New <!-- Keep this note. -->\n" in work.text


@pytest.mark.parametrize("old", ["# Old `<!--`\n", "# Old \\<!-- text -->\n"])
def test_title_replacement_does_not_keep_comment_like_text(old: str) -> None:
    """Comment-like code and escaped text are replaced as part of the title."""
    # Given a heading containing comment-like text that is not an HTML comment
    config, files, catalog = _setup()
    files.files[ROOT / "templates/feature.draft.md"] = (
        '<!-- wio\nkind = "feature"\n[contract]\n-->\n\n' + old
    )
    found = discover_works(ROOT, config.works, files)
    args = NewArguments("feature", None, NameArguments("a", "New", None, None), ())

    # When a new title is set
    work = plan_work(
        args, config, found, catalog, files, ROOT, RandomIds(FakeEntropy())
    )

    # Then the heading and reported title contain only the new title
    assert work.text.endswith("# New\n")
    assert work.title == "New"


@pytest.mark.parametrize("title", ["New #", "#", "New ##", "New#"])
@pytest.mark.parametrize("has_heading", [True, False])
def test_title_ending_in_hash_is_not_taken_as_heading_markup(
    title: str, *, has_heading: bool
) -> None:
    """A requested title ending in hashes remains the heading and report title."""
    # Given a template with or without a level-one heading
    config, files, catalog = _setup()
    if not has_heading:
        files.files[ROOT / "templates/feature.draft.md"] = (
            '<!-- wio\nkind = "feature"\n[contract]\n-->\n\n## Purpose\n'
        )
    found = discover_works(ROOT, config.works, files)
    args = NewArguments("feature", None, NameArguments("a", title, None, None), ())

    # When the Work is planned with the requested title
    work = plan_work(
        args, config, found, catalog, files, ROOT, RandomIds(FakeEntropy())
    )

    # Then reading and reporting the heading retain the complete title
    assert work.title == title
    assert f"Created Work k3m9xq  {title}\n" in render_report(work, as_json=False)


def test_title_replacement_keeps_a_multiline_authoring_comment() -> None:
    """An authoring comment begun on the heading keeps its opening and body."""
    # Given a heading that starts a multiline authoring comment
    from wio.contracts.creation import _set_title

    text = "<!-- wio\n-->\n\n# Old <!-- multi\ncontinued -->\n\n## Body\n"

    # When the heading is replaced
    result = _set_title(text, "New")

    # Then the comment and the remaining body are preserved
    assert result == "<!-- wio\n-->\n\n# New <!-- multi\ncontinued -->\n\n## Body\n"


@pytest.mark.parametrize("character", ["\x0c", "\x85", "\u2028"])
def test_title_replacement_counts_only_markdown_line_endings(character: str) -> None:
    """A non-newline character in an earlier body line cannot shift the heading."""
    # Given a body with a non-newline separator before a level-one heading
    from wio.contracts.creation import _set_title

    text = f"<!-- wio\n-->\nbefore{character}inside\n# Old\n## Purpose\n"

    # When the title is replaced
    result = _set_title(text, "New")

    # Then the earlier line is unchanged and only the heading is replaced
    assert result == f"<!-- wio\n-->\nbefore{character}inside\n# New\n## Purpose\n"
