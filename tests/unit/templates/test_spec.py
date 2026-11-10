# SPDX-License-Identifier: Apache-2.0
"""Tests of the arguments of `wio templates`, as `describe()` declares them."""

from argparse import ArgumentParser

import pytest

from wio.templates import describe


def _parser() -> ArgumentParser:
    """Build the parser of `wio templates` as `wio.cli` does.

    Returns:
        The parser that `describe().configure` set up.
    """
    parser = ArgumentParser(prog="wio templates")
    describe().configure(parser)
    return parser


def test_list_reads_its_kind_and_its_json_flag() -> None:
    """AC-5: `list --kind feature --json` sets the view, the kind and the flag."""
    # Given the parser of `wio templates`
    parser = _parser()

    # When `list` is parsed with a kind and with `--json`, and with neither
    full = parser.parse_args(["list", "--kind", "feature", "--json"])
    plain = parser.parse_args(["list"])

    # Then the first carries all three and the second the defaults
    assert (full.templates_view, full.kind, full.json) == ("list", "feature", True)
    assert (plain.templates_view, plain.kind, plain.json) == ("list", None, False)


def test_bare_templates_has_no_view_and_a_help_that_names_list() -> None:
    """AC-4: no subcommand leaves the view empty and gives the usage."""
    # Given the parser of `wio templates`
    parser = _parser()

    # When nothing is parsed
    args = parser.parse_args([])

    # Then there is no view, and the help names `list`
    assert args.templates_view is None
    assert "list" in args.templates_help()


def test_show_reads_one_name() -> None:
    """AC-4: `show feature.leaf` sets the view and the name, and takes no option."""
    # Given the parser of `wio templates`
    parser = _parser()

    # When `show` is parsed with a name
    args = parser.parse_args(["show", "feature.leaf"])

    # Then the view is `show` and the name is the one given
    assert (args.templates_view, args.name) == ("show", "feature.leaf")


@pytest.mark.parametrize(
    "argv",
    [["show"], ["show", "a", "b"], ["show", "feature.leaf", "--json"]],
    ids=["no-name", "two-names", "json"],
)
def test_show_with_a_wrong_command_line_is_a_usage_mistake(argv: list[str]) -> None:
    """AC-4: no name, two names and `--json` exit 2 with a usage message."""
    # Given the parser of `wio templates`
    parser = _parser()

    # When a wrong command line is parsed
    with pytest.raises(SystemExit) as caught:
        parser.parse_args(argv)

    # Then the parser exits with the code of a usage mistake
    assert caught.value.code == 2


def test_the_help_of_templates_names_show() -> None:
    """AC-4: the usage of `wio templates` lists `show`."""
    # Given the parser of `wio templates`
    parser = _parser()

    # When its help is formatted
    help_text = parser.format_help()

    # Then it names `show`
    assert "show" in help_text


@pytest.mark.parametrize(
    ("argv", "as_json"),
    [(["directives"], False), (["directives", "--json"], True)],
    ids=["text", "json"],
)
def test_directives_reads_only_its_json_flag(argv: list[str], *, as_json: bool) -> None:
    """AC-5: `directives` sets its view and the flag, and takes nothing else."""
    # Given the parser of `wio templates`
    parser = _parser()

    # When `directives` is parsed, with and without `--json`
    args = parser.parse_args(argv)

    # Then the view is `directives` and the flag is as given
    assert (args.templates_view, args.json) == ("directives", as_json)


def test_directives_with_another_argument_is_a_usage_mistake() -> None:
    """AC-5: `directives extra` exits 2 with a usage message."""
    # Given the parser of `wio templates`
    parser = _parser()

    # When `directives` is parsed with an extra argument
    with pytest.raises(SystemExit) as caught:
        parser.parse_args(["directives", "extra"])

    # Then the parser exits with the code of a usage mistake
    assert caught.value.code == 2


def test_the_help_of_templates_names_directives() -> None:
    """AC-5: the usage of `wio templates` lists `directives`."""
    # Given the parser of `wio templates`
    parser = _parser()

    # When its help is formatted
    help_text = parser.format_help()

    # Then it names `directives`
    assert "directives" in help_text
