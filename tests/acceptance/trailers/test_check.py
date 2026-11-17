# SPDX-License-Identifier: Apache-2.0
"""Scenarios of `wio trailers check`, the check of a record by the time it is made.

The scenarios use the project of `test_command.py`: a git repository whose config
declares the stages `architecture` and `architecture-review`, and a Work `k3m9xq`
whose `deliver` lists them. They run on the CLI channel only, because the commit-time
mode reads the index and `HEAD`, which the in-process channel has no repository for.
"""

from typing import TYPE_CHECKING

import pytest

from tests.acceptance.channels import Channel

if TYPE_CHECKING:
    from tests.acceptance.dsl.wio import Wio

FIXTURE = "trailers/command"
RECORD = "Wio-Work: k3m9xq\nWio-Action: deliver\nWio-Stage: {stage}"


def _project(wio: Wio) -> None:
    """Start from the project, committed, so that the Work is in `HEAD`.

    Args:
        wio: The facade.
    """
    wio.fixture(FIXTURE)
    wio.commit("feat: add the Work")


def _message(wio: Wio, text: str) -> None:
    """Write a commit message file.

    Args:
        wio: The facade.
        text: The message.
    """
    wio.put("msg.txt", text.encode())


@pytest.mark.channels(Channel.CLI)
def test_the_same_record_is_judged_by_the_time_of_the_check(wio: Wio) -> None:
    """AC-1: a stage the config lacks is an error at commit time, a warning later."""
    # Given a message whose well-formed record is of a Work that exists and has
    # `Wio-Stage: nosuch`
    _project(wio)
    _message(wio, f"feat: add x\n\n{RECORD.format(stage='nosuch')}\n")

    # When `wio trailers check --require` reads it, and then `wio trailers check`
    # reads it
    required = wio.run(["trailers", "check", "--require", "msg.txt"])
    later = wio.run(["trailers", "check", "msg.txt"])

    # Then the first exits 1 and names the stage, and the second exits 0 and warns
    # about the same stage
    assert required.exit_code == 1
    assert "error: 5:" in required.stderr
    assert "nosuch" in required.stderr
    assert later.exit_code == 0
    assert "warning: 5:" in later.stderr
    assert "nosuch" in later.stderr


@pytest.mark.channels(Channel.CLI)
def test_a_record_is_required_by_the_time_of_the_check(wio: Wio) -> None:
    """AC-2: a message needs a record at commit time unless git wrote its subject."""
    # Given a message with the subject `feat: add x` and no record, and another with
    # the subject `Merge branch x` and no record
    _project(wio)
    wio.put("plain.txt", b"feat: add x\n")
    wio.put("merge.txt", b"Merge branch x\n")

    # When `wio trailers check --require` reads each, and then `wio trailers check`
    # reads the first
    plain = wio.run(["trailers", "check", "--require", "plain.txt"])
    merge = wio.run(["trailers", "check", "--require", "merge.txt"])
    later = wio.run(["trailers", "check", "plain.txt"])

    # Then the first exits 1 and the second exits 0 with `--require`, and the plain
    # check of the first exits 0
    assert plain.exit_code == 1
    assert merge.exit_code == 0
    assert later.exit_code == 0


@pytest.mark.channels(Channel.CLI)
def test_a_range_tolerates_what_the_config_no_longer_has(wio: Wio) -> None:
    """AC-3: a commit with a stage the config lacks passes a range check."""
    # Given a range with a commit whose well-formed record has `Wio-Stage: nosuch`
    _project(wio)
    wio.put("note.txt", b"x\n")
    wio.commit(f"feat: add x\n\n{RECORD.format(stage='nosuch')}")

    # When `wio trailers check --ref-range` reads the range
    output = wio.run(["trailers", "check", "--ref-range", "HEAD~1..HEAD"])

    # Then the command exits 0 and warns about the stage
    assert output.exit_code == 0
    assert "warning:" in output.stderr
    assert "nosuch" in output.stderr


@pytest.mark.channels(Channel.CLI)
def test_a_record_the_reader_cannot_see_is_reported(wio: Wio) -> None:
    """AC-4: a `Wio-` line in a paragraph with prose is an error, then a warning."""
    # Given a message with a `Wio-Work` line in a paragraph that also holds a prose
    # line, read by the `scan` reader
    _project(wio)
    _message(wio, "feat: add x\n\nWio-Work: k3m9xq\nFixes the login bug\n")

    # When `wio trailers check --require` reads it, and then when `wio trailers
    # check` reads it
    required = wio.run(["trailers", "check", "--require", "msg.txt"])
    later = wio.run(["trailers", "check", "msg.txt"])

    # Then the first exits 1 and the second exits 0 with a warning, and both name
    # that line
    assert required.exit_code == 1
    assert "error: 3:" in required.stderr
    assert later.exit_code == 0
    assert "warning: 3:" in later.stderr
