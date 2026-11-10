# SPDX-License-Identifier: Apache-2.0
"""Tests of the checks of the templates in `wio.templates`."""

import json
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, cast, override

from tests.unit.fakes import ROOT, MemoryFileSystem
from wio.models.config import Action, Config, Stage, Templates
from wio.models.diagnostics import Diagnostic
from wio.models.frozen import freeze
from wio.templates import check
from wio.templates.check import (
    Reading,
    check_templates,
    order_diagnostics,
    render_check,
)

if TYPE_CHECKING:
    from collections.abc import Callable, Collection, Iterable, Mapping, Sequence
    from pathlib import Path

    import pytest

    from wio.models.template import Template

DIR = ROOT / ".agents" / "wio" / "templates"
BLOCK = '<!-- wio\nkind = "feature"\n-->\n\n# Title\n\n## Goals\n'


def _block(*lines: str, body: str = "# Title\n") -> str:
    """Write a template whose comment block holds the given lines.

    Args:
        *lines: The lines of TOML, one per argument.
        body: The Markdown after the block.

    Returns:
        The text of the file.
    """
    return "\n".join(["<!-- wio", *lines, "-->", "", body])


def _run(
    files: dict[Path, str], config: Config | None = None
) -> tuple[Diagnostic, ...]:
    """Check the templates of an in-memory project with the real checks.

    Args:
        files: The stored files.
        config: The settings, or the default that declares the kind `feature`.

    Returns:
        The diagnostics of the check.
    """
    return check_templates(ROOT, config or _config(), MemoryFileSystem(files))


def _where(diagnostics: Iterable[Diagnostic]) -> list[tuple[str, str]]:
    """Reduce diagnostics to the severity and the place of each.

    Args:
        diagnostics: The findings.

    Returns:
        A pair for each, in order.
    """
    return [(d.severity, d.where) for d in diagnostics]


DRAFT = DIR / "feature.draft.md"
DRAFT_PLACE = ".agents/wio/templates/feature.draft.md"
VALID = _block('kind = "feature"')


def test_a_project_that_passes_has_no_diagnostic() -> None:
    """AC-1: valid templates, and no template at all, give an empty result."""
    # Given a project whose templates have no problem, and one with no templates
    valid = {DRAFT: VALID}
    # When the templates are checked
    passing = _run(valid)
    empty = _run({}, Config())

    # Then there is no diagnostic for either
    assert (passing, empty) == ((), ())


def test_two_problems_are_both_found() -> None:
    """AC-1: an unknown key in one template and a wrong directive in another."""
    # Given a project with an unknown key in one template and a wrong directive
    # in another
    files = {
        DRAFT: _block('kind = "feature"', 'tickets = "x"'),
        DIR / "other.md": _block(
            'kind = "feature"', body="# T\n\n## A <!-- wio: x -->"
        ),
    }

    # When the templates are checked
    found = _run(files)

    # Then both are in the result, ordered by file
    assert [d.where.split(":")[0] for d in found] == [
        DRAFT_PLACE,
        ".agents/wio/templates/other.md",
    ]
    assert {d.severity for d in found} == {"error"}


def test_the_diagnostics_are_ordered_with_numbers_as_numbers() -> None:
    """The constraint on order: line 4 comes before line 12 of the same file."""
    # Given diagnostics at `a.md:12`, `a.md:4`, `a.md:4:2`, `a.md` and `b.md:1`,
    # and a key path and a pair of files
    places = ["b.md:1", "a.md:12", "a.md:4:2", "templates.kinds.x", "a.md:4", "a.md"]
    mixed = [Diagnostic("error", where, "m") for where in places]

    # When they are ordered
    ordered = [d.where for d in order_diagnostics(mixed)]

    # Then the files come in numeric order, and the other places follow
    assert ordered == [
        "a.md",
        "a.md:4",
        "a.md:4:2",
        "a.md:12",
        "b.md:1",
        "templates.kinds.x",
    ]


def test_ties_are_broken_by_severity_and_message() -> None:
    """Errors come before warnings at one place, then the messages."""
    # Given a warning and two errors at one place
    given = [
        Diagnostic("warning", "a.md:1", "a"),
        Diagnostic("error", "a.md:1", "z"),
        Diagnostic("error", "a.md:1", "b"),
    ]

    # When they are ordered
    ordered = order_diagnostics(given)

    # Then the errors come first, by message
    assert [(d.severity, d.message) for d in ordered] == [
        ("error", "b"),
        ("error", "z"),
        ("warning", "a"),
    ]


