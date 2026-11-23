# SPDX-License-Identifier: Apache-2.0
"""Tests of the discovery of rulesets in `wio.rules`."""

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, override

import pytest

from tests.unit.fakes import ROOT, MemoryFileSystem
from tests.unit.rules.support import kinds
from wio.errors import DiagnosticsError
from wio.models.diagnostics import Diagnostic, sort_diagnostics
from wio.rules import Discovery, discover, refuse_on_errors

if TYPE_CHECKING:
    from collections.abc import Sequence
    from pathlib import Path

RULES = ROOT / ".agents" / "wio" / "rules"
_REL = ".agents/wio/rules"


@dataclass
class _Listing(MemoryFileSystem):
    """A file system whose listing is reversed or fails for some directories."""

    reverse: bool = False
    unlistable: set[Path] = field(default_factory=set)

    @override
    def list_dir(self, path: Path) -> Sequence[Path]:
        """List a directory, reversed when asked, or fail for an unlistable one.

        Args:
            path: The directory.

        Returns:
            The entries, in the order or the reverse of the stored listing.

        Raises:
            PermissionError: The directory is one of `unlistable`.
        """
        if path in self.unlistable:
            raise PermissionError(path)
        entries = super().list_dir(path)
        return list(reversed(entries)) if self.reverse else entries


def _rule(code: str, name: str) -> str:
    """Write a rule file.

    Args:
        code: The `code` key.
        name: The `name` key.

    Returns:
        The text of a marked rule file with a one-line body.
    """
    return f'<!-- wio\ncode = "{code}"\nname = "{name}"\n-->\n\nBody.\n'


def _manifest(*families: str) -> str:
    """Write a manifest that declares families.

    Args:
        *families: The letters of the families.

    Returns:
        The text of a `ruleset.toml`.
    """
    return "[families]\n" + "".join(f'{f} = "Topic"\n' for f in families)


def _find(disk: MemoryFileSystem) -> Discovery:
    """Discover the rulesets of the disk.

    Args:
        disk: The files.

    Returns:
        What the walk found.
    """
    return discover(ROOT, disk)


def _demo(
    *rules: tuple[str, str, str], families: tuple[str, ...] = ("ARC",)
) -> dict[Path, str]:
    """Build the files of a ruleset `demo`.

    Args:
        *rules: A file name, a code and a name for each rule.
        families: The families its manifest declares.

    Returns:
        The files, by path.
    """
    files = {RULES / "demo" / "ruleset.toml": _manifest(*families)}
    for file, code, name in rules:
        files[RULES / "demo" / file] = _rule(code, name)
    return files


def test_rulesets_are_found_by_name_and_rules_by_family_and_code() -> None:
    """AC-3: the order of the rules, `rules_of` and `get`."""
    # Given `demo` with six rules in no order and `acme` with one
    codes = ["ARC2", "ARC10", "ARC1", "ARC01", "ARC001", "PAY1"]
    files = _demo(
        *((f"{c}-r.md", c, f"rule-{c.lower()}") for c in codes),
        families=("ARC", "PAY"),
    )
    files[RULES / "acme" / "ruleset.toml"] = _manifest("ARC")
    files[RULES / "acme" / "ARC1-r.md"] = _rule("ARC1", "other")

    # When the discovery runs
    found = _find(MemoryFileSystem(files))

    # Then `acme` comes before `demo`, the rules are in the order of family,
    # number and text, and the finders answer
    assert [r.name for r in found.rulesets] == ["acme", "demo"]
    demo = found.rulesets[1]
    assert [r.code for r in demo.rules] == [
        "ARC001",
        "ARC01",
        "ARC1",
        "ARC2",
        "ARC10",
        "PAY1",
    ]
    assert [r.code for r in demo.rules_of("ARC")] == [r.code for r in demo.rules[:5]]
    assert demo.rules_of("ZZZ") == ()
    assert demo.get("ARC2") == demo.rules[3]
    assert demo.get("ARC3") is None


def test_a_ruleset_is_a_value() -> None:
    """AC-3: equal with one hash, and not equal when a rule differs."""
    # Given two discoveries of the same files and one with a rule renamed
    files = _demo(("ARC1-r.md", "ARC1", "first"))
    other = _demo(("ARC1-r.md", "ARC1", "second"))

    # When the rulesets are compared
    first, second = _find(MemoryFileSystem(files)), _find(MemoryFileSystem(files))
    changed = _find(MemoryFileSystem(other))

    # Then the same files give equal rulesets with one hash, and a rule that
    # differs makes them unequal
    assert first.rulesets == second.rulesets
    assert hash(first.rulesets[0]) == hash(second.rulesets[0])
    assert first.rulesets != changed.rulesets


