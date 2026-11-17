# SPDX-License-Identifier: Apache-2.0
"""Tests of the later check of `wio trailers`, run with fakes of its ports.

The examples use a body B of the line `Fix the bug.`, a blank line and R, the
paragraph `Wio-Work: k3m9xq`, `Wio-Action: deliver` and `Wio-Stage: architecture`, so
that R's lines are 3 to 5. A range has the commits `c1`, `c2` and `c3` from the
oldest, each of the message B. The config's results are `pass`, `fail` and `unknown`,
and its reader is `scan` unless a scenario says otherwise. The tests fail with
`NotImplementedError` until the implementation stage, which removes the marker,
except those that argparse or the wired dispatch answer.
"""

import io
from argparse import ArgumentParser
from dataclasses import dataclass, replace
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from tests.unit.fakes import FakeStdio
from tests.unit.trailers.test_check import services
from tests.unit.trailers.test_fold import FakeHistory, _commit, _id
from tests.unit.trailers.test_validation import CONFIG
from wio.models.config import Config, Trailers
from wio.trailers.check import configure_check, run_check
from wio.trailers.errors import TrailersError

if TYPE_CHECKING:
    from wio.models.commits import Commit

PENDING = pytest.mark.xfail(
    raises=NotImplementedError, strict=True, reason="implementation stage"
)
R = "Wio-Work: k3m9xq\nWio-Action: deliver\nWio-Stage: architecture"
B = f"Fix the bug.\n\n{R}"
GIT_CONFIG = replace(CONFIG, trailers=Trailers(reader="git"))


@dataclass(frozen=True)
class LostHistory:
    """A `History` port whose working directory is not in a repository."""

    def history(self, revision_range: str) -> tuple[Commit, ...]:
        """Refuse every range.

        Args:
            revision_range: The range.

        Raises:
            RuntimeError: Always.
        """
        message = f"not inside a git repository ({revision_range})"
        raise RuntimeError(message)


def _run(
    argv: list[str],
    *,
    body: str = "",
    files: dict[Path, str] | None = None,
    commits: tuple[Commit, ...] = (),
    history: object | None = None,
    config: Config = CONFIG,
) -> tuple[int, str]:
    """Run the check form on arguments, with a body on standard input.

    Args:
        argv: The arguments after `wio trailers check`.
        body: What standard input holds.
        files: The files of the file system, by path.
        commits: The commits of the range `a..b`.
        history: The `History` port, or `None` for one that holds `commits`.
        config: The config the settings load.

    Returns:
        The exit code and what was written to standard error.
    """
    parser = ArgumentParser(prog="wio trailers check")
    configure_check(parser)
    args = parser.parse_args(argv)
    out, err = io.StringIO(), io.StringIO()
    ports = services(config, history=history or FakeHistory(commits), files=files)
    code = run_check(ports, args, FakeStdio(io.StringIO(body), out, err))
    assert out.getvalue() == ""
    return code, err.getvalue()


@PENDING
def test_a_body_from_a_file_and_from_standard_input_gives_one_diagnostic() -> None:
    """AC-1: the same `error: 3:` line from a file, `-` and no path."""
    # Given B with `Wio-Work: k3 m9xq`, in a file and on standard input
    bad = B.replace("k3m9xq", "k3 m9xq")
    files: dict[Path, str] = {Path("body.txt"): bad}

    # When `check <file>`, `check -` and `check` read it
    results = [
        _run(["body.txt"], files=files),
        _run(["-"], body=bad),
        _run([], body=bad),
    ]

    # Then each exits 1 and prints the same diagnostic, which begins `error: 3:`
    assert results[0] == results[1] == results[2]
    assert results[0][0] == 1
    assert results[0][1].startswith("error: 3:")


@PENDING
def test_a_file_that_does_not_exist_is_a_usage_error() -> None:
    """AC-1: a path that cannot be read raises `TrailersError`."""
    # Given a path that does not exist
    # When `check <path>` runs
    # Then it raises a `TrailersError`, which exits 2
    with pytest.raises(TrailersError):
        _run(["nope.txt"])


@PENDING
def test_a_path_with_a_range_is_a_usage_error() -> None:
    """AC-1 and A-2: the two read different inputs."""
    # Given a call that gives a path and `--ref-range`
    # When `check <path> --ref-range main..HEAD` runs
    # Then it raises a `TrailersError`
    with pytest.raises(TrailersError):
        _run(["body.txt", "--ref-range", "a..b"])


@PENDING
def test_a_range_that_does_not_resolve_is_a_usage_error() -> None:
    """AC-1: `nosuch..nosuch2` is refused by the port with a `ValueError`."""
    # Given a range `nosuch..nosuch2`
    # When `check --ref-range nosuch..nosuch2` runs
    # Then it raises a `TrailersError`
    with pytest.raises(TrailersError):
        _run(["--ref-range", "nosuch..nosuch2"])


@PENDING
def test_a_directory_that_is_not_in_a_repository_is_a_usage_error() -> None:
    """AC-1: the port's `RuntimeError` is a usage error."""
    # Given a directory that is not in a repository
    # When `check --ref-range main..HEAD` runs in it
    # Then it raises a `TrailersError`
    with pytest.raises(TrailersError):
        _run(["--ref-range", "main..HEAD"], history=LostHistory())