def test_the_problems_of_discovery_are_errors_of_the_check() -> None:
    """AC-2: a block that does not close and two files with one name."""
    # Given a project with a block that does not close and two files named `a.md`
    files = {
        DIR / "broken.md": "<!-- wio\nkind = 'x'\n",
        DIR / "a.md": VALID,
        DIR / "sub" / "a.md": VALID,
        DRAFT: VALID,
    }

    # When the templates are checked
    found = _run(files)

    # Then there is an error for the block and one for the duplicate, each with
    # its place
    assert _where(found) == [
        ("error", ".agents/wio/templates/broken.md:1"),
        ("error", ".agents/wio/templates/a.md, .agents/wio/templates/sub/a.md"),
    ]


def test_a_missing_directory_is_one_error_and_no_missing_entry() -> None:
    """AC-2: the directory is named, and the entry template is not reported."""
    # Given a config with `[templates] dir = "t"` and the kind `feature`, and no
    # directory `t`
    config = _config(directory="t")

    # When the templates are checked
    found = _run({}, config)

    # Then there is one error that names the directory and none for the entry
    assert _where(found) == [("error", "t")]


def test_an_unknown_key_is_an_error_and_the_contract_keys_are_free() -> None:
    """AC-3: `name`, a misspelled key and a non-table `contract` or `actions`."""
    # Given templates with `name`, `descriptions`, `contract = 1`, `actions = 1`
    # and a `[contract]` that holds `ticket = ""`
    files = {
        DIR / "a.md": _block('kind = "feature"', 'name = "x"'),
        DIR / "b.md": _block('kind = "feature"', 'descriptions = "y"'),
        DIR / "c.md": _block('kind = "feature"', "contract = 1"),
        DIR / "d.md": _block('kind = "feature"', "actions = 1"),
        DIR / "e.md": _block('kind = "feature"', "[contract]", 'ticket = ""'),
        DRAFT: VALID,
    }

    # When the templates are checked
    found = _run(files)

    # Then the first four each give an error that names the file and the key, the
    # first saying that a template is named by its file, and the last gives none
    assert [(d.where, d.message) for d in found] == [
        (
            ".agents/wio/templates/a.md",
            "A template has no `name` key: it is named by its file",
        ),
        (".agents/wio/templates/b.md", "Unknown key `descriptions` in the metadata"),
        (".agents/wio/templates/c.md", "`contract` must be a table"),
        (".agents/wio/templates/d.md", "`actions` must be a table"),
    ]


def test_a_wrong_directive_list_names_the_file_line_and_column() -> None:
    """AC-4: a refused list, an unclosed one and one on a level-3 heading."""
    # Given a template with `## A <!-- wio: mandatory -->` on line 12,
    # `## B <!-- wio: required,` on line 14 and `### C <!-- wio: required -->` on
    # line 16
    filler = "\n" * 3
    body = (
        "# Title\n" + filler * 3 + "x\n\n"
        "## A <!-- wio: mandatory -->\n\n"
        "## B <!-- wio: required,\n\n"
        "### C <!-- wio: required -->\n"
    )
    text = _block('kind = "feature"', body=body)
    lines = text.splitlines()
    first = lines.index("## A <!-- wio: mandatory -->") + 1

    # When the templates are checked
    found = _run({DRAFT: text})

    # Then the places are the file, the lines of the headings and the columns
    assert [d.where for d in found] == [
        f"{DRAFT_PLACE}:{first}:16",
        f"{DRAFT_PLACE}:{first + 2}:6",
        f"{DRAFT_PLACE}:{first + 4}:7",
    ]
    assert found[2].message == "Directives are read on level-2 headings only"


