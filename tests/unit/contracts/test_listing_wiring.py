# SPDX-License-Identifier: Apache-2.0
"""Tests of how the listing of Works is composed from its leaves."""

from argparse import ArgumentParser, Namespace
from typing import TYPE_CHECKING, cast
from unittest.mock import Mock

import pytest

from tests.unit.contracts.helpers import work_with_id
from tests.unit.fakes import FakeRepository, FakeStdio, MemoryFileSystem
from wio.contracts import ContractsError, Services, describe
from wio.contracts import listing as module
from wio.contracts.hierarchy import build_hierarchy
from wio.models.config import Config, Works

if TYPE_CHECKING:
    import io

    from wio.contracts.hierarchy import Hierarchy
    from wio.models.works import Work


class _Settings:
    """A `Settings` that gives a config."""

    def __init__(self, config: Config) -> None:
        """Keep the config to give.

        Args:
            config: The settings.
        """
        self._config = config

    def load(self) -> Config:
        """Give the config.

        Returns:
            The settings.
        """
        return self._config


def _hierarchy(*works: Work) -> Hierarchy:
    """Build the hierarchy of Works under `flat`, so that none has a relative.

    Args:
        *works: The Works.

    Returns:
        The hierarchy.
    """
    return build_hierarchy(works, "flat")


def _first_and_second(work: Work, *_rest: object) -> list[str]:
    """Lay out a block as the first line of the Work and a second line.

    Args:
        work: The Work.
        *_rest: The depth, the width and the titles, which are not read.

    Returns:
        Two lines.
    """
    return [f"first {work.id}", "second"]


def _id_object(work: Work, _found: Hierarchy) -> dict[str, object]:
    """Make the object of a Work out of its id alone.

    Args:
        work: The Work.
        _found: The hierarchy, which is not read.

    Returns:
        An object with the id.
    """
    return {"id": work.id}


def test_the_text_is_assembled_from_the_leaves(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The order, the width and the titles reach the block of each Work."""
    # Given Works and leaves that give their order, with a depth, and a block
    a, bb = work_with_id("a"), work_with_id("bbbb")
    found = _hierarchy(a, bb)
    monkeypatch.setattr(module, "_text_order", Mock(return_value=[(bb, 0), (a, 1)]))
    block = Mock(side_effect=_first_and_second)
    monkeypatch.setattr(module, "_block", block)

    # When the Works are rendered as text
    text = module.render_list(found, as_json=False)

    # Then the lines of each block are in the order that the leaf gave, each
    # ended by a newline, and each block got the depth, the widest id and the
    # titles of all the Works
    assert text == "first bbbb\nsecond\nfirst a\nsecond\n"
    assert [c.args[1:3] for c in block.call_args_list] == [(0, 4), (1, 4)]
    assert block.call_args.args[3] == {"a": None, "bbbb": None}


def test_the_json_is_one_line_of_the_objects_in_the_order_of_the_works(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Each Work becomes the object that the leaf makes of it."""
    # Given two Works and a leaf that makes an object of each
    a, b = work_with_id("a"), work_with_id("b")
    found = _hierarchy(a, b)
    monkeypatch.setattr(module, "_as_object", Mock(side_effect=_id_object))

    # When the Works are rendered as JSON
    text = module.render_list(found, as_json=True)

    # Then it is one array on one line, in the order of the Works
    assert text == '[{"id": "a"}, {"id": "b"}]\n'


def _written(stdio: FakeStdio) -> str:
    """Read what was written to standard output.

    Args:
        stdio: The streams.

    Returns:
        The text.
    """
    return cast("io.StringIO", stdio.stdout).getvalue()


def _services(config: Config | None = None) -> Services:
    """Build the services of a project with no Work.

    Args:
        config: The settings, or the defaults.

    Returns:
        Services over a file system that holds nothing.
    """
    return Services(
        _Settings(config or Config()),
        FakeRepository(),
        MemoryFileSystem(),
        Mock(),
    )


def test_the_command_refuses_before_it_builds_or_prints(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """An incomplete tree writes nothing and reaches no later leaf."""
    # Given a refusal and a renderer that must not run
    refuse = Mock(side_effect=ContractsError("incomplete"))
    monkeypatch.setattr(module, "_refuse_incomplete", refuse)
    render = Mock()
    monkeypatch.setattr(module, "render_list", render)
    stdio = FakeStdio()

    # When the command runs
    with pytest.raises(ContractsError):
        module.run_list(_services(), Namespace(json=False), stdio)

    # Then nothing was rendered or written, and the leaf got what discovery found
    render.assert_not_called()
    assert _written(stdio) == ""
    assert refuse.call_args.args[0].works == ()


def test_the_command_builds_the_hierarchy_of_the_config_and_prints_it(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The mode of the config and `--json` reach the renderer."""
    # Given a project under `nesting`, which is not the default, a leaf that
    # accepts the tree and a renderer
    monkeypatch.setattr(module, "_refuse_incomplete", Mock())
    build = Mock(return_value="the hierarchy")
    monkeypatch.setattr(module, "build_hierarchy", build)
    render = Mock(return_value="listing\n")
    monkeypatch.setattr(module, "render_list", render)
    services = _services(Config(works=Works(hierarchy="nesting")))
    stdio = FakeStdio()

    # When the command runs with `--json`
    code = module.run_list(services, Namespace(json=True), stdio)

    # Then the hierarchy was built for `nesting`, rendered as JSON and written, and
    # the exit code is 0
    assert build.call_args.args[1] == "nesting"
    render.assert_called_once_with("the hierarchy", as_json=True)
    assert _written(stdio) == "listing\n"
    assert code == 0


def test_the_group_has_a_list_subcommand_with_a_json_option() -> None:
    """`wio contracts list --json` is parsed into the entry of the table."""
    # Given the parser of the group
    parser = ArgumentParser()
    describe().configure(parser)

    # When `list` is parsed with and without `--json`
    plain = parser.parse_args(["list"])
    as_json = parser.parse_args(["list", "--json"])

    # Then both choose `list`, and only the second asks for JSON
    assert (plain.contracts_subcommand, plain.json) == ("list", False)
    assert (as_json.contracts_subcommand, as_json.json) == ("list", True)
