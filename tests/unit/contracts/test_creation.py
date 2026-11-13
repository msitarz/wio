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
    assert "    \n# Mine\n" in work.text