def test_a_name_the_config_does_not_declare_is_an_error() -> None:
    """AC-5: action, stage preset and stage names, and values of the wrong type."""
    # Given a config declaring `define`, `define-feature` and `implementation`,
    # and seven `[actions]`, one to a template
    config = Config(
        templates=Templates(kinds=freeze({"feature": "feature.draft"})),
        actions=freeze({"define": Action(description="d")}),
        stage_presets=freeze({"define-feature": ("implementation",)}),
        stages=freeze({"implementation": Stage()}),
    )
    entries = [
        'define = "nosuch"',
        'nosuch = "define-feature"',
        'define = ["nosuch"]',
        "define = 1",
        "define = [1]",
        "define = []",
        'define = ["implementation"]',
    ]
    files = {DRAFT: VALID}
    for index, entry in enumerate(entries):
        files[DIR / f"t{index}.md"] = _block('kind = "feature"', "[actions]", entry)

    # When the templates are checked
    found = _run(files, config)

    # Then the first three each name the file and the undeclared name, the next
    # two the key `define`, and the last two give none
    assert [(d.where.rsplit("/", 1)[1], d.message) for d in found] == [
        ("t0.md", "The stage preset `nosuch` is not declared"),
        ("t1.md", "The action `nosuch` is not declared"),
        ("t2.md", "The stage `nosuch` is not declared"),
        ("t3.md", "`define` must be a name or a list of names"),
        ("t4.md", "`define` must be a name or a list of names"),
    ]


def test_a_kind_that_disagrees_with_the_config_is_an_error() -> None:
    """AC-6: an undeclared kind, a missing entry and an entry of another kind."""
    # Given the kinds `feature = "feature.draft"` and `bugfix = "missing"`, a
    # template `feature.draft` of kind `bugfix` and one `other` of kind `nokind`
    config = Config(
        templates=Templates(
            kinds=freeze({"feature": "feature.draft", "bugfix": "missing"})
        )
    )
    files = {
        DRAFT: _block('kind = "bugfix"'),
        DIR / "other.md": _block('kind = "nokind"'),
    }

    # When the templates are checked
    found = _run(files, config)

    # Then there are three errors, whose places are the file of `feature.draft`,
    # the file of `other` and `templates.kinds.bugfix`
    assert _where(found) == [
        ("error", DRAFT_PLACE),
        ("error", ".agents/wio/templates/other.md"),
        ("error", "templates.kinds.bugfix"),
    ]
    messages = " ".join(d.message for d in found)
    assert "`nokind`" in messages
    assert "`missing`" in messages
    assert "entry template of `feature`" in messages
    assert "kind `bugfix` differs" in messages


def test_a_repeated_heading_is_a_warning() -> None:
    """AC-7: the second `##` heading with the same text, ignoring case."""
    # Given a template with `## Goals <!-- wio: required -->` and `## goals`
    text = _block(
        'kind = "feature"', body="# T\n\n## Goals <!-- wio: required -->\n\n## goals\n"
    )
    first = text.splitlines().index("## Goals <!-- wio: required -->") + 1

    # When the templates are checked
    found = _run({DRAFT: text})

    # Then there is one warning at the second heading that names the first line
    assert _where(found) == [("warning", f"{DRAFT_PLACE}:{first + 2}")]
    assert f"line {first}" in found[0].message


def test_a_heading_with_a_refused_list_still_counts_for_repeats() -> None:
    """A repeat is found by the text before a list that the parser refuses."""
    # Given `## Goals <!-- wio: nosuch -->` and `## Goals`
    text = _block(
        'kind = "feature"', body="# T\n\n## Goals <!-- wio: nosuch -->\n\n## Goals\n"
    )

    # When the templates are checked
    found = _run({DRAFT: text})

    # Then there is the error of the list and the warning of the repeat
    assert [d.severity for d in found] == ["error", "warning"]


def test_the_text_says_that_the_templates_pass_and_the_json_is_empty() -> None:
    """AC-1: the rendering of no diagnostic, as text and as JSON."""
    # Given no diagnostic
    # When it is rendered as text and as JSON
    text = render_check([], as_json=False)
    as_json = render_check([], as_json=True)

    # Then the text is `The templates pass.` and a newline, and the JSON is `[]`
    # and a newline
    assert (text, as_json) == ("The templates pass.\n", "[]\n")


def test_the_diagnostics_are_rendered_in_the_order_given() -> None:
    """AC-1: lines, and an array with `severity`, `where` and `message`."""
    # Given a line 4 diagnostic before a line 12 one and a warning
    found = [
        Diagnostic("error", "a.md:4", "x"),
        Diagnostic("warning", "a.md:12", "y"),
    ]

    # When they are rendered as text and as JSON
    text = render_check(found, as_json=False)
    data = json.loads(render_check(found, as_json=True))

    # Then the text has a line for each, in that order, and the JSON the same
    assert text == "error: a.md:4: x\nwarning: a.md:12: y\n"
    assert [item["where"] for item in data] == ["a.md:4", "a.md:12"]
    assert set(data[0]) == {"severity", "where", "message"}


