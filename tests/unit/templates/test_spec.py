# SPDX-License-Identifier: Apache-2.0
"""Tests of the arguments of `wio templates`, as `describe()` declares them."""

from argparse import ArgumentParser

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
