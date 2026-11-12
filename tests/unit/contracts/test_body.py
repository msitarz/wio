# SPDX-License-Identifier: Apache-2.0
"""Tests of the check of the body of a contract."""

from pathlib import Path
from typing import TYPE_CHECKING, override

import pytest

from tests.unit.fakes import ROOT, MemoryFileSystem
from wio.contracts import body as module
from wio.contracts.body import BodyChecker
from wio.formats import read_metadata_block
from wio.models.frozen import freeze
from wio.models.heading import Heading
from wio.models.template import Template
from wio.models.works import Work

if TYPE_CHECKING:
    from collections.abc import Sequence

    from wio.models.block import MetadataBlock

FILE = "c/README.md"
BAD_BODY = "# Title\n\n## Bad <!-- wio: mandatory -->\n"
"""A body that is reported in the mode of a contract with no template."""
STRAY_CLOSE = (
    "The section `Constraint` is not in the template `t`. Did you mean `Constraints`?"
)
TEMPLATE_FILE = "templates/t.md"


class _Counting(MemoryFileSystem):
    """A file system that counts the reads of each file."""

    def __init__(self, files: dict[Path, str]) -> None:
        """Keep the files and start counting.

        Args:
            files: The files, by path.
        """
        super().__init__(files)
        self.reads: dict[Path, int] = {}

    @override
    def read_text(self, path: Path) -> str:
        """Count the read and give the text.

        Args:
            path: The file.

        Returns:
            Its text.
        """
        self.reads[path] = self.reads.get(path, 0) + 1
        return super().read_text(path)


def _template_text(body: str) -> str:
    """Write a template's file.

    Args:
        body: The text after its block.

    Returns:
        The file.
    """
    return f'<!-- wio\nkind = "feature"\n-->\n{body}'


def _contract(body: str, title: str | None = "Title") -> tuple[Work, MetadataBlock]:
    """Write a contract and read it, as the check of the Works does.

    Args:
        body: The text after its block, which begins on line 4.
        title: The title that discovery found.

    Returns:
        The Work, which names a template when asked to, and its block.
    """
    text = f'<!-- wio\nid = "a1"\n-->\n{body}'
    block = read_metadata_block(text)
    assert block is not None
    work = Work("a1", title, Path(FILE), None, (), (), freeze({}))
    return work, block


def _named(work: Work, template: str) -> Work:
    """Make a Work that names a template.

    Args:
        work: A Work.
        template: The template's name.

    Returns:
        The Work with that `template`.
    """
    return Work(work.id, work.title, work.path, template, (), (), freeze({}))


def _run(
    body: str,
    template: str | None = None,
    title: str | None = "Title",
) -> list[tuple[str, str, str]]:
    """Check one contract against a template, or against its own headings.

    Args:
        body: The contract's body, from line 4.
        template: The template's body, or `None` for a contract that names none.
        title: The title that discovery found.

    Returns:
        The severity, the place and the message of each finding, in order.
    """
    work, block = _contract(body, title)
    disk = MemoryFileSystem({ROOT / TEMPLATE_FILE: _template_text(template or "")})
    checker = BodyChecker(ROOT, disk)
    if template is None:
        found = checker.check(work, block, None)
    else:
        given = Template("t", "feature", None, None, Path(TEMPLATE_FILE), entry=False)
        found = checker.check(_named(work, "t"), block, given)
    return sorted((d.severity, d.where, d.message) for d in found)


def test_a_required_section_that_is_missing_is_an_error() -> None:
    """A section is matched by its text, and a missing required one is an error."""
    # Given a template that requires `Purpose` and `Goals` and has `Notes`, and a
    # contract with `##  purpose` only
    template = (
        "\n# T\n\n## Purpose <!-- wio: required -->\n\n"
        "## Goals <!-- wio: required -->\n\n## Notes\n"
    )

    # When the body is checked
    found = _run("\n# Title\n\n##  purpose\n", template)

    # Then there is one error at the file for `Goals`, none for `Purpose`, which
    # matches in another case, and none for `Notes`
    assert found == [
        ("error", FILE, "The section `Goals` is required by the template `t`")
    ]


