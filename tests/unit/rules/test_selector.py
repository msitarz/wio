# SPDX-License-Identifier: Apache-2.0
"""Tests of the selector that gives `wio context` and `wio trailers` their rules."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, override

import pytest

from tests.unit.fakes import ROOT, FakeRepository, MemoryFileSystem
from wio.errors import DiagnosticsError, WioError
from wio.formats import rule_hash
from wio.models.config import Config, Root, Stage
from wio.models.frozen import freeze
from wio.models.resolved import ResolvedContract
from wio.models.works import Work
from wio.rules import RuleSelector, discover, ruleset_map, select

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence

    from wio.models.rules import Selection

_RULES = ROOT / ".agents" / "wio" / "rules"
_ARC1 = _RULES / "demo" / "ARC001-keep.md"
_ARC2 = _RULES / "demo" / "ARC002-name.md"
_WEB1 = _RULES / "web" / "WEB001-page.md"
_ARC1_TEXT = '<!-- wio\r\ncode = "ARC001"\r\nname = "keep"\r\n-->\r\n\r\nKeep.\r\n'


def _rule(code: str, name: str) -> str:
    """Write a rule file.

    Args:
        code: The `code` key.
        name: The `name` key.

    Returns:
        The text of a marked rule file.
    """
    return f'<!-- wio\ncode = "{code}"\nname = "{name}"\n-->\n\nBody.\n'


def _files(*, reverse: bool = False) -> dict[Path, str]:
    """Build the rule files of the repository of AC-1 of the selection.

    Args:
        reverse: Whether to insert them in the opposite order.

    Returns:
        The files by path: `demo` with `ARC001` and `ARC002`, and `web` with
        `WEB001`.
    """
    pairs = [
        (_RULES / "demo" / "ruleset.toml", '[families]\nARC = "Topic"\n'),
        (_ARC1, _ARC1_TEXT),
        (_ARC2, _rule("ARC002", "name")),
        (_RULES / "web" / "ruleset.toml", '[families]\nWEB = "Topic"\n'),
        (_WEB1, _rule("WEB001", "page")),
    ]
    return dict(reversed(pairs) if reverse else pairs)


def _config(*, reverse: bool = False) -> Config:
    """Build the config of the repository: two roots and two stages.

    Args:
        reverse: Whether to write its tables in the opposite order.

    Returns:
        The config, where `api` reaches `demo`, `web` reaches `web`, the stage `s`
        has no `roots` and excludes `demo.ARC002`, and the stage `w` selects the
        root `web` only.
    """
    roots = [
        ("api", Root(("src",), ("demo.all",))),
        ("web", Root(("w",), ("web.all",))),
    ]
    stages = [
        (
            "s",
            Stage(
                goal="g", rules_include=("web.WEB001",), rules_exclude=("demo.ARC002",)
            ),
        ),
        ("w", Stage(goal="g", roots=("web",))),
    ]
    return Config(
        roots=freeze(dict(reversed(roots) if reverse else roots)),
        stages=freeze(dict(reversed(stages) if reverse else stages)),
    )


@dataclass
class _Settings:
    """Settings that give one config."""

    config: Config

    def load(self) -> Config:
        """Give the config.

        Returns:
            The config.
        """
        return self.config


@dataclass
class _Roots:
    """The roots of the Works, by id."""

    roots: Mapping[str, tuple[str, ...]]

    def roots_of(self, work_id: str) -> tuple[str, ...] | None:
        """Find the roots of a Work.

        Args:
            work_id: The Work's id.

        Returns:
            Its roots, or `None` for an id that no Work has.
        """
        return self.roots.get(work_id)


@dataclass
class _Disk(MemoryFileSystem):
    """A file system that records the reads of bytes and can refuse some."""

    read: list[Path] = field(default_factory=list)
    unreadable: set[Path] = field(default_factory=set)
    reverse: bool = False

    @override
    def list_dir(self, path: Path) -> Sequence[Path]:
        """List a directory, reversed when asked.

        Args:
            path: The directory.

        Returns:
            The entries, in the stored order or the opposite one.
        """
        entries = super().list_dir(path)
        return list(reversed(entries)) if self.reverse else entries

    @override
    def read_bytes(self, path: Path) -> bytes:
        """Read bytes, and record the read.

        Args:
            path: The file.

        Returns:
            Its bytes.

        Raises:
            OSError: The file is one of `unreadable`.
        """
        self.read.append(path)
        if path in self.unreadable:
            raise OSError(path)
        return super().read_bytes(path)


def _selector(
    disk: MemoryFileSystem | None = None, config: Config | None = None
) -> RuleSelector:
    """Build the selector over the repository of the examples.

    Args:
        disk: The files, `_files()` by default.
        config: The config, `_config()` by default.

    Returns:
        A selector whose Work `w1` has the root `api` and whose Work `bare` has
        none.
    """
    return RuleSelector(
        _Settings(config or _config()),
        FakeRepository(),
        disk or MemoryFileSystem(_files()),
        _Roots({"w1": ("api",), "bare": ()}),
    )


def _contract(work_id: str) -> ResolvedContract:
    """Build the resolved contract of a Work.

    Args:
        work_id: The Work's id.

    Returns:
        A contract with no text.
    """
    work = Work(work_id, None, Path("w.md"), None, (), (), freeze({}))
    return ResolvedContract(work, "", ())


def _outs(selection: Selection) -> set[str]:
    """Collect the reasons that the rules of a selection are out.

    Args:
        selection: The selection.

    Returns:
        The kind of each reason, and `included` for a rule that is in.
    """
    return {
        d.reason.kind if d.reason and not d.included else "included"
        for d in selection.values()
    }


def _expected(roots: tuple[str, ...], stage: str, disk: MemoryFileSystem) -> Selection:
    """Compute the selection that `select` gives for the roots.

    Args:
        roots: The roots to apply.
        stage: The stage.
        disk: The files.

    Returns:
        The selection of `select` over the discovery of the files.
    """
    found = discover(ROOT, disk)
    return select(roots, stage, _config(), ruleset_map(found))


def test_the_selector_gives_the_selection_of_the_roots_of_the_stage() -> None:
    """AC-1: `selection` and `select` equal `select` for the roots that count."""
    # Given the repository, a Work in `api`, a stage with no `roots` and one with
    # `roots = ["web"]`
    disk = MemoryFileSystem(_files())
    selector = _selector(disk)

    # When `selection` and `select` run for each stage
    found = {
        stage: (
            selector.selection("w1", stage),
            selector.select(_contract("w1"), stage),
        )
        for stage in ("s", "w")
    }

    # Then each equals `select` for the roots `("api",)` and `("web",)`
    assert found["s"] == (_expected(("api",), "s", disk),) * 2
    assert found["w"] == (_expected(("web",), "w", disk),) * 2


def test_selected_gives_the_hash_of_each_included_rule_only() -> None:
    """AC-2: the code and hash of `ARC001`, no other rule, no other read."""
    # Given a stage that includes `demo.ARC001` with CRLF line endings, excludes
    # `demo.ARC002` and cuts `web.WEB001`, and a disk that records its reads
    disk = _Disk(_files())
    selector = _selector(disk)

    # When `selected` runs for two actions, then the file is edited and it runs
    first = selector.selected("w1", "deliver", "s")
    second = selector.selected("w1", "define", "s")
    disk.files[_ARC1] = _ARC1_TEXT + "More.\r\n"
    third = selector.selected("w1", "deliver", "s")

    # Then only `demo.ARC001` is given with the hash of its bytes, the same for
    # both actions, no other file was read as bytes, and an edit changes the hash
    assert first == {"demo.ARC001": rule_hash(_ARC1_TEXT.encode())}
    assert second == first
    assert set(disk.read) == {_ARC1}
    assert third["demo.ARC001"] != first["demo.ARC001"]


def test_a_fault_in_the_rules_is_a_refusal_for_every_method() -> None:
    """AC-4: two rules with one code raise and return nothing."""
    # Given a ruleset with two rules that share the code `ARC001`
    files = _files()
    files[_RULES / "demo" / "ARC001-other.md"] = _rule("ARC001", "other")
    selector = _selector(MemoryFileSystem(files))

    # When `selection`, `select` and `selected` run
    calls = (
        lambda: selector.selection("w1", "s"),
        lambda: selector.select(_contract("w1"), "s"),
        lambda: selector.selected("w1", "deliver", "s"),
    )

    # Then each raises the error that names both files
    for call in calls:
        with pytest.raises(DiagnosticsError) as raised:
            call()
        assert "ARC001-keep.md" in str(raised.value)
        assert "ARC001-other.md" in str(raised.value)


def test_unknown_names_are_refused_in_the_form_of_each_port() -> None:
    """AC-5: `KeyError` for the context methods, `WioError` for `selected`."""
    # Given an unknown stage and an unknown Work id
    selector = _selector()

    # When each method runs for each
    # Then `selection` and `select` raise `KeyError`, and `selected` raises a
    # `WioError` that is no `KeyError`
    for work, stage in (("w1", "nope"), ("nope", "s")):
        with pytest.raises(KeyError):
            selector.selection(work, stage)
        with pytest.raises(KeyError):
            selector.select(_contract(work), stage)
        with pytest.raises(WioError) as raised:
            selector.selected(work, "deliver", stage)
        assert not isinstance(raised.value, KeyError)
        assert "nope" in str(raised.value)


def test_the_result_does_not_depend_on_the_order_of_the_inputs() -> None:
    """AC-6: the same selections and mappings for two orders of the inputs."""
    # Given the repository in two orders of its files, of their listing and of
    # its config tables
    forward = _selector(_Disk(_files()), _config())
    backward = _selector(
        _Disk(_files(reverse=True), reverse=True), _config(reverse=True)
    )

    # When `selection` and `selected` run on each
    # Then the selections are equal and the mappings are equal
    assert forward.selection("w1", "s") == backward.selection("w1", "s")
    assert forward.selected("w1", "deliver", "s") == backward.selected(
        "w1", "deliver", "s"
    )


def test_a_work_without_roots_gets_no_included_rule() -> None:
    """AC-7: an empty mapping, and every rule out as `not-selected`."""
    # Given a Work with no roots and a stage with no `roots`
    selector = _selector()

    # When `selected`, `selection` and `select` run
    mapping = selector.selected("bare", "deliver", "s")
    chosen = (selector.selection("bare", "s"), selector.select(_contract("bare"), "s"))

    # Then the mapping is empty, and each selection has every rule out for the
    # reason `not-selected`, and nothing is raised
    assert mapping == {}
    for selection in chosen:
        assert len(selection) == 3
        assert _outs(selection) == {"not-selected"}


def test_a_rule_file_that_cannot_be_read_is_a_refusal() -> None:
    """AC-8: a `WioError` that names the file, and no `OSError`."""
    # Given a selection that includes `demo.ARC001`, whose bytes cannot be read
    disk = _Disk(_files(), unreadable={_ARC1})
    selector = _selector(disk)

    # When `selected` runs
    # Then it raises a `WioError` that names the file
    with pytest.raises(WioError) as raised:
        selector.selected("w1", "deliver", "s")
    assert "ARC001-keep.md" in str(raised.value)
