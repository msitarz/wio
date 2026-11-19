# SPDX-License-Identifier: Apache-2.0
"""Contract scenarios for harness session identification.

The scenarios cover the identification boundary through its environment and
standard-stream ports.
"""

from dataclasses import replace
from io import StringIO
from pathlib import Path
from unittest.mock import Mock, call

import pytest

from tests.fakes import FakeEnvironment
from tests.unit.fakes import FakeStdio
from wio.log.identify import SessionIdentity, identify
from wio.models.config import Harness, Log
from wio.models.frozen import freeze

_DEFAULT_LOG = Log()
_NESTED = {
    "CLAUDE_CODE_SESSION_ID": "c1",
    "CODEX_THREAD_ID": "t2",
    "CODEX_SESSION_ID": "s1",
}


def _identify(
    variables: dict[str, str], log: Log = _DEFAULT_LOG
) -> tuple[SessionIdentity, str]:
    """Exercise the entry point with in-memory ports.

    Args:
        variables: The environment variables made available to the call.
        log: The effective log settings.

    Returns:
        The identified session fields and standard error text.
    """
    stderr = StringIO()
    environment = FakeEnvironment(Path(), variables)
    identity = identify(log, environment, FakeStdio(stderr=stderr))
    return identity, stderr.getvalue()


def test_claude_code_records_its_session() -> None:
    """AC-1 identifies a Claude Code session and records its extra id.

    The built-in mapping uses the session variable and records AI_AGENT.
    """
    # Given the built-in Claude Code session and the default extra variable.
    variables = {"CLAUDE_CODE_SESSION_ID": "c1", "AI_AGENT": "claude-code_2"}

    # When the session is identified.
    identity, warnings = _identify(variables)

    # Then Claude Code is the sole match and both ids are retained.
    assert identity == SessionIdentity(
        "claude-code", "c1", None, ("claude-code",), variables
    )
    assert warnings == ""


@pytest.mark.parametrize(
    ("extra", "session", "parent"),
    [
        ({"CODEX_THREAD_ID": "s1"}, "s1", None),
        ({"CODEX_THREAD_ID": "t2"}, "t2", "s1"),
        ({}, "s1", None),
    ],
)
def test_codex_uses_thread_then_session(
    extra: dict[str, str], session: str, parent: str | None
) -> None:
    """AC-1 identifies main sessions and subagents in Codex.

    Args:
        extra: The optional thread variable.
        session: The expected session id.
        parent: The expected parent id.
    """
    # Given the main session id and an optional thread id.
    variables = {"CODEX_SESSION_ID": "s1"} | extra

    # When the session is identified.
    identity, warnings = _identify(variables)

    # Then Codex is the sole match with the applicable session and parent.
    assert identity == SessionIdentity("codex", session, parent, ("codex",), variables)
    assert warnings == ""


def test_nested_matches_stay_unresolved() -> None:
    """AC-2 retains ordered matches and ids for an ambiguous run.

    The default config leaves a nested session unresolved.
    """
    # Given both built-in harnesses and no preference.
    variables = _NESTED.copy()

    # When the session is identified.
    identity, warnings = _identify(variables)

    # Then both match in config order and the session fields are unknown.
    assert identity == SessionIdentity(
        None, None, None, ("claude-code", "codex"), variables
    )
    assert tuple(identity.ids) == tuple(_NESTED)
    assert warnings == ""


def test_ai_agent_alone_does_not_identify_a_harness() -> None:
    """AC-2 retains an extra id for a run with no known harness.

    AI_AGENT alone has no session meaning in the default config.
    """
    # Given an extra id and no configured harness session variables set.
    variables = {"AI_AGENT": "x"}

    # When the session is identified.
    identity, warnings = _identify(variables)

    # Then no harness matches and the id is still recorded.
    assert identity == SessionIdentity(None, None, None, (), variables)
    assert warnings == ""


