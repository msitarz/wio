# SPDX-License-Identifier: Apache-2.0
"""Tests of the reader and the shape check of records in `wio.formats`.

Each test is one criterion of the Work that builds them. They fail with
`NotImplementedError` until the implementation stage, which removes the marker.
"""

import pytest

from wio.formats import check_shape, read

PENDING = pytest.mark.xfail(
    raises=NotImplementedError, strict=True, reason="implementation stage"
)
R = "Wio-Work: k3m9xq\nWio-Action: deliver\nWio-Stage: architecture"


def _kinds(message: str) -> list[tuple[str, str | None]]:
    """List the kind and key of each finding of a message read by `scan`.

    Args:
        message: The commit message.

    Returns:
        A pair for each finding, in order.
    """
    return [(f.kind, f.key) for f in check_shape(message, "scan")]


@PENDING
@pytest.mark.parametrize(
    "message",
    [
        R,
        f"{R}\nWio-Items: AC-1, AC-3\nWio-Result: pass\nWio-Judge: human",
        "Wio-Work: none",
        R.replace("k3m9xq", "k3m9xq, a7b2c4"),
        R.replace("k3m9xq", "PROJ-12"),
        "feat: x\n\nno record here",
        "feat: x\n\n```\n" + R + "\n```",
    ],
    ids=["R", "full", "none", "list", "A-1", "no-record", "fenced"],
)
def test_a_valid_message_has_no_finding(message: str) -> None:
    """AC-1: valid records of every form, no record and a fenced example."""
    # Given a valid message
    # When `check_shape` reads it with the `scan` reader
    findings = check_shape(message, "scan")

    # Then it returns no finding
    assert findings == []


@PENDING
@pytest.mark.parametrize(
    "message",
    [
        R.replace("k3m9xq", "k3 m9xq"),
        R.replace("k3m9xq", "none, k3m9xq"),
        R.replace("k3m9xq", "k3m9xq, k3m9xq"),
        "Wio-Action: deliver\nWio-Stage: architecture",
    ],
    ids=["space", "none-in-list", "repeated", "no-work"],
)
def test_the_work_value_is_judged(message: str) -> None:
    """AC-2: an invalid id, an invalid list and a record with no Work."""
    # Given a record whose `Wio-Work` is wrong
    # When `check_shape` reads it
    findings = check_shape(message, "scan")

    # Then it returns one `malformed` finding with the key `Wio-Work` and the
    # first line, which holds the value or opens the record
    assert [(f.kind, f.key, f.number) for f in findings] == [
        ("malformed", "Wio-Work", 1)
    ]


@PENDING
@pytest.mark.parametrize(
    ("message", "key"),
    [
        (R.replace("\nWio-Stage: architecture", ""), "Wio-Stage"),
        ("Wio-Work: none\nWio-Stage: architecture", "Wio-Stage"),
        (f"{R}\nWio-Stage: wiring", "Wio-Stage"),
        (f"{R}\nWio-Judge: human", "Wio-Judge"),
    ],
    ids=["missing", "forbidden", "repeated", "judge-without-result"],
)
def test_the_other_keys_are_judged(message: str, key: str) -> None:
    """AC-3: a missing, forbidden or repeated key and a lone judge."""
    # Given a record with a fault in a key other than `Wio-Work`
    # When `check_shape` reads it
    kinds = _kinds(message)

    # Then it returns one `malformed` finding with that key
    assert kinds == [("malformed", key)]


@PENDING
def test_a_repeated_key_is_found_at_its_second_line() -> None:
    """AC-3: the finding names the line of the second `Wio-Stage`."""
    # Given R with a second `Wio-Stage: wiring` line, the fourth of the message
    message = f"{R}\nWio-Stage: wiring"

    # When `check_shape` reads it with the `scan` reader
    findings = check_shape(message, "scan")

    # Then it returns one `malformed` finding with the key `Wio-Stage` and line 4
    assert [(f.kind, f.key, f.number) for f in findings] == [
        ("malformed", "Wio-Stage", 4)
    ]


@PENDING
@pytest.mark.parametrize(
    ("message", "key"),
    [
        (R.replace("architecture", "Bad Stage"), "Wio-Stage"),
        (R.replace("deliver", "Deliver"), "Wio-Action"),
        (f"{R}\nWio-Result: Pass", "Wio-Result"),
        (f"{R}\nWio-Result: pass\nWio-Judge: robot", "Wio-Judge"),
        (f"{R}\nWio-Items: AC-1,AC-3", "Wio-Items"),
    ],
    ids=["stage", "action", "result", "judge", "items"],
)
def test_a_value_of_the_wrong_form_is_malformed(message: str, key: str) -> None:
    """AC-4: a name, a judge and items of the wrong form."""
    # Given a record with a value of the wrong form
    # When `check_shape` reads it with the `scan` reader
    kinds = _kinds(message)

    # Then it returns one `malformed` finding with that key
    assert kinds == [("malformed", key)]


