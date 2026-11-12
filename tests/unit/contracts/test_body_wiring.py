# SPDX-License-Identifier: Apache-2.0
"""Tests of how the check of the body is composed from its leaves."""

from pathlib import Path
from typing import TYPE_CHECKING
from unittest.mock import Mock

import pytest

from tests.unit.contracts.helpers import work_with_id
from tests.unit.fakes import ROOT, MemoryFileSystem
from wio.contracts import body as module
from wio.formats import read_metadata_block
from wio.models.diagnostics import Diagnostic
from wio.models.frozen import freeze
from wio.models.heading import Heading
from wio.models.template import Template
from wio.models.works import Work

if TYPE_CHECKING:
    from wio.models.block import MetadataBlock

TEMPLATE = Template("t", "feature", None, None, Path("templates/t.md"), entry=False)


def _block(body: str = "# Title\n\n## Goals\n") -> MetadataBlock:
    """Read the block of a contract.

    Args:
        body: The text after the block.

    Returns:
        The block.
    """
    block = read_metadata_block(f'<!-- wio\nid = "a1"\n-->\n\n{body}')
    assert block is not None
    return block


def _following(work: Work, template: str | None) -> Work:
    """Make a Work that names a template.

    Args:
        work: A Work.
        template: The template it names, or `None` for none.

    Returns:
        The Work with that `template`.
    """
    return Work(
        work.id,
        work.title,
        work.path,
        template,
        work.roots,
        work.depends_on,
        freeze({}),
    )


def _leaves(monkeypatch: pytest.MonkeyPatch, source: object) -> dict[str, Mock]:
    """Replace the leaves of the check with mocks that record their calls.

    Args:
        monkeypatch: The fixture.
        source: What reading a template gives.

    Returns:
        The mocks by name.
    """
    mocks = {
        "_read_template": Mock(return_value=source),
        "_level_two": Mock(return_value=module._Headings({}, [])),  # noqa: SLF001
        "_directives": Mock(return_value=module._Directives({}, [])),  # noqa: SLF001
        "_repeat_warnings": Mock(return_value=[]),
        "_against_template": Mock(return_value=[]),
        "_item_errors": Mock(return_value=[]),
    }
    for name, mock in mocks.items():
        monkeypatch.setattr(module, name, mock)
    return mocks


def test_a_contract_that_names_a_template_that_cannot_be_used_gets_nothing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Missing, rejected and unreadable templates give no diagnostic."""
    # Given leaves that must not run, a Work that names a template that the
    # catalog did not give, and one whose template cannot be read
    mocks = _leaves(monkeypatch, None)
    checker = module.BodyChecker(ROOT, MemoryFileSystem())
    work = _following(work_with_id("a1"), "t")

    # When the bodies are checked
    missing = checker.check(work, _block(), None)
    unreadable = checker.check(work, _block(), TEMPLATE)

    # Then nothing is reported and no section was looked at
    assert (missing, unreadable) == ([], [])
    mocks["_level_two"].assert_not_called()


def test_a_template_is_read_once_and_a_failed_read_is_remembered(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The second contract that follows a template does not read it again."""
    # Given a checker and three contracts that follow one template, and three
    # that follow one that cannot be read
    good = module._Source("t", {})  # noqa: SLF001
    mocks = _leaves(monkeypatch, good)
    checker = module.BodyChecker(ROOT, MemoryFileSystem())
    work = _following(work_with_id("a1"), "t")

    # When each is checked
    for _ in range(3):
        checker.check(work, _block(), TEMPLATE)
    mocks["_read_template"].return_value = None
    other = Template("u", "feature", None, None, Path("templates/u.md"), entry=False)
    for _ in range(3):
        checker.check(_following(work, "u"), _block(), other)

    # Then each template's file was read once
    assert [c.args[0].name for c in mocks["_read_template"].call_args_list] == [
        "t",
        "u",
    ]