@dataclass
class _Leaves:
    """The checks of the module, replaced by recorders that say what they got."""

    calls: list[tuple[str, tuple[object, ...]]] = field(default_factory=list)
    ordered: list[list[Diagnostic]] = field(default_factory=list)


def _record(
    leaves: _Leaves, name: str, found: Callable[[], list[Diagnostic]]
) -> Callable[..., list[Diagnostic]]:
    """Make a replacement for a check that records its call.

    Args:
        leaves: Where the call is recorded.
        name: The check's name.
        found: Makes what the check returns.

    Returns:
        The replacement, which gives what `found` makes.
    """

    def leaf(*args: object) -> list[Diagnostic]:
        """Record the call and give the canned result.

        Args:
            *args: What the check was given.

        Returns:
            The canned diagnostics.
        """
        leaves.calls.append((name, args))
        return found()

    return leaf


def _stub_leaves(monkeypatch: pytest.MonkeyPatch) -> _Leaves:
    """Replace every check of `wio.templates.check` by a recorder.

    Args:
        monkeypatch: The fixture that restores them.

    Returns:
        The record of the calls. Each check gives one error named after it, and
        the ordering keeps the order it is given.
    """
    leaves = _Leaves()
    for name in ("check_keys", "check_headings", "check_actions", "check_kinds"):
        canned = Diagnostic("error", name, name)
        monkeypatch.setattr(check, name, _record(leaves, name, lambda c=canned: [c]))

    def order(found: Iterable[Diagnostic]) -> tuple[Diagnostic, ...]:
        """Record what the check hands to the ordering, and keep its order.

        Args:
            found: Every diagnostic that the check gathered.

        Returns:
            The same diagnostics, as they were given.
        """
        leaves.ordered.append(list(found))
        return tuple(leaves.ordered[-1])

    monkeypatch.setattr(check, "order_diagnostics", order)
    return leaves


def _config(*, directory: str | None = None) -> Config:
    """Make a config that declares the kind `feature`.

    Args:
        directory: The templates directory, or `None` for the default.

    Returns:
        The config.
    """
    kinds = freeze({"feature": "feature.draft"})
    if directory is None:
        return Config(templates=Templates(kinds=kinds))
    return Config(templates=Templates(dir=directory, kinds=kinds))


def _kinds_call(
    leaves: _Leaves,
) -> tuple[Sequence[Template], Mapping[str, str], Collection[str]]:
    """Read the arguments that `check_kinds` was called with.

    Args:
        leaves: The record of the calls.

    Returns:
        The templates, the kinds and the unbuilt names it was given.
    """
    arguments = dict(leaves.calls)["check_kinds"]
    return cast(
        "tuple[Sequence[Template], Mapping[str, str], Collection[str]]", arguments
    )


def _names(diagnostics: Iterable[Diagnostic]) -> list[str]:
    """List what the recorders reported, which is the name of each.

    Args:
        diagnostics: The findings.

    Returns:
        Their messages.
    """
    return [diagnostic.message for diagnostic in diagnostics]


