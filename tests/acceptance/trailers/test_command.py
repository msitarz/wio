# SPDX-License-Identifier: Apache-2.0
"""Scenarios of `wio trailers`, the command that runs its three forms.

Each test is a stub for one scenario of the Work that builds the command, and
skips until the implementation stage fills it in. The scenarios use a temporary git
repository whose config declares the gate `architecture-review`, with
`judge = "human"`, and a Work `k3m9xq` that has an item `AC-1` and a `deliver` that
lists `architecture` and `architecture-review`. `HEAD` carries a record for
`k3m9xq`. They run on the CLI channel only, because the in-process channel has no
git repository, and the implementation stage gives the facade the verb that makes
a commit.
"""

from typing import TYPE_CHECKING

import pytest

from tests.acceptance.channels import Channel

if TYPE_CHECKING:
    from tests.acceptance.dsl.wio import Wio

STUB = "filled in by the implementation stage"


@pytest.mark.channels(Channel.CLI)
def test_the_arguments_select_the_form(wio: Wio) -> None:
    """AC-1: the write form, `check` and `fold` run from the first argument."""
    # Given the repository, a commit message file with the subject `feat: add x` and
    # no record, and a pull request body. Standard input holds the message for the
    # fourth run and the body for the sixth
    # When `wio trailers k3m9xq deliver architecture`, `wio trailers check <file>`,
    # `wio trailers check --require <file>`, `wio trailers check --require -` with
    # the message on standard input, `wio trailers fold block HEAD~1..HEAD` and
    # `wio trailers fold body HEAD~1..HEAD` run
    # Then the first, the fifth and the sixth exit 0 and print the record of
    # `k3m9xq`, the folded record of `HEAD` and the body with that record at its end
    # in turn, the second exits 0 because a message without a record passes, and the
    # third and the fourth exit 1 because it has none
    del wio
    pytest.skip(STUB)


@pytest.mark.channels(Channel.CLI)
@pytest.mark.parametrize(
    "call",
    ["no argument", "unknown fold", "unknown option", "option before the Work"],
)
def test_a_usage_mistake_exits_2(wio: Wio, call: str) -> None:
    """AC-2: each call that no form accepts exits 2 and says what is wrong."""
    # Given the repository
    # When `wio trailers`, `wio trailers fold nosuch`, `wio trailers check
    # --nosuch` and the call that starts with the option `--items AC-1`, before
    # `k3m9xq deliver architecture`, run
    # Then each exits 2, prints nothing on standard output and says on standard
    # error what is wrong
    del wio
    pytest.skip(f"{STUB}: {call}")


@pytest.mark.channels(Channel.CLI)
def test_a_record_round_trips_through_the_real_adapters(wio: Wio) -> None:
    """AC-3: the printed record is checked and folded from a real commit."""
    # Given the repository, and no injected adapter
    # When `wio trailers k3m9xq deliver architecture` prints a record, a commit
    # carries it in its message, and `wio trailers check --ref-range HEAD~1..HEAD`
    # and `wio trailers fold block HEAD~1..HEAD` run
    # Then each exits 0 and the fold prints that record
    del wio
    pytest.skip(STUB)


@pytest.mark.channels(Channel.CLI)
def test_a_gate_result_with_the_no_op_sink_leaves_the_wio_home_empty(wio: Wio) -> None:
    """AC-3: the record is printed and no event file appears."""
    # Given the repository, with a work commit under a pure gate commit of
    # `architecture-review`, and an empty Wio home
    # When `wio trailers k3m9xq deliver architecture-review --result pass --judge
    # human` runs
    # Then it prints the record, exits 0 and leaves the Wio home empty
    del wio
    pytest.skip(STUB)


@pytest.mark.channels(Channel.CLI)
def test_a_cited_rule_code_is_refused_by_the_null_rules_port(wio: Wio) -> None:
    """AC-3: `docs.DOC001` is not selected by any stage, so it is refused."""
    # Given the repository, with no injected adapter
    # When `wio trailers k3m9xq deliver architecture-review --result pass --judge
    # human --cite docs.DOC001=fail` runs
    # Then it exits 1, prints an `error:` line that names `docs.DOC001` on standard
    # error and prints nothing on standard output
    del wio
    pytest.skip(STUB)


@pytest.mark.channels(Channel.CLI)
def test_the_help_lists_the_forms(wio: Wio) -> None:
    """AC-4: `wio trailers --help` lists the write form, `check` and `fold`."""
    # Given the repository
    # When `wio trailers --help` runs
    # Then it exits 0 and lists the write form, `check` and `fold`
    del wio
    pytest.skip(STUB)