@pytest.mark.parametrize(
    ("override", "expected", "unknown"),
    [
        (None, ("codex", "t2", "s1"), None),
        ("", ("codex", "t2", "s1"), None),
        (" ", ("codex", "t2", "s1"), None),
        (",", ("codex", "t2", "s1"), None),
        ("claude-code", ("claude-code", "c1", None), None),
        (" claude-code , ", ("claude-code", "c1", None), None),
        ("claude-code,,codex", ("claude-code", "c1", None), None),
        ("none", (None, None, None), None),
        ("none,codex", ("codex", "t2", "s1"), "none"),
        ("cursor,codex", ("codex", "t2", "s1"), "cursor"),
        ("codex,codex", ("codex", "t2", "s1"), None),
        ("CODEX", (None, None, None), "CODEX"),
    ],
)
def test_preference_resolves_nested_matches(
    override: str | None,
    expected: tuple[str | None, str | None, str | None],
    unknown: str | None,
) -> None:
    """AC-3 applies preference syntax to real matches.

    Args:
        override: The optional preference variable to set.
        expected: The selected harness, session and parent.
        unknown: The unavailable name that should produce a warning, if any.
    """
    # Given both harnesses, a config preference, and an optional override.
    log = replace(_DEFAULT_LOG, prefer_harness=("codex",))
    variables = _NESTED.copy()
    if override is not None:
        variables["WIO_PREFER_HARNESS"] = override

    # When the session is identified.
    identity, warnings = _identify(variables, log)

    # Then the preference determines the fields and unknown names are reported.
    assert identity == SessionIdentity(*expected, ("claude-code", "codex"), _NESTED)
    if unknown is None:
        assert warnings == ""
    else:
        assert len(warnings.splitlines()) == 1
        assert unknown in warnings


def test_preference_for_an_unmatched_harness_leaves_the_run_unresolved() -> None:
    """AC-3 limits preferences to harnesses whose session variables are set.

    A configured harness can be preferred while being absent from this run.
    """
    # Given an effective preference for Cursor and just the built-in matches.
    harnesses = freeze(
        _DEFAULT_LOG.harnesses | {"cursor": Harness(("CURSOR_TRACE_ID",))}
    )
    log = replace(_DEFAULT_LOG, harnesses=harnesses, prefer_harness=("cursor",))

    # When the session is identified.
    identity, warnings = _identify(_NESTED, log)

    # Then neither built-in is selected and the valid preference is silent.
    assert identity == SessionIdentity(
        None, None, None, ("claude-code", "codex"), _NESTED
    )
    assert warnings == ""


@pytest.mark.parametrize("override", ["", "none", "cursor"])
def test_a_sole_match_wins_even_with_a_different_preference(override: str) -> None:
    """AC-3 keeps a sole match and validates every override.

    Args:
        override: An empty, clearing, or unknown override.
    """
    # Given a Codex preference and the Claude Code session only.
    log = replace(_DEFAULT_LOG, prefer_harness=("codex",))
    variables = {"CLAUDE_CODE_SESSION_ID": "c1", "WIO_PREFER_HARNESS": override}

    # When the session is identified.
    identity, warnings = _identify(variables, log)

    # Then Claude Code wins, with a warning for the unknown override.
    assert identity == SessionIdentity(
        "claude-code", "c1", None, ("claude-code",), {"CLAUDE_CODE_SESSION_ID": "c1"}
    )
    if override == "cursor":
        assert len(warnings.splitlines()) == 1
        assert "cursor" in warnings
    else:
        assert warnings == ""


@pytest.mark.parametrize(
    "value", ["bad value!", "x/y", "é", "x\n", "a" * 129, "a" * 200]
)
def test_malformed_session_retains_the_harness(value: str) -> None:
    """AC-4 omits malformed ids and keeps the harness match.

    Args:
        value: A session value outside the allowed character set or length.
    """
    # Given a set but malformed Claude Code session variable.
    variables = {"CLAUDE_CODE_SESSION_ID": value}

    # When the session is identified.
    identity, warnings = _identify(variables)

    # Then only the harness is identified and one warning names the variable.
    assert identity == SessionIdentity("claude-code", None, None, ("claude-code",), {})
    assert len(warnings.splitlines()) == 1
    assert "CLAUDE_CODE_SESSION_ID" in warnings
    assert value not in warnings


@pytest.mark.parametrize("value", ["a" * 128, "Az0._:-"])
def test_well_shaped_ids_are_used_as_given(value: str) -> None:
    """AC-4 preserves valid ids, including the maximum length.

    Args:
        value: A valid session id at a length or alphabet boundary.
    """
    # Given a valid Claude Code session variable.
    variables = {"CLAUDE_CODE_SESSION_ID": value}

    # When the session is identified.
    identity, warnings = _identify(variables)

    # Then the original value is the session and is recorded unchanged.
    assert identity == SessionIdentity(
        "claude-code", value, None, ("claude-code",), variables
    )
    assert warnings == ""