@PENDING
def test_a_malformed_record_fails_a_body_and_a_range() -> None:
    """AC-2: `error: 3:` for the body, `error: <id of c2>:3:` for the range."""
    # Given B with `Wio-Work: k3 m9xq`, and a range whose `c2` has that message while
    # `c1` and `c3` are valid and `c3` also has an unknown name
    bad = B.replace("k3m9xq", "k3 m9xq")
    odd = f"Fix the bug.\n\n{R.replace('architecture', 'nosuch')}"
    commits = (
        _commit(1, B.split("\n\n", 1)[1]),
        _commit(2, bad.split("\n\n", 1)[1]),
        _commit(3, odd.split("\n\n", 1)[1]),
    )

    # When `check` reads the body and `--ref-range` reads the range
    body = _run([], body=bad)
    ranged = _run(["--ref-range", "a..b"], commits=commits)

    # Then each exits 1, the body's diagnostic begins `error: 3:`, the range's begins
    # `error:` followed by the full id of `c2` and `:3:`, and `c1` and `c3` add no
    # error
    assert body[0] == ranged[0] == 1
    assert body[1].startswith("error: 3:")
    assert ranged[1].startswith(f"error: {_id(2)}:3:")
    assert ranged[1].count("error:") == 1


@PENDING
@pytest.mark.parametrize(
    ("record", "name"),
    [
        (R.replace("architecture", "nosuch"), "nosuch"),
        (R.replace("deliver", "nosuch"), "nosuch"),
        (
            R.replace("architecture", "architecture-review") + "\nWio-Result: maybe",
            "maybe",
        ),
    ],
    ids=["stage", "action", "result"],
)
def test_a_name_the_config_no_longer_has_is_a_warning(record: str, name: str) -> None:
    """AC-3: `nosuch`, `nosuch` and `maybe` are warned about, never refused."""
    # Given B with a name the config does not have
    # When `check` reads it
    code, err = _run([], body=f"Fix the bug.\n\n{record}")

    # Then it exits 0 and prints a `warning:` that names the name
    assert code == 0
    assert err.startswith("warning:")
    assert name in err


@PENDING
def test_a_work_that_was_deleted_is_not_looked_up() -> None:
    """AC-3: `d4e5f6` and `AC-99` print nothing."""
    # Given B with `Wio-Work: d4e5f6`, which is in no tree, and `Wio-Items: AC-99`
    body = f"{B.replace('k3m9xq', 'd4e5f6')}\nWio-Items: AC-99"

    # When `check` reads it
    code, err = _run([], body=body)

    # Then it exits 0 and prints nothing
    assert (code, err) == (0, "")


@PENDING
def test_a_line_the_reader_cannot_see_is_a_warning() -> None:
    """AC-4: prose in the paragraph under `scan`, a second paragraph under `git`."""
    # Given B whose paragraph also holds the prose line `Fixes the login bug`, with
    # the `scan` reader, and the range commit `c2` of that message with the `git`
    # reader and a blank line and a `Co-authored-by` paragraph after R
    prose = f"Fix the bug.\n\n{R}\nFixes the login bug"
    commit = _commit(2, f"{R}\n\nCo-authored-by: A <a@example.com>")

    # When `check` reads the body and `--ref-range` reads the range
    body = _run([], body=prose)
    ranged = _run(["--ref-range", "a..b"], commits=(commit,), config=GIT_CONFIG)

    # Then each exits 0 and prints a `warning:` for each `Wio-` line that the reader
    # cannot see, at its line
    assert body[0] == ranged[0] == 0
    assert [line.split(":")[1] for line in body[1].splitlines()] == ["3", "4", "5"]
    assert ranged[1].count("warning:") == 3
    assert all(
        line.startswith(f"warning: {_id(2)}:") for line in ranged[1].splitlines()
    )


@PENDING
def test_a_name_the_engine_does_not_define_is_a_warning() -> None:
    """AC-4: `warning: 6:` names `Wio-Criteria`."""
    # Given B with a `Wio-Criteria: AC-1` line as line 6 of R's paragraph
    # When `check` reads it
    code, err = _run([], body=f"{B}\nWio-Criteria: AC-1")

    # Then it exits 0 and prints a `warning: 6:` that names `Wio-Criteria`
    assert code == 0
    assert err.startswith("warning: 6:")
    assert "Wio-Criteria" in err


@PENDING
@pytest.mark.parametrize("what", ["body", "commit", "empty"])
def test_no_record_is_not_a_failure(what: str) -> None:
    """AC-5: a body, a commit and an empty range print nothing."""
    # Given a body of `Fix the bug.` alone, a range of one commit with that message,
    # and a range of no commit
    # When `check` reads the body and `--ref-range` reads each range
    runs = {
        "body": _run([], body="Fix the bug."),
        "commit": _run(["--ref-range", "a..b"], commits=(_commit(1),)),
        "empty": _run(["--ref-range", "a..b"], commits=()),
    }

    # Then each exits 0 and prints nothing
    assert runs[what] == (0, "")
