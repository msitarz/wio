# SPDX-License-Identifier: Apache-2.0
"""Check and collect the `Wio-*` trailer records of this repository's commits.

This is a stand-in for `wio trailers check` until that command exists. It reads
records the way the `scan` reader does: a record is a paragraph in which every
line is a `Key: value` trailer and some key starts with `Wio-`, outside fenced
code blocks. It checks only the shape of a record, not whether its Work, stage
or criteria exist.

Commands:

- `check FILE`: check one commit message (the commit-msg hook).
- `commits RANGE`: check the commits in a revision range (CI).
- `body RANGE`: read a pull request body on standard input and print it with the
  records of the range's commits at its end, after the revert lines of commits
  that revert work outside the range, or nothing when it already has them
  (CI).
"""

import argparse
import re
import subprocess
import sys
from pathlib import Path
lazy from collections.abc import Sequence

type Record = tuple[tuple[str, str], ...]
type Commit = tuple[str, str]  # (sha, message)

TRAILER = re.compile(r"^(?P<key>[A-Za-z0-9][A-Za-z0-9-]*): (?P<value>\S.*)$")
FENCE = re.compile(r"^\s*(```|~~~)")
WORK_ID = re.compile(r"^[0-9a-hjkmnp-tv-z]{6,8}$")  # lowercase Crockford base32
CRITERIA = re.compile(r"^AC-\d+(, AC-\d+)*$")
NAME = re.compile(r"^[a-z0-9][a-z0-9-]*$")
RESULT = re.compile(r"^(pass|fail|unknown)$")
KEYS = frozenset({"Wio-Work", "Wio-Action", "Wio-Stage", "Wio-Criteria", "Wio-Result"})
SKIPPED_SUBJECTS = ("Merge ", "Revert ", "fixup! ", "squash! ", "amend! ")
REVERT_LINE = re.compile(r"^This reverts commit [0-9a-f]{7,40}\.?$")
REVERTS = re.compile(r"^This reverts commit (?P<sha>[0-9a-f]{7,40})\b", re.MULTILINE)
NO_WORK = "none"
FORMATS = (
    ("Wio-Work", WORK_ID, "is not a Work id"),
    ("Wio-Action", NAME, "is not a name"),
    ("Wio-Stage", NAME, "is not a name"),
    ("Wio-Criteria", CRITERIA, "must look like `AC-1, AC-3`"),
    ("Wio-Result", RESULT, "must be one of pass, fail, unknown"),
)


def _kept_lines(message: str) -> list[str | None]:
    """List a message's lines, with `None` for every line that is left out.

    Blank lines, comment lines and fenced code are left out, so each `None`
    ends a paragraph.

    Args:
        message: A commit message or a pull request body.

    Returns:
        One entry per line of the message.
    """
    kept: list[str | None] = []
    in_fence = False
    for line in message.replace("\r\n", "\n").split("\n"):
        is_fence = FENCE.match(line) is not None
        in_fence = in_fence != is_fence
        dropped = is_fence or in_fence or line.startswith("#") or not line.strip()
        kept.append(None if dropped else line)
    return kept


def paragraphs(message: str) -> list[list[str]]:
    """Split a message into paragraphs, leaving out comments and fenced code.

    Args:
        message: A commit message or a pull request body.

    Returns:
        The paragraphs in order, each as its list of lines.
    """
    result: list[list[str]] = [[]]
    for line in _kept_lines(message):
        if line is None:
            result.append([])
        else:
            result[-1].append(line)
    return [paragraph for paragraph in result if paragraph]


def as_record(paragraph: list[str]) -> Record | None:
    """Read a paragraph as a record.

    Args:
        paragraph: The lines of one paragraph.

    Returns:
        The paragraph's fields, or `None` when it is not a record.
    """
    matches = [TRAILER.match(line) for line in paragraph]
    fields = tuple((m["key"], m["value"]) for m in matches if m is not None)
    if len(fields) != len(paragraph):
        return None
    if not any(key.startswith("Wio-") for key, _ in fields):
        return None
    return fields


def records(message: str) -> list[Record]:
    """Find every record in a message.

    Args:
        message: A commit message or a pull request body.

    Returns:
        The records in the order they appear.
    """
    found = (as_record(paragraph) for paragraph in paragraphs(message))
    return [record for record in found if record is not None]