def test_an_empty_session_variable_is_unset() -> None:
    """AC-4 treats the empty string as an unset environment value.

    An unset value contributes neither a match nor a diagnostic.
    """
    # Given an empty Claude Code session variable.
    variables = {"CLAUDE_CODE_SESSION_ID": ""}

    # When the session is identified.
    identity, warnings = _identify(variables)

    # Then the record has no matches or ids and stderr is empty.
    assert identity == SessionIdentity(None, None, None, (), {})
    assert warnings == ""


def test_first_set_session_can_be_malformed() -> None:
    """AC-4 preserves the distinction between subagents and main sessions.

    A set thread variable establishes a match even when its id is unusable.
    """
    # Given a malformed thread id and a valid main session id.
    variables = {"CODEX_THREAD_ID": "bad value!", "CODEX_SESSION_ID": "s1"}

    # When the session is identified.
    identity, warnings = _identify(variables)

    # Then the harness is known, the session and parent are unknown, and the
    # main session id still appears in ids.
    assert identity == SessionIdentity(
        "codex", None, None, ("codex",), {"CODEX_SESSION_ID": "s1"}
    )
    assert len(warnings.splitlines()) == 1
    assert "CODEX_THREAD_ID" in warnings
    assert "bad value!" not in warnings


def test_malformed_parent_and_extra_values_are_dropped() -> None:
    """AC-4 diagnoses unusable parent and extra values independently.

    A valid thread id still identifies its session.
    """
    # Given a valid thread id and malformed ids for the parent and extra value.
    variables = {
        "CODEX_THREAD_ID": "t2",
        "CODEX_SESSION_ID": "bad value!",
        "AI_AGENT": "x/y",
    }

    # When the session is identified.
    identity, warnings = _identify(variables)

    # Then the parent is unknown and each dropped variable is diagnosed on stderr.
    assert identity == SessionIdentity(
        "codex", "t2", None, ("codex",), {"CODEX_THREAD_ID": "t2"}
    )
    assert len(warnings.splitlines()) == 2
    assert warnings.count("CODEX_SESSION_ID") == 1
    assert warnings.count("AI_AGENT") == 1
    assert "bad value!" not in warnings
    assert "x/y" not in warnings


@pytest.mark.parametrize(("first_valid", "parent"), [("outer", "outer"), ("r9", None)])
def test_parent_uses_the_first_valid_candidate(
    first_valid: str, parent: str | None
) -> None:
    """AC-4 derives the parent from the first well-shaped candidate.

    Args:
        first_valid: The first well-shaped parent id, which can equal the session.
        parent: The expected distinct parent if the first valid candidate differs.
    """
    # Given a custom harness with a malformed parent before two valid candidates.
    harness = Harness(
        ("CURSOR_TRACE_ID",), ("BAD_PARENT", "FIRST_PARENT", "LAST_PARENT")
    )
    log = replace(_DEFAULT_LOG, harnesses=freeze({"cursor": harness}))
    variables = {
        "CURSOR_TRACE_ID": "r9",
        "BAD_PARENT": "bad/value",
        "FIRST_PARENT": first_valid,
        "LAST_PARENT": "later",
    }

    # When the session is identified.
    identity, warnings = _identify(variables, log)

    # Then the first valid parent is used only when distinct from the session.
    assert identity == SessionIdentity(
        "cursor",
        "r9",
        parent,
        ("cursor",),
        {
            "CURSOR_TRACE_ID": "r9",
            "FIRST_PARENT": first_valid,
            "LAST_PARENT": "later",
        },
    )
    assert len(warnings.splitlines()) == 1
    assert "BAD_PARENT" in warnings
    assert "bad/value" not in warnings


def test_a_malformed_variable_named_twice_warns_once() -> None:
    """AC-4 diagnoses a variable once across multiple lists.

    A session lookup and extra recording can both name one variable.
    """
    # Given AI_AGENT in both a session list and the extra list.
    harnesses = freeze(_DEFAULT_LOG.harnesses | {"cursor": Harness(("AI_AGENT",))})
    log = replace(_DEFAULT_LOG, harnesses=harnesses)

    # When both uses see a malformed value.
    identity, warnings = _identify({"AI_AGENT": "x/y"}, log)

    # Then Cursor still matches and one warning names AI_AGENT without its value.
    assert identity == SessionIdentity("cursor", None, None, ("cursor",), {})
    assert len(warnings.splitlines()) == 1
    assert "AI_AGENT" in warnings
    assert "x/y" not in warnings