def test_a_rule_of_an_undeclared_family_is_an_error_and_left_out() -> None:
    """AC-4: the error names the file and the family."""
    # Given `demo` that declares `ARC` and holds `ARC001` and `ZZZ001`
    files = _demo(("ARC001-a.md", "ARC001", "a"), ("ZZZ001-z.md", "ZZZ001", "z"))

    # When the discovery runs
    found = _find(MemoryFileSystem(files))

    # Then one error names the file of `ZZZ001` and the family, and `demo` holds
    # `ARC001` only
    assert kinds(found.diagnostics) == [("error", f"{_REL}/demo/ZZZ001-z.md")]
    assert "`ZZZ`" in found.diagnostics[0].message
    assert [r.code for r in found.rulesets[0].rules] == ["ARC001"]


def test_rules_that_share_a_code_or_a_name_are_errors_and_left_out() -> None:
    """AC-4: one error for the code and one for the name, each naming both files."""
    # Given two files with `ARC001`, two rules named `keep-it-small` and `ARC009`
    files = _demo(
        ("ARC001-first.md", "ARC001", "first"),
        ("ARC001-second.md", "ARC001", "second"),
        ("ARC002-x.md", "ARC002", "keep-it-small"),
        ("ARC003-y.md", "ARC003", "keep-it-small"),
        ("ARC009-z.md", "ARC009", "other"),
    )

    # When the discovery runs
    found = _find(MemoryFileSystem(files))

    # Then one error names both files of the code and one names both of the name,
    # and `demo` holds `ARC009` only
    by_place = {d.where: d.message for d in found.diagnostics}
    code_place = f"{_REL}/demo/ARC001-first.md, {_REL}/demo/ARC001-second.md"
    name_place = f"{_REL}/demo/ARC002-x.md, {_REL}/demo/ARC003-y.md"
    assert sorted(w for _, w in kinds(found.diagnostics)) == [code_place, name_place]
    assert "`ARC001`" in by_place[code_place]
    assert "`keep-it-small`" in by_place[name_place]
    assert [r.code for r in found.rulesets[0].rules] == ["ARC009"]


def test_the_same_code_in_two_rulesets_is_no_fault() -> None:
    """AC-4: a qualified code is unique."""
    # Given two rulesets that each declare `ARC` and hold `ARC001`
    files = _demo(("ARC001-a.md", "ARC001", "a"))
    files[RULES / "acme" / "ruleset.toml"] = _manifest("ARC")
    files[RULES / "acme" / "ARC001-a.md"] = _rule("ARC001", "a")

    # When the discovery runs
    found = _find(MemoryFileSystem(files))

    # Then nothing is reported and both rules are returned
    assert found.diagnostics == ()
    assert [len(r.rules) for r in found.rulesets] == [1, 1]


def test_a_ruleset_is_named_by_its_directory() -> None:
    """AC-5: a wrong name and a link are errors, a hidden directory is ignored."""
    # Given `demo`, `My_Rules`, `.cache` and a link `linked`, each with a manifest
    files = {
        RULES / name / "ruleset.toml": _manifest("ARC")
        for name in ("demo", "My_Rules", ".cache", "linked")
    }
    disk = MemoryFileSystem(files, links={RULES / "linked"})

    # When the discovery runs
    found = _find(disk)

    # Then `demo` is returned, and one error each names `My_Rules` and `linked`
    assert [r.name for r in found.rulesets] == ["demo"]
    assert kinds(found.diagnostics) == [
        ("error", f"{_REL}/My_Rules"),
        ("error", f"{_REL}/linked"),
    ]
    assert "ruleset name" in found.diagnostics[0].message
    assert "symbolic link" in found.diagnostics[1].message
    assert not [p for op, p in disk.calls if op == "read_text" and ".cache" in p.parts]


def test_the_faults_of_rulesets_and_stray_files_are_reported() -> None:
    """AC-6: one error for each, and the good rulesets are returned whole."""
    # Given `bare` with no manifest, `broken` that does not parse, `outer` with a
    # manifest below it, a stray rule file, an unmarked README and `good`
    files = {
        RULES / "bare" / "notes.txt": "x",
        RULES / "broken" / "ruleset.toml": "[x",
        RULES / "outer" / "ruleset.toml": _manifest("ARC"),
        RULES / "outer" / "ARC001-a.md": _rule("ARC001", "a"),
        RULES / "outer" / "sub" / "ruleset.toml": _manifest("ARC"),
        RULES / "ARC001-stray.md": _rule("ARC001", "stray"),
        RULES / "README.md": "# Rules\n",
        RULES / "good" / "ruleset.toml": _manifest("ARC"),
        RULES / "good" / "ARC001-g.md": _rule("ARC001", "g"),
    }

    # When the discovery runs
    found = _find(MemoryFileSystem(files))

    # Then there is one error for each fault, and `outer` and `good` are whole
    places = [w for _, w in kinds(found.diagnostics)]
    assert len(places) == 4
    assert f"{_REL}/ARC001-stray.md" in places
    assert f"{_REL}/bare" in places
    assert f"{_REL}/outer/sub/ruleset.toml" in places
    assert any(w.startswith(f"{_REL}/broken/ruleset.toml") for w in places)
    assert [r.name for r in found.rulesets] == ["good", "outer"]
    assert [len(r.rules) for r in found.rulesets] == [1, 1]