def test_matching_ignores_only_case_whitespace_and_a_trailing_list() -> None:
    """Nothing else is normalized."""
    # Given a template that requires `Acceptance criteria`
    template = "\n# T\n\n## Acceptance criteria <!-- wio: required -->\n"

    # When contracts with near misses and with each allowed difference are checked
    punctuation = _run("\n# T\n\n## Acceptance criteria:\n", template)
    inner_space = _run("\n# T\n\n## Acceptance  criteria\n", template)
    allowed = _run("\n# T\n\n##    ACCEPTANCE criteria   ##\n", template)

    # Then only the allowed one matches
    assert [m for _, _, m in punctuation if "required" in m] != []
    assert [m for _, _, m in inner_space if "required" in m] != []
    assert [m for _, _, m in allowed if "required" in m] == []


def test_the_first_of_two_template_headings_is_the_section() -> None:
    """The first heading's directives apply, and a repeat adds nothing."""
    # Given a template that has `Goals` twice, the first not required
    template = "\n# T\n\n## Goals\n\n## goals <!-- wio: required -->\n"

    # When a contract with no `Goals` is checked
    found = _run("\n# Title\n", template)

    # Then nothing is required
    assert found == []


def test_a_template_section_that_inherits_and_is_required_is_required() -> None:
    """Inheritance does not lift a requirement."""
    # Given a template section that is `inherit` and `required`
    template = "\n# T\n\n## Constraints <!-- wio: inherit, required -->\n"

    # When a contract without it is checked
    found = _run("\n# Title\n", template)

    # Then the section is required
    assert [m for _, _, m in found] == [
        "The section `Constraints` is required by the template `t`"
    ]


def test_items_and_their_ids_are_judged_as_the_items_leaf_judges_them() -> None:
    """The count and the ids come from the template's directives."""
    # Given a template with `items>=1` and a `pattern`, and a contract whose Goals
    # holds an authoring comment and whose criteria repeat an id and lack one
    template = (
        "\n# T\n\n## Goals <!-- wio: items>=1 -->\n\n"
        "## Acceptance criteria <!-- wio: pattern=AC-\\d+ -->\n"
    )
    body = (
        "# Title\n\n## Goals\n\n<!-- Write the goals. -->\n\n"
        "## Acceptance criteria\n\n### **AC-1** First\n\n"
        "### **AC-1** Second\n\n### Third\n"
    )

    # When the body is checked
    found = _run(body, template)

    # Then there are an error at `## Goals`, one at the first id that names the
    # line of the second, and one at the item with no id
    assert [(s, w) for s, w, _ in found] == [
        ("error", f"{FILE}:12"),
        ("error", f"{FILE}:16"),
        ("error", f"{FILE}:6"),
    ]
    assert "line 14" in found[0][2]


def test_a_misspelled_section_is_a_warning_with_the_closest_section() -> None:
    """A stray `##` heading is told, deeper headings are free."""
    # Given a template with `Constraints` and a contract with `Constraint`, `Zzz`
    # and a deeper heading
    template = "\n# T\n\n## Constraints <!-- wio: inherit -->\n"
    body = "# Title\n\n## Constraint\n\n### Detail\n\n## Zzz\n"

    # When the body is checked
    found = _run(body, template)

    # Then the first has the suggestion, the second none, and the deeper heading
    # gives nothing
    assert found == [
        (
            "warning",
            f"{FILE}:10",
            "The section `Zzz` is not in the template `t`",
        ),
        (
            "warning",
            f"{FILE}:6",
            STRAY_CLOSE,
        ),
    ]


def test_a_contract_without_a_template_gets_no_warning_about_a_section() -> None:
    """Sections of its own are free."""
    # Given a contract with no template and sections of its own
    # When the body is checked
    found = _run("# Title\n\n## Anything\n\n## Else\n")

    # Then there is no warning about a section
    assert found == []