def test_wiring_runs_every_check_on_the_templates_that_discovery_built(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The checks get each template's place, data and headings, and the config."""
    # Given a project with one template and recorders in place of the checks
    leaves = _stub_leaves(monkeypatch)
    files: dict[Path, str] = {DIR / "feature.draft.md": BLOCK}

    # When the templates are checked
    found = check_templates(ROOT, _config(), MemoryFileSystem(files))

    # Then every check ran once, and its diagnostic is in the result
    assert sorted(_names(found)) == [
        "check_actions",
        "check_headings",
        "check_keys",
        "check_kinds",
    ]
    calls = dict(leaves.calls)
    assert calls["check_keys"] == (
        ".agents/wio/templates/feature.draft.md",
        {"kind": "feature"},
    )
    (reading,) = calls["check_headings"]
    assert isinstance(reading, Reading)
    assert [heading.text for heading in reading.headings] == ["Title", "Goals"]
    config = _config()
    assert calls["check_actions"] == (
        ".agents/wio/templates/feature.draft.md",
        {},
        config,
    )
    templates, kinds, unbuilt = _kinds_call(leaves)
    assert [template.name for template in templates] == ["feature.draft"]
    assert (kinds, unbuilt) == (config.templates.kinds, frozenset())
    assert leaves.ordered == [list(found)]


def test_wiring_keeps_the_problems_of_discovery_and_excuses_the_unbuilt_entry(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A broken entry template is an error of discovery and is not reported missing."""
    # Given a project whose entry template `feature.draft` has an unclosed block
    leaves = _stub_leaves(monkeypatch)
    files: dict[Path, str] = {DIR / "feature.draft.md": "<!-- wio\nkind = 'x'\n"}

    # When the templates are checked
    found = check_templates(ROOT, _config(), MemoryFileSystem(files))

    # Then the error of discovery is in the result, and `check_kinds` was told
    # that the entry template could not be built
    assert any(
        d.where.startswith(".agents/wio/templates/feature.draft.md") for d in found
    )
    kinds_call = dict(leaves.calls)["check_kinds"]
    assert kinds_call[2] == frozenset({"feature.draft"})


def test_wiring_returns_a_refused_directory_alone(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A missing directory is one error, and no check runs after it."""
    # Given a config whose templates directory `t` does not exist
    leaves = _stub_leaves(monkeypatch)

    # When the templates are checked
    found = check_templates(ROOT, _config(directory="t"), MemoryFileSystem({}))

    # Then the result is the one error of discovery, and no check ran
    assert [(d.severity, d.where) for d in found] == [("error", "t")]
    assert leaves.calls == []


@dataclass
class _ReadsTwice(MemoryFileSystem):
    """A file system whose file can be read once and fails the second time."""

    fragile: Path | None = None
    reads: int = 0

    @override
    def read_text(self, path: Path) -> str:
        """Read a file, failing the second time the fragile one is read.

        Args:
            path: The file.

        Returns:
            Its text.

        Raises:
            PermissionError: The fragile file is read a second time.
        """
        if path == self.fragile:
            self.reads += 1
            if self.reads > 1:
                raise PermissionError(13, "Permission denied")
        return super().read_text(path)


def test_wiring_judges_a_template_that_cannot_be_read_again_as_a_template(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A second read that fails is one error, and not a missing entry template."""
    # Given an entry template that can be read once and not twice
    leaves = _stub_leaves(monkeypatch)
    path = DIR / "feature.draft.md"
    files = _ReadsTwice({path: BLOCK}, fragile=path)

    # When the templates are checked
    found = check_templates(ROOT, _config(), files)

    # Then its read error is in the result, no check of its content ran, and the
    # kinds check still got the template and no unbuilt name
    assert [d.where for d in found if d.message != "check_kinds"] == [
        ".agents/wio/templates/feature.draft.md"
    ]
    names = [name for name, _ in leaves.calls]
    assert names == ["check_kinds"]
    templates, _, unbuilt = _kinds_call(leaves)
    assert [template.name for template in templates] == ["feature.draft"]
    assert unbuilt == frozenset()


def test_wiring_excuses_an_entry_template_that_two_files_claim(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A duplicate name is an error of discovery, and its entry is not missing."""
    # Given two files named `feature.draft.md`, the entry template of the kind
    leaves = _stub_leaves(monkeypatch)
    files: dict[Path, str] = {
        DIR / "feature.draft.md": BLOCK,
        DIR / "more" / "feature.draft.md": BLOCK,
    }

    # When the templates are checked
    found = check_templates(ROOT, _config(), MemoryFileSystem(files))

    # Then discovery's error is in the result, and the kinds check was told that
    # the entry template could not be built
    assert any("Two templates are named" in d.message for d in found)
    assert dict(leaves.calls)["check_kinds"][2] == frozenset({"feature.draft"})


def test_wiring_runs_the_kinds_check_when_the_default_directory_is_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A missing default directory holds no templates, so the entries are missing."""
    # Given a project with no templates directory and the default configured
    leaves = _stub_leaves(monkeypatch)

    # When the templates are checked
    found = check_templates(ROOT, _config(), MemoryFileSystem({}))

    # Then only the kinds check ran, on no templates
    assert [name for name, _ in leaves.calls] == ["check_kinds"]
    assert dict(leaves.calls)["check_kinds"][0] == ()
    assert _names(found) == ["check_kinds"]