def test_lookup_is_limited_and_ids_keep_first_occurrence_order() -> None:
    """AC-5 limits environment reads and orders ids by config.

    Extra recording can share a name with a harness mapping.
    """
    # Given an added harness, a repeated name, and an unrelated environment value.
    harnesses = freeze(
        _DEFAULT_LOG.harnesses | {"cursor": Harness(("CURSOR_TRACE_ID", "AI_AGENT"))}
    )
    log = replace(
        _DEFAULT_LOG,
        harnesses=harnesses,
        record_env_vars=("AI_AGENT", "WIO_PREFER_HARNESS"),
    )
    variables = {
        "SECRET_TOKEN": "hunter2",
        "AI_AGENT": "x",
        "CURSOR_TRACE_ID": "r9",
        "CLAUDE_CODE_SESSION_ID": "c1",
        "WIO_PREFER_HARNESS": "cursor",
    }
    environment = Mock()
    environment.get.side_effect = variables.get
    stdio = FakeStdio()

    # When the session is identified.
    identity = identify(log, environment, stdio)

    # Then the override picks Cursor and only configured id values are retained.
    assert environment.method_calls == [
        call.get("CLAUDE_CODE_SESSION_ID"),
        call.get("CODEX_THREAD_ID"),
        call.get("CODEX_SESSION_ID"),
        call.get("CURSOR_TRACE_ID"),
        call.get("AI_AGENT"),
        call.get("WIO_PREFER_HARNESS"),
    ]
    assert tuple(identity.ids.items()) == (
        ("CLAUDE_CODE_SESSION_ID", "c1"),
        ("CURSOR_TRACE_ID", "r9"),
        ("AI_AGENT", "x"),
    )
    assert (identity.harness, identity.session, identity.parent) == (
        "cursor",
        "r9",
        None,
    )
    assert identity.matches == ("claude-code", "cursor")
    assert stdio.stderr.tell() == 0


def test_custom_session_mapping_identifies_a_harness() -> None:
    """AC-5 uses effective harness mappings for session lookup.

    A project can add a harness with its own variable names.
    """
    # Given a configured Cursor mapping and its session variable.
    harnesses = freeze(
        _DEFAULT_LOG.harnesses | {"cursor": Harness(("CURSOR_TRACE_ID",))}
    )
    log = replace(_DEFAULT_LOG, harnesses=harnesses)
    variables = {"CURSOR_TRACE_ID": "r9"}

    # When the session is identified.
    identity, warnings = _identify(variables, log)

    # Then Cursor is the sole match and supplies the session.
    assert identity == SessionIdentity("cursor", "r9", None, ("cursor",), variables)
    assert warnings == ""


def test_the_preference_is_reserved_in_harness_lists() -> None:
    """AC-5 reserves the override when a mapping names it.

    Declaring the override as a session or parent variable leaves it available
    exclusively for selecting among genuine matches.
    """
    # Given a config that also names the override in harness mappings.
    harnesses = freeze(
        _DEFAULT_LOG.harnesses
        | {
            "cursor": Harness(("WIO_PREFER_HARNESS",)),
            "codex": Harness(("CODEX_THREAD_ID",), ("WIO_PREFER_HARNESS",)),
        }
    )
    log = replace(_DEFAULT_LOG, harnesses=harnesses)
    actual = {"CLAUDE_CODE_SESSION_ID": "c1", "CODEX_THREAD_ID": "t2"}
    preference = {"WIO_PREFER_HARNESS": "codex"}

    # When the override is applied with and without genuine matches.
    selected, warnings = _identify(actual | preference, log)
    unresolved, unresolved_warnings = _identify(preference, log)

    # Then the override can select Codex and contributes no ids or matches.
    assert selected == SessionIdentity(
        "codex", "t2", None, ("claude-code", "codex"), actual
    )
    assert unresolved == SessionIdentity(None, None, None, (), {})
    assert warnings == unresolved_warnings == ""