def test_a_directive_list_in_a_contract_that_follows_a_template_is_ignored() -> None:
    """Such a list is a warning and changes nothing."""
    # Given a template that requires `Goals` and has `Notes` and `Bad`, and a
    # contract that lacks `Goals` and has lists on three headings
    template = "\n# T\n\n## Goals <!-- wio: required -->\n\n## Notes\n\n## Bad\n"
    body = (
        "# Title\n\n## Notes <!-- wio: required -->\n\n"
        "## Bad <!-- wio: mandatory -->\n\n### Deep <!-- wio: required -->\n"
    )

    # When the body is checked
    found = _run(body, template)

    # Then there is one warning for each list, no parser error, no stray section,
    # and the error for the missing `Goals`
    ignored = (
        "The directive list is ignored because the contract follows the template `t`"
    )
    assert found == [
        ("error", FILE, "The section `Goals` is required by the template `t`"),
        ("warning", f"{FILE}:10", ignored),
        ("warning", f"{FILE}:6", ignored),
        ("warning", f"{FILE}:8", ignored),
    ]


def test_a_directive_list_on_a_repeated_heading_is_warned_of_twice() -> None:
    """Every list is judged, and a repeat is a warning."""
    # Given a template with `Notes` and a contract that repeats it with a list
    template = "\n# T\n\n## Notes\n"
    body = "# Title\n\n## Notes\n\n## Notes <!-- wio: required -->\n"

    # When the body is checked
    found = _run(body, template)

    # Then there are the warning that the list is ignored and that it is repeated
    assert sorted(m for _, _, m in found) == [
        "The directive list is ignored because the contract follows the template `t`",
        "The section `Notes` is repeated; the first one counts",
    ]


def test_a_contract_without_a_template_is_checked_by_its_own_headings() -> None:
    """Its lists are read, and a list that cannot be read is an error."""
    # Given a contract with no template whose headings carry directives
    body = (
        "# Title\n\n## Purpose <!-- wio: required -->\n\n"
        "## Goals <!-- wio: items>=2 -->\n\n- one\n\n"
        "## Bad <!-- wio: mandatory -->\n\n### Deep <!-- wio: required -->\n"
    )

    # When the body is checked
    found = _run(body)

    # Then there are the error for the items, the parser's error at its line and
    # column, and the error for the deeper heading, and none for `Purpose`
    assert [(s, w) for s, w, _ in found] == [
        ("error", f"{FILE}:12:18"),
        ("error", f"{FILE}:14:10"),
        ("error", f"{FILE}:8"),
    ]
    assert found[1][2] == "Directives are read on level-2 headings only"


def test_a_list_on_the_title_is_an_error_alone_and_a_warning_under_a_template() -> None:
    """The title is level 1, where directives are not read."""
    # Given a contract whose title has a list
    body = "# Title <!-- wio: required -->\n"

    # When it is checked without a template and under one
    alone = _run(body)
    under = _run(body, "\n# T\n")

    # Then it is an error, and a warning
    assert [(s, m) for s, _, m in alone] == [
        ("error", "Directives are read on level-2 headings only")
    ]
    assert [s for s, _, _ in under] == ["warning"]


def test_a_contract_with_no_directive_list_has_no_diagnostic_about_its_body() -> None:
    """Nothing to read, nothing to report."""
    # Given a contract with no template and no directive list
    # When the body is checked
    found = _run("# Title\n\n## Purpose\n\ntext\n")

    # Then there is nothing
    assert found == []


def test_a_repeated_section_and_a_missing_title_are_warnings() -> None:
    """A repeat carries no items, and a contract with no heading is told."""
    # Given a contract with `Goals` twice, the first with one item and the second
    # with two, under a template that wants two, and a contract with no heading
    template = "\n# T\n\n## Goals <!-- wio: items>=2 -->\n"
    body = "# Title\n\n## Goals\n\n- one\n\n## Goals\n\n- a\n- b\n"

    # When the bodies are checked
    found = _run(body, template)
    untitled = _run("just text\n", "\n# T\n", title=None)

    # Then the repeat is a warning, the first's items are too few, and the second
    # contract has no title
    assert [(s, w) for s, w, _ in found] == [
        ("error", f"{FILE}:6"),
        ("warning", f"{FILE}:10"),
    ]
    assert found[1][2] == "The section `Goals` is repeated; the first one counts"
    assert untitled == [("warning", FILE, "The contract has no title")]