def test_a_file_that_cannot_be_read_is_one_error_and_raises_nothing() -> None:
    """AC-6: bad UTF-8, an `OSError` and a linked manifest."""
    # Given `demo` with a rule that is not UTF-8, one whose read fails and a valid
    # one, and `other` whose manifest is a link
    files = _demo(
        ("ARC001-a.md", "ARC001", "a"),
        ("ARC002-b.md", "ARC002", "b"),
        ("ARC003-c.md", "ARC003", "c"),
    )
    files[RULES / "other" / "ruleset.toml"] = _manifest("ARC")
    disk = MemoryFileSystem(
        files,
        links={RULES / "other" / "ruleset.toml"},
        broken={
            RULES / "demo" / "ARC001-a.md": UnicodeDecodeError(
                "utf-8", b"\xff", 0, 1, "invalid start byte"
            ),
            RULES / "demo" / "ARC002-b.md": OSError("denied"),
        },
    )

    # When the discovery runs
    found = _find(disk)

    # Then there are three errors naming the files, and `demo` holds the valid
    # rule only
    assert sorted(w for _, w in kinds(found.diagnostics)) == [
        f"{_REL}/demo/ARC001-a.md",
        f"{_REL}/demo/ARC002-b.md",
        f"{_REL}/other/ruleset.toml",
    ]
    assert [r.code for r in found.rulesets[0].rules] == ["ARC003"]


@pytest.mark.parametrize("shape", ["missing", "link", "file"])
def test_the_rules_directory_is_checked_before_it_is_walked(shape: str) -> None:
    """AC-7: missing is no fault, a link or a file is one error and not walked."""
    # Given a repository with no rules directory, a link or a file in its place
    files = {RULES / "demo" / "ruleset.toml": _manifest("ARC")}
    disk = {
        "missing": MemoryFileSystem({ROOT / "README.md": "x"}),
        "link": MemoryFileSystem(files, links={RULES}),
        "file": MemoryFileSystem({RULES: "x"}),
    }[shape]

    # When the discovery runs
    found = _find(disk)

    # Then no ruleset is returned, and the other two give one error at the rules
    # directory
    assert found.rulesets == ()
    expected: list[tuple[str, str]] = [] if shape == "missing" else [("error", _REL)]
    assert kinds(found.diagnostics) == expected
    assert ("list_dir", RULES) not in disk.calls


@pytest.mark.parametrize("whole", [True, False])
def test_a_directory_that_cannot_be_listed_is_one_error(whole: bool) -> None:  # noqa: FBT001
    """AC-7: the rules directory, or one ruleset's directory beside a good one."""
    # Given a port that cannot list the rules directory or one ruleset directory
    files = _demo(("ARC001-a.md", "ARC001", "a"))
    files[RULES / "locked" / "ruleset.toml"] = _manifest("ARC")
    locked = RULES if whole else RULES / "locked"
    disk = _Listing(files, unlistable={locked})

    # When the discovery runs
    found = _find(disk)

    # Then one error names the directory, nothing is raised, and a good ruleset
    # beside the locked one is still returned
    place = _REL if whole else f"{_REL}/locked"
    assert kinds(found.diagnostics) == [("error", place)]
    assert [r.name for r in found.rulesets] == ([] if whole else ["demo"])


def test_the_diagnostics_do_not_depend_on_the_order_of_the_listing() -> None:
    """AC-8: the same rulesets and diagnostics, in the order of `sort_diagnostics`."""
    # Given a rule whose block does not close, a rule of an undeclared family, a
    # manifest that does not parse and a stray rule file
    files = _demo(("ARC001-a.md", "ARC001", "a"), ("ZZZ001-z.md", "ZZZ001", "z"))
    files[RULES / "demo" / "ARC002-open.md"] = "<!-- wio\ncode = "
    files[RULES / "bad" / "ruleset.toml"] = "[x"
    files[RULES / "ARC001-stray.md"] = _rule("ARC001", "stray")

    # When the discovery runs with each listing order
    forward = _find(_Listing(dict(files)))
    backward = _find(_Listing(dict(files), reverse=True))

    # Then both give the same rulesets and diagnostics, in sorted order
    assert forward == backward
    assert forward.diagnostics == sort_diagnostics(forward.diagnostics)
    assert len(forward.diagnostics) == 4


def test_a_discovery_with_an_error_is_refused_and_one_with_a_warning_is_not() -> None:
    """AC-9: the refusal carries the errors and not the warnings."""
    # Given a discovery with an error and a warning, and one with a warning only
    error = Diagnostic("error", f"{_REL}/demo/ARC001-a.md:1", "does not close")
    warning = Diagnostic("warning", f"{_REL}/demo/ruleset.toml#family", "unknown key")
    both = Discovery((), (error, warning))
    only = Discovery((), (warning,))

    # When each is refused or accepted
    with pytest.raises(DiagnosticsError) as refused:
        refuse_on_errors(both)
    refuse_on_errors(only)

    # Then the first raised an error that carries the error and not the warning
    assert refused.value.diagnostics == (error,)
