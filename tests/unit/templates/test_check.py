# SPDX-License-Identifier: Apache-2.0
"""Tests of the checks of the templates in `wio.templates`."""

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, override

import pytest

from tests.unit.fakes import ROOT, MemoryFileSystem
from wio.models.config import Config, Templates
from wio.models.diagnostics import Diagnostic
from wio.models.frozen import freeze
from wio.templates import check
from wio.templates.check import Reading, check_templates

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable
    from pathlib import Path

DIR = ROOT / ".agents" / "wio" / "templates"
BLOCK = '<!-- wio\nkind = "feature"\n-->\n\n# Title\n\n## Goals\n'
SKIP = "Pending the implementation stage."


@pytest.mark.skip(reason=SKIP)
def test_a_project_that_passes_has_no_diagnostic() -> None:
    """AC-1: valid templates, and no template at all, give an empty result."""
    # Given a project whose templates have no problem, and one with no templates
    # When the templates are checked
    # Then there is no diagnostic for either


@pytest.mark.skip(reason=SKIP)
def test_two_problems_are_both_found() -> None:
    """AC-1: an unknown key in one template and a wrong directive in another."""
    # Given a project with an unknown key in one template and a wrong directive
    # in another
    # When the templates are checked
    # Then both are in the result, in the order of the constraint


@pytest.mark.skip(reason=SKIP)
def test_the_diagnostics_are_ordered_with_numbers_as_numbers() -> None:
    """The constraint on order: line 4 comes before line 12 of the same file."""
    # Given diagnostics at `a.md:12`, `a.md:4`, `a.md:4:2`, `a.md` and `b.md:1`
    # When they are ordered
    # Then they are `a.md`, `a.md:4`, `a.md:4:2`, `a.md:12` and `b.md:1`


@pytest.mark.skip(reason=SKIP)
def test_the_problems_of_discovery_are_errors_of_the_check() -> None:
    """AC-2: a block that does not close and two files with one name."""
    # Given a project with a block that does not close and two files named
    # `a.md`
    # When the templates are checked
    # Then there is an error for the block and one for the duplicate, each with
    # its place


@pytest.mark.skip(reason=SKIP)
def test_a_missing_directory_is_one_error_and_no_missing_entry() -> None:
    """AC-2: the directory is named, and the entry template is not reported."""
    # Given a config with `[templates] dir = "t"` and the kind `feature`, and no
    # directory `t`
    # When the templates are checked
    # Then there is one error that names the directory and none for the entry


@pytest.mark.skip(reason=SKIP)
def test_an_unknown_key_is_an_error_and_the_contract_keys_are_free() -> None:
    """AC-3: `name`, a misspelled key and a non-table `contract` or `actions`."""
    # Given templates with `name`, `descriptions`, `contract = 1`, `actions = 1`
    # and a `[contract]` that holds `ticket = ""`
    # When the keys are checked
    # Then the first four each give an error that names the file and the key,
    # the first saying that a template is named by its file, and the last none


@pytest.mark.skip(reason=SKIP)
def test_a_wrong_directive_list_names_the_file_line_and_column() -> None:
    """AC-4: a refused list, an unclosed one and one on a level-3 heading."""
    # Given a template with `## A <!-- wio: mandatory -->` on line 12,
    # `## B <!-- wio: required,` on line 14 and `### C <!-- wio: required -->`
    # on line 16
    # When the headings are checked
    # Then the places are `<file>:12:16`, `<file>:14:6` and `<file>:16:7`, the
    # third saying that directives are read on level-2 headings only


@pytest.mark.skip(reason=SKIP)
def test_a_name_the_config_does_not_declare_is_an_error() -> None:
    """AC-5: action, stage preset and stage names, and values of the wrong type."""
    # Given a config declaring `define`, `define-feature` and `implementation`,
    # and the seven `[actions]` of AC-5
    # When the names are checked
    # Then the first three give an error that names the file and the name, the
    # next two one that names the key `define`, and the last two give none


@pytest.mark.skip(reason=SKIP)
def test_a_kind_that_disagrees_with_the_config_is_an_error() -> None:
    """AC-6: an undeclared kind, a missing entry and an entry of another kind."""
    # Given the kinds `feature = "feature.draft"` and `bugfix = "missing"`, a
    # template `feature.draft` of kind `bugfix` and one `other` of kind `nokind`
    # When the kinds are checked
    # Then there are three errors, whose places are the file of `other`,
    # `templates.kinds.bugfix` and the file of `feature.draft`


@pytest.mark.skip(reason=SKIP)
def test_a_repeated_heading_is_a_warning() -> None:
    """AC-7: the second `##` heading with the same text, ignoring case."""
    # Given a template with `## Goals <!-- wio: required -->` and `## goals`
    # When the headings are checked
    # Then there is one warning at the second heading's line that names the
    # line of the first


@pytest.mark.skip(reason=SKIP)
def test_the_text_says_that_the_templates_pass_and_the_json_is_empty() -> None:
    """AC-1: the rendering of no diagnostic, as text and as JSON."""
    # Given no diagnostic
    # When it is rendered as text and as JSON
    # Then the text is `The templates pass.` and a newline, and the JSON is `[]`
    # and a newline


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
    (templates, kinds, unbuilt) = calls["check_kinds"]
    assert [template.name for template in templates] == ["feature.draft"]  # type: ignore[attr-defined]
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
    (templates, _, unbuilt) = dict(leaves.calls)["check_kinds"]
    assert [template.name for template in templates] == ["feature.draft"]  # type: ignore[attr-defined]
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