@PENDING
@pytest.mark.parametrize(
    "message",
    [
        R.replace("architecture", "nosuch"),
        f"{R}\nWio-Result: maybe\nWio-Judge: agent",
    ],
    ids=["stage", "result"],
)
def test_a_name_the_config_may_not_list_is_not_judged(message: str) -> None:
    """AC-4: the modes check the config, so the shape check finds nothing."""
    # Given a record with a well-formed name or result the config may not list
    # When `check_shape` reads it with the `scan` reader
    findings = check_shape(message, "scan")

    # Then it returns no finding
    assert findings == []


@PENDING
def test_an_unknown_key_is_a_finding_of_its_own() -> None:
    """AC-5: `Wio-Criteria` is `unknown-key`, and a `none` record also breaks."""
    # Given R with a `Wio-Criteria` line, and `Wio-Work: none` with the same line
    line = "Wio-Criteria: AC-1"

    # When `check_shape` reads each with the `scan` reader
    plain = _kinds(f"{R}\n{line}")
    none = _kinds(f"Wio-Work: none\n{line}")

    # Then the first gives one `unknown-key` finding, and the second also a
    # `malformed` finding for the forbidden key
    assert plain == [("unknown-key", "Wio-Criteria")]
    assert none[0] == ("unknown-key", "Wio-Criteria")
    assert none[1][0] == "malformed"
    assert len(none) == 2


@PENDING
def test_a_line_in_a_paragraph_with_prose_is_invisible_under_scan() -> None:
    """AC-6: each `Wio-` line of a paragraph that also holds prose is found."""
    # Given a paragraph that holds R and the prose line `Fixes the login bug`
    message = f"{R}\nFixes the login bug"

    # When `check_shape` reads it with the `scan` reader
    kinds = _kinds(message)

    # Then it returns one `invisible` finding for each of the three `Wio-` lines
    assert [kind for kind, _ in kinds] == ["invisible"] * 3


@PENDING
def test_a_record_before_the_last_paragraph_is_invisible_under_git() -> None:
    """AC-6: R followed by another record is not seen, the last one is."""
    # Given R, a blank line, and a second record that git sees as the last
    last = R.replace("k3m9xq", "a7b2c4")
    message = f"{R}\n\n{last}"

    # When `check_shape` reads it with the `git` reader
    findings = check_shape(message, "git")

    # Then it returns one `invisible` finding for each `Wio-` line of R, and
    # none for the last paragraph
    assert [f.kind for f in findings] == ["invisible"] * 3
    assert [f.number for f in findings] == [1, 2, 3]


@PENDING
def test_findings_say_what_is_wrong_and_where() -> None:
    """AC-7: line numbers, non-empty messages and the order of the message."""
    # Given a subject, a body paragraph and R with bad items and an unknown key
    message = f"fix: x\n\nbody\n\n{R}\nWio-Items: AC-1,AC-3\nWio-Criteria: AC-1"

    # When `check_shape` reads it with the `scan` reader
    findings = check_shape(message, "scan")

    # Then the `malformed` finding comes before the `unknown-key` one, each with
    # its 1-based line number and a non-empty message
    assert [(f.kind, f.number) for f in findings] == [
        ("malformed", 8),
        ("unknown-key", 9),
    ]
    assert all(f.message for f in findings)


@PENDING
def test_the_scan_reader_decides_what_is_a_record() -> None:
    """AC-8: only the middle record is read, with no rejected line."""
    # Given R in the middle, another in a fenced block and a `# Wio-Work` line
    other = R.replace("k3m9xq", "a7b2c4")
    message = f"feat: x\n\n{R}\n\n```\n{other}\n```\n\n# Wio-Work: zzzzzz"

    # When `read` reads it with the `scan` reader
    reading = read(message, "scan")

    # Then the `Reading` holds R alone with line numbers and no rejected line
    assert len(reading.records) == 1
    assert [t.number for t in reading.records[0].trailers] == [3, 4, 5]
    assert reading.rejected == ()


@PENDING
def test_the_git_reader_decides_what_is_a_record() -> None:
    """AC-8: R before a `Co-authored-by` paragraph is rejected, not read."""
    # Given R, a blank line and a `Co-authored-by` paragraph
    message = f"{R}\n\nCo-authored-by: A <a@example.com>"

    # When `read` reads it with the `git` reader
    reading = read(message, "git")

    # Then the `Reading` holds no record and the three `Wio-` lines of R as
    # rejected lines
    assert reading.records == ()
    assert [t.number for t in reading.rejected] == [1, 2, 3]