def _key_problems(keys: list[str]) -> list[str]:
    """Report unknown and repeated `Wio-*` keys in one record.

    Args:
        keys: The record's `Wio-*` keys, in order.

    Returns:
        One message per problem.
    """
    unknown = [f"unknown trailer {key}" for key in keys if key not in KEYS]
    repeated = [
        f"{key} appears more than once in one record"
        for key in sorted(set(keys))
        if keys.count(key) > 1
    ]
    return unknown + repeated


def _work_problems(values: dict[str, str]) -> list[str]:
    """Report problems of a record that names a Work.

    Args:
        values: The record's `Wio-*` fields.

    Returns:
        One message per problem.
    """
    required = ("Wio-Action", "Wio-Stage")
    missing = [f"{key} is missing" for key in required if key not in values]
    malformed = [
        f"{key} {values[key]!r} {message}"
        for key, pattern, message in FORMATS
        if key in values and not pattern.match(values[key])
    ]
    return missing + malformed


def _value_problems(values: dict[str, str]) -> list[str]:
    """Report problems of a record's values.

    Args:
        values: The record's `Wio-*` fields.

    Returns:
        One message per problem.
    """
    match values.get("Wio-Work"):
        case None:
            return ["Wio-Work is missing"]
        case work if work == NO_WORK:
            return [
                f"{key} is not allowed when Wio-Work is {NO_WORK}"
                for key in sorted(values)
                if key != "Wio-Work"
            ]
        case _:
            return _work_problems(values)


def record_problems(record: Record) -> list[str]:
    """Check the shape of one record.

    Args:
        record: The fields of one record.

    Returns:
        One message per problem, empty when the record is valid.
    """
    fields = [(key, value) for key, value in record if key.startswith("Wio-")]
    keys = [key for key, _ in fields]
    return _key_problems(keys) + _value_problems(dict(fields))


def message_problems(message: str) -> list[str]:
    """Check every record of a commit message.

    Merge and revert commits, and commits made to be squashed into another
    one, need no record.

    Args:
        message: A commit message.

    Returns:
        One message per problem, empty when the message is valid.
    """
    if message.lstrip().startswith(SKIPPED_SUBJECTS):
        return []
    found = records(message)
    if not found:
        return [f"no Wio-* record; add one, or `Wio-Work: {NO_WORK}`"]
    return [problem for record in found for problem in record_problems(record)]


def render(record: Record) -> str:
    """Render the `Wio-*` fields of a record as one paragraph.

    Args:
        record: The fields of one record.

    Returns:
        The trailer lines, joined by newlines.
    """
    return "\n".join(f"{key}: {value}" for key, value in record if key in KEYS)


def _kept(commits: Sequence[Commit]) -> list[Commit]:
    """Leave out the commits that a later commit in the list reverts.

    A revert undoes the work its records named, so neither keeps a record. A
    revert of a revert restores the original commit.

    Args:
        commits: Commits as (sha, message), oldest first.

    Returns:
        The commits that still count, oldest first.
    """
    dropped: set[str] = set()
    kept: list[Commit] = []
    for sha, message in reversed(commits):
        if any(sha.startswith(reverted) for reverted in dropped):
            continue
        dropped.update(match["sha"] for match in REVERTS.finditer(message))
        kept.append((sha, message))
    return kept[::-1]


def collect(commits: Sequence[Commit]) -> list[str]:
    """Collect the records of several commits that name a Work.

    Records of commits reverted later in the list are left out.

    Args:
        commits: Commits as (sha, message), oldest first.

    Returns:
        The rendered records, in commit order.
    """
    return [
        render(record)
        for _, message in _kept(commits)
        for record in records(message)
        if dict(record).get("Wio-Work") != NO_WORK
    ]


def outside_reverts(commits: Sequence[Commit]) -> list[str]:
    """List the revert lines of commits that revert work outside the list.

    A squash merge drops the commits' messages, so these lines are copied into
    the pull request body, where a reader still sees which earlier commit the
    merged change reverts.

    Args:
        commits: Commits as (sha, message), oldest first.

    Returns:
        One `This reverts commit <sha>.` line per such revert, in commit order.
    """
    shas = [sha for sha, _ in commits]
    return [
        f"This reverts commit {match['sha']}."
        for _, message in _kept(commits)
        for match in REVERTS.finditer(message)
        if not any(sha.startswith(match["sha"]) for sha in shas)
    ]