def test_a_contract_with_no_template_is_checked_by_its_own_headings(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """With no template there is no source, and the leaves get `None`."""
    # Given leaves and a Work that names no template
    mocks = _leaves(monkeypatch, None)
    checker = module.BodyChecker(ROOT, MemoryFileSystem())
    work = work_with_id("a1")

    # When the body is checked
    checker.check(work, _block(), None)

    # Then no template was read, and the leaves were given no source
    mocks["_read_template"].assert_not_called()
    assert mocks["_directives"].call_args.args[3] is None
    assert mocks["_against_template"].call_args.args[3] is None


def test_the_findings_of_the_leaves_come_together_in_one_list(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Each leaf contributes, and the title warning is the code's own."""
    # Given leaves that each give one finding and a Work with no title
    mocks = _leaves(monkeypatch, module._Source("t", {}))  # noqa: SLF001
    for name in ("_repeat_warnings", "_against_template", "_item_errors"):
        mocks[name].return_value = [Diagnostic("note", "a", name)]
    mocks["_directives"].return_value = module._Directives(  # noqa: SLF001
        {}, [Diagnostic("note", "a", "directives")]
    )
    checker = module.BodyChecker(ROOT, MemoryFileSystem())

    # When the body is checked
    found = checker.check(_following(work_with_id("a1"), "t"), _block(), TEMPLATE)

    # Then all five are there, the title warning among them
    assert sorted(d.message for d in found) == [
        "The contract has no title",
        "_against_template",
        "_item_errors",
        "_repeat_warnings",
        "directives",
    ]


@pytest.mark.parametrize(
    ("raw", "text"),
    [
        ("## Goals", "Goals"),
        ("##  Goals  ", "Goals"),
        ("## Goals <!-- wio: required -->", "Goals"),
        ("## Goals <!--   wio:   mandatory -->", "Goals"),
        ("## Goals <!-- wio: required", "Goals"),
        ("## Goals ##", "Goals"),
        ("## Goals <!-- note -->", "Goals <!-- note -->"),
    ],
)
def test_the_text_of_a_heading_is_what_comes_before_its_directive_list(
    raw: str, text: str
) -> None:
    """A list that the parser refuses has a text too."""
    # Given a heading line
    heading = Heading(2, raw, raw, 5)

    # When its text is taken
    found = module._text_of(heading)  # noqa: SLF001

    # Then it is the text before the list, without marks and whitespace
    assert found == text


def test_a_repeated_section_is_a_warning_at_its_line_and_a_missing_title_too() -> None:
    """The two warnings that need no template."""
    # Given a repeat of `Goals` and a Work with no title
    repeat = Heading(
        2, "## Goals <!-- wio: required -->", "## Goals <!-- wio: required -->", 9
    )
    headings = module._Headings({}, [(repeat, 3)])  # noqa: SLF001

    # When they are judged
    repeated = module._repeat_warnings("c/README.md", headings)  # noqa: SLF001
    untitled = module._title_warning(work_with_id("a1"))  # noqa: SLF001

    # Then each is a warning at its place
    assert [(d.severity, d.where, d.message) for d in repeated] == [
        (
            "warning",
            "c/README.md:9",
            "The section `Goals` is repeated; the first one counts",
        )
    ]
    assert [(d.severity, d.message) for d in untitled] == [
        ("warning", "The contract has no title")
    ]


def test_the_check_of_the_works_gives_each_body_to_the_checker_but_not_a_wrong_template(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A Work whose `template` discovery reported is not checked by its headings."""
    # Given Works of which one names no template and one has `template = 1`, and
    # a checker that records what it is given
    from wio.contracts import checking
    from wio.models.config import Config

    check = Mock(return_value=[])
    monkeypatch.setattr(module.BodyChecker, "check", check)
    base = ROOT / ".agents/wio/works"
    disk = MemoryFileSystem(
        {
            base / "a/README.md": '<!-- wio\nid = "a1"\n-->\n\n# A\n',
            base / "b/README.md": '<!-- wio\nid = "b1"\ntemplate = 1\n-->\n\n# B\n',
        }
    )

    # When the Works are checked
    checking.check_works(ROOT, Config(), disk, Mock(find=Mock(return_value=None)))

    # Then only the first was given to the body checker, with its block and no
    # template
    assert [c.args[0].id for c in check.call_args_list] == ["a1"]
    assert check.call_args.args[2] is None
    assert check.call_args.args[1].body.startswith("\n# A")


def test_each_directive_list_of_a_contract_that_follows_a_template_is_ignored() -> None:
    """One warning for each list, on a heading of any level and in any syntax."""
    # Given headings with a list, a list that the parser refuses, two lists on
    # one heading, a plain note and none
    raws = [
        "# Title <!-- wio: required -->",
        "## Bad <!-- wio: mandatory -->",
        "### Deep <!-- wio: required --> <!-- wio: items>=1 -->",
        "## Note <!-- just a note -->",
        "## Plain",
    ]
    outline = [Heading(2, raw, raw, 10 + n) for n, raw in enumerate(raws)]

    # When they are judged against a template `t`
    found = module._ignored_lists("c/README.md", outline, "t")  # noqa: SLF001

    # Then each list is a warning at its heading's line
    assert [(d.severity, d.where) for d in found] == [
        ("warning", "c/README.md:10"),
        ("warning", "c/README.md:11"),
        ("warning", "c/README.md:12"),
        ("warning", "c/README.md:12"),
    ]
    assert found[0].message == (
        "The directive list is ignored because the contract follows the template `t`"
    )
