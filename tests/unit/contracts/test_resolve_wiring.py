# SPDX-License-Identifier: Apache-2.0
"""Tests of how the resolved view of a Work is composed from its leaves."""

from pathlib import Path
from typing import TYPE_CHECKING
from unittest.mock import Mock

import pytest

from tests.unit.fakes import ROOT, MemoryFileSystem
from wio.contracts import resolve as module
from wio.models.frozen import freeze
from wio.models.resolved import InheritedSections, ResolvedContract
from wio.models.works import Work

if TYPE_CHECKING:
    from wio.contracts.ports import TemplateCatalog


def _work(name: str) -> Work:
    """Build a Work for a directory.

    Args:
        name: The directory's name, which is also the Work's id.

    Returns:
        A Work at `<name>/README.md`.
    """
    return Work(
        id=name,
        title=name,
        path=Path(name) / "README.md",
        template=None,
        roots=(),
        depends_on=(),
        actions=freeze({}),
    )


def _files(*works: Work) -> MemoryFileSystem:
    """Give each Work a file.

    Args:
        works: The Works.

    Returns:
        A file system holding `text of <id>` at each Work's file.
    """
    return MemoryFileSystem({ROOT / w.path: f"text of {w.id}" for w in works})


def test_the_view_is_composed_from_the_leaves_nearest_ancestor_first(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The own contract and each ancestor that passes anything become one value."""
    # Given a Work and two ancestors, and leaves that give an own contract, a
    # marked set, sections and a title for each
    child, near, far = _work("c"), _work("n"), _work("f")
    files = _files(child, near, far)
    own = Mock(return_value="own")
    monkeypatch.setattr(module, "_own_contract", own)
    marked = Mock(return_value=frozenset({"constraints"}))
    monkeypatch.setattr(module, "_marked_texts", marked)

    def cut(text: str, _: frozenset[str]) -> tuple[str, tuple[str, ...]]:
        return text, (f"section of {text}",)

    monkeypatch.setattr(module, "_cut_ancestor", cut)
    catalog: TemplateCatalog = Mock()

    # When the Work is resolved
    resolved = module.resolve_work(child, (near, far), catalog, ROOT, files)

    # Then the leaves got the Work's file and each ancestor's, and the value holds
    # the own contract and the ancestors in the order given
    assert own.call_args.args == ("text of c",)
    assert marked.call_args_list[0].args == (near, "text of n", catalog, ROOT, files)
    assert resolved == ResolvedContract(
        child,
        "own",
        (
            InheritedSections(near, "text of n", ("section of text of n",)),
            InheritedSections(far, "text of f", ("section of text of f",)),
        ),
    )


def test_an_ancestor_that_passes_nothing_is_left_out_and_stops_nothing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """An unreadable file, an unusable source and no section each pass nothing."""
    # Given ancestors whose file fails, whose source is unusable, that mark
    # nothing, and one that passes, with leaves that give no own contract
    child = _work("c")
    broken, unusable, empty, good = (_work(n) for n in ("b", "u", "e", "g"))
    files = _files(child, unusable, empty, good)
    files.broken[ROOT / broken.path] = UnicodeDecodeError("utf-8", b"", 0, 1, "bad")
    monkeypatch.setattr(module, "_own_contract", Mock(return_value=""))

    def marked(ancestor: Work, *_: object) -> frozenset[str] | None:
        return None if ancestor is unusable else frozenset({"x"})

    monkeypatch.setattr(module, "_marked_texts", marked)

    def cut(text: str, _: frozenset[str]) -> tuple[str, tuple[str, ...]]:
        return ("G", ("s",)) if text == "text of g" else ("", ())

    monkeypatch.setattr(module, "_cut_ancestor", cut)

    # When the Work is resolved
    resolved = module.resolve_work(
        child, (broken, unusable, empty, good), Mock(), ROOT, files
    )

    # Then only the ancestor that passes is in the value, and nothing was raised
    assert resolved.inherited == (InheritedSections(good, "G", ("s",)),)


def test_the_works_own_file_that_cannot_be_read_is_raised() -> None:
    """A failure of the Work's own read reaches the caller."""
    # Given a Work whose file raises an OSError
    child = _work("c")
    files = MemoryFileSystem(failure=PermissionError("no"))

    # When the Work is resolved
    # Then the OSError is raised
    with pytest.raises(PermissionError):
        module.resolve_work(child, (), Mock(), ROOT, files)


@pytest.mark.parametrize(
    ("own", "inherited", "expected"),
    [
        (
            "own",
            (("T", ("a", "b")), ("U", ("c",))),
            (
                "own\n\n## Inherited from: T (t)\n\na\n\nb\n\n"
                "## Inherited from: U (u)\n\nc\n"
            ),
        ),
        ("", (("T", ("a",)),), "## Inherited from: T (t)\n\na\n"),
        ("own", (), "own\n"),
        ("", (), ""),
    ],
)
def test_the_text_joins_the_own_contract_and_each_part_with_one_blank_line(
    own: str,
    inherited: tuple[tuple[str, tuple[str, ...]], ...],
    expected: str,
) -> None:
    """The text is the non-empty parts, a blank line apart, with one line ending."""
    # Given an own contract and ancestors that each have a title and sections
    entries = tuple(
        InheritedSections(_work(title.lower()), title, sections)
        for title, sections in inherited
    )
    resolved = ResolvedContract(_work("c"), own, entries)

    # When the view is rendered
    text = module.render_resolved(resolved)

    # Then each ancestor's header comes before its sections, the parts are a
    # blank line apart, one line ending ends the text, and nothing gives nothing
    assert text == expected