def _is_managed(block: str) -> bool:
    """Tell whether a body paragraph is one this script writes.

    Args:
        block: One paragraph of a pull request body.

    Returns:
        True for a record and for a paragraph of revert lines.
    """
    lines = block.strip().split("\n")
    is_reverts = all(REVERT_LINE.match(line) for line in lines)
    return is_reverts or as_record(lines) is not None


def with_records(
    body: str, rendered: Sequence[str], reverts: Sequence[str] = ()
) -> str:
    """Replace the records and revert lines at the end of a pull request body.

    Args:
        body: The current body.
        rendered: The records to put at its end.
        reverts: Revert lines to put before the records, as one paragraph.

    Returns:
        The body without its trailing managed paragraphs, followed by the
        revert lines and `rendered`.
    """
    blocks = body.replace("\r\n", "\n").strip().split("\n\n")
    while blocks and _is_managed(blocks[-1]):
        blocks.pop()
    extra = ["\n".join(reverts)] if reverts else []
    return "\n\n".join([*blocks, *extra, *rendered]).strip() + "\n"


def commits_in(revision_range: str) -> list[Commit]:
    """Read the commits in a revision range.

    Args:
        revision_range: A range such as `main..HEAD`.

    Returns:
        The commits as (sha, message), oldest first.
    """
    output = subprocess.run(
        ["git", "log", "--reverse", "--format=%H%n%B%x00", revision_range],
        capture_output=True,
        check=True,
        text=True,
    ).stdout
    entries = (entry.strip() for entry in output.split("\0"))
    pairs = (entry.partition("\n") for entry in entries if entry)
    return [(sha, message.strip()) for sha, _, message in pairs]


def _report(label: str, problems: list[str]) -> None:
    """Write the problems of one message to standard error.

    Args:
        label: What the problems belong to.
        problems: The messages to write.
    """
    for problem in problems:
        sys.stderr.write(f"{label}: {problem}\n")


def _check(path: str) -> int:
    """Check one commit message file.

    Args:
        path: The file that holds the message.

    Returns:
        The exit code: 0 when valid, 1 otherwise.
    """
    problems = message_problems(Path(path).read_text(encoding="utf-8"))
    _report(path, problems)
    return 1 if problems else 0


def _commit_problems(message: str) -> list[str]:
    """Check one commit of a range, warning when it has no record.

    A commit without a record is only a warning here, because commits made
    in GitHub's web interface skip the commit-msg hook.

    Args:
        message: The commit message.

    Returns:
        One message per malformed field.
    """
    found = records(message)
    if not found and not message.startswith(SKIPPED_SUBJECTS):
        subject = message.split("\n", 1)[0]
        sys.stderr.write(f"warning: {subject}: no Wio-* record\n")
    return [problem for record in found for problem in record_problems(record)]


def _commits(revision_range: str) -> int:
    """Check the commits in a revision range.

    Args:
        revision_range: A range such as `main..HEAD`.

    Returns:
        The exit code: 0 when every record is valid, 1 otherwise.
    """
    failed = False
    for _, message in commits_in(revision_range):
        problems = _commit_problems(message)
        _report(message.split("\n", 1)[0], problems)
        failed = failed or bool(problems)
    return 1 if failed else 0


def _body(revision_range: str) -> int:
    """Print the pull request body from standard input with the range's records.

    Nothing is printed when the body already ends with exactly those records,
    so the caller edits the pull request only when something changed.

    Args:
        revision_range: A range such as `main..HEAD`.

    Returns:
        The exit code, always 0.
    """
    body = sys.stdin.read()
    commits = commits_in(revision_range)
    updated = with_records(body, collect(commits), outside_reverts(commits))
    if updated.strip() != body.replace("\r\n", "\n").strip():
        sys.stdout.write(updated)
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    """Run one command.

    Args:
        argv: The arguments, without the program name.

    Returns:
        The exit code.
    """
    parser = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("check").add_argument("path")
    commands.add_parser("commits").add_argument("revision_range")
    commands.add_parser("body").add_argument("revision_range")
    arguments = parser.parse_args(argv)
    match arguments.command:
        case "check":
            return _check(arguments.path)
        case "commits":
            return _commits(arguments.revision_range)
        case _:
            return _body(arguments.revision_range)


if __name__ == "__main__":
    sys.exit(main())
