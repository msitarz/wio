# SPDX-License-Identifier: Apache-2.0
"""Tests of how the id and the place of a new Work are composed from leaves."""

from pathlib import Path
from typing import TYPE_CHECKING
from unittest.mock import Mock

import pytest

from tests.unit.fakes import ROOT, MemoryFileSystem
from wio.contracts import ContractsError, WorkDiscovery
from wio.contracts import location as module
from wio.models.config import Works as WorksSettings
from wio.models.frozen import freeze
from wio.models.works import Work

if TYPE_CHECKING:
    from collections.abc import Sequence

NONE = WorkDiscovery((), (), (), (), (), ())


def _work(work_id: str) -> Work:
    """Build a Work with an id.

    Args:
        work_id: The Work's id.

    Returns:
        A Work at `<id>/README.md`.
    """
    return Work(
        id=work_id,
        title=None,
        path=Path(work_id) / "README.md",
        template=None,
        roots=(),
        depends_on=(),
        actions=freeze({}),
    )


class _Draws:
    """An `IdGenerator` that gives prepared ids and counts its draws."""

    def __init__(self, ids: Sequence[str]) -> None:
        """Keep the ids to give, the last one on every draw after them.

        Args:
            ids: The candidates, in order.
        """
        self.ids = list(ids)
        self.calls = 0

    def draw(self) -> str:
        """Give the next candidate.

        Returns:
            The next prepared id, or the last when none is left.
        """
        self.calls += 1
        return self.ids.pop(0) if len(self.ids) > 1 else self.ids[0]


def _arguments(**given: str | None) -> module.NameArguments:
    """Build the options of `new`.

    Args:
        **given: The options that were typed.

    Returns:
        The arguments, with the others not given.
    """
    options: dict[str, str | None] = {
        "slug": None,
        "title": None,
        "path": None,
        "parent": None,
    }
    options.update(given)
    return module.NameArguments(**options)


def test_a_place_is_decided_by_the_leaves_in_the_order_of_the_errors(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The options, the slug, the place and the existing files are judged in turn."""
    # Given leaves that record their calls and a title alone
    calls: list[str] = []
    place = Path(".agents/wio/works/child/README.md")

    def record(name: str, result: object = None) -> Mock:
        """Make a leaf that records its name when it is called.

        Args:
            name: What to record.
            result: What the leaf gives.

        Returns:
            The mock.
        """

        def leaf(*_args: object, **_kwargs: object) -> object:
            """Record the call and give the result.

            Args:
                *_args: The arguments, which are not read.
                **_kwargs: The keyword arguments, which are not read.

            Returns:
                The prepared result.
            """
            calls.append(name)
            return result

        return Mock(side_effect=leaf)

    monkeypatch.setattr(module, "_check_options", record("options"))
    monkeypatch.setattr(module, "choose_slug", record("slug", "child"))
    default = record("place", place)
    monkeypatch.setattr(module, "_default_place", default)
    taken = record("existing")
    monkeypatch.setattr(module, "_refuse_existing", taken)
    settings = WorksSettings(hierarchy="nesting")
    disk = MemoryFileSystem()
    arguments = _arguments(title="Child")

    # When the place is decided
    found = module.decide_place(ROOT, settings, NONE, disk, arguments)

    # Then the leaves ran in that order, the slug and the options reached the
    # place, the directory of the place was refused when it exists, and the
    # place is the one the leaf gave
    assert calls == ["options", "slug", "place", "existing"]
    assert found == place
    assert default.call_args.args == (settings, NONE, arguments, "child")
    assert taken.call_args.args == (ROOT, place, disk)
    assert taken.call_args.kwargs == {"whole_directory": True}


def test_a_given_path_skips_the_slug_and_refuses_only_the_file(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A `--path` is judged as it is and only its own file must not exist."""
    # Given leaves for a call with `--path`
    monkeypatch.setattr(module, "_check_options", Mock())
    slug = Mock()
    monkeypatch.setattr(module, "choose_slug", slug)
    place = Path(".agents/wio/works/q/spec.md")
    judge = Mock(return_value=place)
    monkeypatch.setattr(module, "_checked_path", judge)
    taken = Mock()
    monkeypatch.setattr(module, "_refuse_existing", taken)
    settings = WorksSettings(hierarchy="flat")
    disk = MemoryFileSystem()

    # When the place is decided
    found = module.decide_place(
        ROOT, settings, NONE, disk, _arguments(path="q/spec.md")
    )

    # Then no slug was chosen, the path was judged with everything it needs,
    # and only the file was refused
    assert found == place
    slug.assert_not_called()
    assert judge.call_args.args == (ROOT, settings, NONE, disk, "q/spec.md")
    assert taken.call_args.kwargs == {"whole_directory": False}


def test_the_default_place_is_below_the_works_directory_or_the_parent(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A parent moves the directory of the place, and no parent is looked up
    without one."""
    # Given a leaf that finds the directory of a parent
    find = Mock(return_value=Path("p"))
    monkeypatch.setattr(module, "_parent_directory", find)
    settings = WorksSettings(dir=".agents/wio/works")

    # When the default place is decided without and with a parent
    top = module._default_place(settings, NONE, _arguments(), "child")  # noqa: SLF001
    below = module._default_place(  # noqa: SLF001
        settings, NONE, _arguments(parent="p5n2hv"), "child"
    )

    # Then the first is in the Works directory without a lookup, and the second
    # is below the directory that the lookup gave
    assert top == Path(".agents/wio/works/child/README.md")
    assert below == Path("p/child/README.md")
    assert find.call_args_list[0].args == (NONE, "p5n2hv")
    assert find.call_count == 1


def test_an_id_is_drawn_until_no_work_has_it() -> None:
    """A taken candidate, a shared one included, is drawn again."""
    # Given a tree where `aaaaaa` is shared by two Works and `bbbbbb` is taken
    works = [_work("aaaaaa"), _work("aaaaaa"), _work("bbbbbb")]
    draws = _Draws(["aaaaaa", "bbbbbb", "cccccc"])

    # When an id is drawn
    found = module.new_id(draws, works)

    # Then the first free candidate is returned after three draws
    assert found == "cccccc"
    assert draws.calls == 3


def test_the_draw_gives_up_after_the_limit() -> None:
    """A tree that holds every candidate ends in an error after 100 draws."""
    # Given a tree that holds the one id the generator gives
    draws = _Draws(["aaaaaa"])

    # When an id is drawn
    with pytest.raises(ContractsError) as raised:
        module.new_id(draws, [_work("aaaaaa")])

    # Then the generator was asked exactly 100 times
    assert draws.calls == 100
    assert "100" in str(raised.value)


def test_the_guard_writes_a_free_path_and_refuses_one_that_exists() -> None:
    """A new file is written with its directories, and an old one is kept."""
    # Given a file system that holds one contract
    old = Path(".agents/wio/works/old/spec.md")
    disk = MemoryFileSystem({ROOT / old: "kept"})
    new = Path(".agents/wio/works/new/spec.md")

    # When a contract is written to the free path and to the old one
    module.write_new(disk, ROOT, new, "fresh")
    with pytest.raises(ContractsError) as raised:
        module.write_new(disk, ROOT, old, "lost")

    # Then the new file has the text, the old file is unchanged and the error
    # names it
    assert disk.files[ROOT / new] == "fresh"
    assert disk.files[ROOT / old] == "kept"
    assert old.as_posix() in str(raised.value)