def test_a_template_that_cannot_be_used_gets_no_body_check_and_is_read_once() -> None:
    """A missing and a rejected template give nothing, and a good one is read once."""
    # Given Works that name a missing template and a rejected one, and three that
    # follow one good template, and a file system that counts reads
    disk = _Counting(
        {ROOT / TEMPLATE_FILE: _template_text("\n## Goals <!-- wio: required -->\n")}
    )
    checker = BodyChecker(ROOT, disk)
    work, block = _contract(BAD_BODY, title=None)
    good = Template("t", "feature", None, None, Path(TEMPLATE_FILE), entry=False)

    # When the bodies are checked on their own
    missing = checker.check(_named(work, "nosuch"), block, None)
    rejected = checker.check(_named(work, "bad"), block, None)
    followers = [checker.check(_named(work, "t"), block, good) for _ in range(3)]

    # Then the first two have nothing, and the good template's file was read once
    assert (missing, rejected) == ([], [])
    assert all(len(found) >= 1 for found in followers)
    assert disk.reads[ROOT / TEMPLATE_FILE] == 1


@pytest.mark.parametrize(
    "text",
    [None, "<!-- wio\nkind = 'x'\n", "no block at all\n"],
    ids=["missing file", "block does not close", "no block"],
)
def test_a_template_that_cannot_be_read_is_skipped(text: str | None) -> None:
    """A template whose file fails gives the contract no body check."""
    # Given a template whose file is missing, does not close or has no block
    files = {} if text is None else {ROOT / TEMPLATE_FILE: text}
    checker = BodyChecker(ROOT, MemoryFileSystem(files))
    work, block = _contract(BAD_BODY, title=None)
    given = Template("t", "feature", None, None, Path(TEMPLATE_FILE), entry=False)

    # When a contract that follows it, whose body would be reported if it were
    # checked by its own headings, is checked
    found = checker.check(_named(work, "t"), block, given)

    # Then there is no diagnostic
    assert found == []


def test_a_fresh_work_passes_when_the_template_requires_only_headings() -> None:
    """What an entry template requires decides what a Work needs."""
    # Given a template that requires `Purpose`, and a contract made from it, and a
    # template that requires an item
    headings = "\n# T\n\n## Purpose <!-- wio: required -->\n"
    items = "\n# T\n\n## Goals <!-- wio: items>=1 -->\n"

    # When a contract with its Purpose written, and one with only an authoring
    # comment under Goals, and one with an item are checked
    first = _run("# Title\n\n## Purpose\n\nWhy.\n", headings)
    second = _run("# Title\n\n## Goals\n\n<!-- Write the goals. -->\n", items)
    third = _run("# Title\n\n## Goals\n\n- First goal\n", items)

    # Then the first passes, the second has one error at `## Goals`, and the third
    # passes
    assert first == []
    assert [(s, w) for s, w, _ in second] == [("error", f"{FILE}:6")]
    assert third == []


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
    outline: Sequence[Heading] = [
        Heading(2, raw, raw, 10 + n) for n, raw in enumerate(raws)
    ]

    # When they are judged against a template `t`
    found = module._ignored_lists("c/README.md", outline, "t")  # noqa: SLF001

    # Then each list is a warning at its heading's line
    assert [(d.severity, d.where) for d in found] == [
        ("warning", "c/README.md:10"),
        ("warning", "c/README.md:11"),
        ("warning", "c/README.md:12"),
        ("warning", "c/README.md:12"),
    ]


def test_a_deeper_template_heading_is_no_section() -> None:
    """Only `##` headings of the template are sections."""
    # Given a template with `### Deep` and a contract with `## Deep`
    template = "\n# T\n\n### Deep\n"

    # When the body is checked
    found = _run("# Title\n\n## Deep\n", template)

    # Then the contract's heading is not in the template
    assert [m for _, _, m in found] == ["The section `Deep` is not in the template `t`"]
