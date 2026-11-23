# SPDX-License-Identifier: Apache-2.0
"""Tests of the roots that count for a stage and the roots that hold a file."""

from pathlib import PurePosixPath
from typing import TYPE_CHECKING

import pytest

from wio.models.config import Config, Root, Stage
from wio.models.frozen import freeze
from wio.rules import roots_of_path, stage_roots

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence


class _Works:
    """A `WorkRoots` over a table of Works and their roots."""

    def __init__(self, roots: Mapping[str, tuple[str, ...]]) -> None:
        """Hold the table.

        Args:
            roots: The roots of each Work by id.
        """
        self._roots = roots

    def roots_of(self, work_id: str) -> tuple[str, ...] | None:
        """Find the roots of a Work.

        Args:
            work_id: The Work's id.

        Returns:
            The roots, or `None` for an id that is not in the table.
        """
        return self._roots.get(work_id)


def _stages(
    *forms: tuple[str, Sequence[str] | None],
) -> Config:
    """Build a config with the root `contract` and the stages given.

    Args:
        *forms: A stage's name with its `roots`, `None` when it sets none.

    Returns:
        The config.
    """
    stages = {
        name: Stage(goal="g", roots=None if roots is None else tuple(roots))
        for name, roots in forms
    }
    return Config(
        roots=freeze({"contract": Root(("contracts",)), "api": Root(("src/api",))}),
        stages=freeze(stages),
    )


_FOUR: tuple[tuple[str, Sequence[str] | None], ...] = (
    ("plain", None),
    ("only", ["contract"]),
    ("both", ["contract", "@work"]),
    ("none", []),
)


def _each(config: Config, roots: tuple[str, ...]) -> list[tuple[str, ...] | str]:
    """Run `stage_roots` for the four stages of AC-4 on a Work.

    Args:
        config: The config with the four stages.
        roots: The Work's roots.

    Returns:
        The result for each stage, or the message of its `ValueError`.
    """
    works = _Works({"w": roots})
    found: list[tuple[str, ...] | str] = []
    for name, _ in _FOUR:
        try:
            found.append(stage_roots(config, name, "w", works))
        except ValueError as error:
            found.append(str(error))
    return found


def test_the_stage_decides_which_roots_count() -> None:
    """AC-4: no `roots` is the Work's, `@work` adds them, `[]` selects none."""
    # Given a Work with the root `api` and stages of the four forms
    config = _stages(*_FOUR)

    # When the roots of each stage are found
    found = _each(config, ("api",))

    # Then each form gives its roots
    assert found == [("api",), ("contract",), ("api", "contract"), ()]


def test_a_work_without_roots_fails_where_a_stage_needs_them() -> None:
    """AC-4: the stage that selects the Work's roots raises `ValueError`."""
    # Given a Work with no roots and stages of the four forms
    config = _stages(*_FOUR)

    # When the roots of each stage are found
    found = _each(config, ())

    # Then the stages that select the Work's roots say it has none
    assert "no roots" in str(found[0])
    assert found[1] == ("contract",)
    assert "no roots" in str(found[2])
    assert found[3] == ()


def test_no_stage_selects_the_roots_of_the_work() -> None:
    """AC-4: with no stage the roots are the Work's, and none is an error."""
    # Given a Work with roots and a Work without
    config = _stages(*_FOUR)
    works = _Works({"has": ("api",), "bare": ()})

    # When the roots are found for each with no stage
    found = stage_roots(config, None, "has", works)
    with pytest.raises(ValueError, match="no roots"):
        stage_roots(config, None, "bare", works)

    # Then the first gives the roots and the second raised
    assert found == ("api",)


def test_a_name_that_does_not_exist_is_refused() -> None:
    """AC-5: each unknown name raises `KeyError` that names it."""
    # Given a Work whose root is not in the config, a stage with no `roots` and a
    # stage with a root that is not in the config
    config = _stages(("plain", None), ("bad", ["missing"]))
    works = _Works({"w": ("nope",)})

    # When the roots are found for each unknown name
    cases = [("none", "w"), ("plain", "none"), ("plain", "w"), ("bad", "w")]
    named: list[str] = []
    for stage, work in cases:
        with pytest.raises(KeyError) as raised:
            stage_roots(config, stage, work, works)
        named.append(raised.value.args[0])

    # Then each error names what was not found
    assert named == ["none", "none", "nope", "missing"]


def _paths() -> Config:
    """Build the config of the overlapping roots of AC-6.

    Returns:
        The config.
    """
    return Config(
        roots=freeze(
            {
                "api": Root(("src/api",)),
                "api2": Root(("src/api2",)),
                "web": Root(("src/web",)),
                "repo": Root((".",)),
            }
        )
    )


def test_every_root_that_contains_a_file_is_found_by_whole_components() -> None:
    """AC-6: a root holds its path and what lies under it, and not a prefix."""
    # Given overlapping roots, one of which is the repository
    config = _paths()

    # When the roots of four paths are found
    given = ["src/api/app.py", "src/api2/x.py", "docs/readme.md", "src/api"]
    found = [roots_of_path(config, PurePosixPath(p)) for p in given]

    # Then a prefix of a component does not match, and the whole repository does
    assert found == [("api", "repo"), ("api2", "repo"), ("repo",), ("api", "repo")]


def test_a_file_in_no_root_has_no_roots() -> None:
    """AC-6: a path outside every root gives an empty tuple."""
    # Given roots that do not hold the path
    config = Config(
        roots=freeze({"api": Root(("src/api",)), "web": Root(("src/web",))})
    )

    # When the roots of a documentation file are found
    found = roots_of_path(config, PurePosixPath("docs/readme.md"))

    # Then there are none
    assert found == ()


def test_the_roots_do_not_depend_on_the_order_of_the_inputs() -> None:
    """AC-7: two orders of the config give equal results."""
    # Given the stages of AC-4 and the roots of AC-6 in two orders
    forward = _stages(*_FOUR)
    backward = _stages(*reversed(_FOUR))
    swapped = Config(roots=freeze(dict(reversed(_paths().roots.items()))))
    spread = Config(roots=freeze({"web": Root(("src/web", "src/api"))}))
    other = Config(roots=freeze({"web": Root(("src/api", "src/web"))}))
    reordered = _stages(("both", ["@work", "contract"]))

    # When the functions run on each, with a fake for the port
    one = _each(forward, ("api",)), roots_of_path(_paths(), PurePosixPath("src/api"))
    two = _each(backward, ("api",)), roots_of_path(swapped, PurePosixPath("src/api"))
    both = stage_roots(reordered, "both", "w", _Works({"w": ("api",)}))

    # Then the results are equal
    assert sorted(map(str, one[0])) == sorted(map(str, two[0]))
    assert one[1] == two[1]
    assert roots_of_path(spread, PurePosixPath("src/api/x")) == roots_of_path(
        other, PurePosixPath("src/api/x")
    )
    assert both == ("api", "contract")
