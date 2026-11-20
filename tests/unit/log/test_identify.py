# SPDX-License-Identifier: Apache-2.0
"""Contract scenarios for harness session identification.

The scenarios cover the identification boundary through its environment and
standard-stream ports.
"""

from dataclasses import replace
from io import StringIO
from pathlib import Path

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
    """AC-1 and AC-2 record the values and identify the harness.

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
    """AC-3 selects the Codex session and any distinct parent.

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
    """AC-1 and AC-2 retain an extra id without matching a harness.

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
    """AC-2 and AC-5 apply preference syntax to matching harnesses.

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
    """AC-2 limits preference to matching harnesses.

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
    """AC-2 and AC-5 keep the sole match and warn on unknown names.

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


@pytest.mark.parametrize("value", ["", "bad value!", "x/y", "é", "x\n", "a" * 129])
def test_set_session_matches_and_retains_its_value(value: str) -> None:
    """AC-1 and AC-2 match and preserve every set session value."""
    # Given a set Claude Code session variable.
    variables = {"CLAUDE_CODE_SESSION_ID": value}

    # When the session is identified.
    identity, warnings = _identify(variables)

    # Then the session matches by presence and is retained verbatim.
    assert identity == SessionIdentity(
        "claude-code", value, None, ("claude-code",), variables
    )
    assert warnings == ""


@pytest.mark.parametrize(
    ("session", "first_parent", "parent"),
    [("", "", None), ("thread", "", ""), ("thread", "outer\n", "outer\n")],
)
def test_first_set_session_and_parent_win(
    session: str, first_parent: str, parent: str | None
) -> None:
    """AC-3 selects the first set fields and omits an equal parent."""
    # Given ordered candidates with an unset variable before each set field.
    harness = Harness(
        ("UNSET_SESSION", "FIRST_SESSION", "LAST_SESSION"),
        ("UNSET_PARENT", "FIRST_PARENT", "LAST_PARENT"),
    )
    log = Log(harnesses=freeze({"cursor": harness}))
    variables = {
        "FIRST_SESSION": session,
        "LAST_SESSION": "later",
        "FIRST_PARENT": first_parent,
        "LAST_PARENT": "later-parent",
    }

    # When the session is identified.
    identity, warnings = _identify(variables, log)

    # Then the first set fields are used, with an equal parent omitted.
    assert identity == SessionIdentity(
        "cursor", session, parent, ("cursor",), variables
    )
    assert warnings == ""


def test_lookup_is_limited_and_ids_keep_first_occurrence_order() -> None:
    """AC-4 reads shared variables once and orders ids by config.

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
    environment = FakeEnvironment(Path(), variables)
    stdio = FakeStdio()

    # When the session is identified.
    identity = identify(log, environment, stdio)

    # Then the override picks Cursor and only configured id values are retained.
    expected_reads = {
        "CLAUDE_CODE_SESSION_ID",
        "CODEX_THREAD_ID",
        "CODEX_SESSION_ID",
        "CURSOR_TRACE_ID",
        "AI_AGENT",
        "WIO_PREFER_HARNESS",
    }
    assert set(environment.reads) == expected_reads
    assert len(environment.reads) == len(expected_reads)
    assert tuple(identity.ids.items()) == (
        ("CLAUDE_CODE_SESSION_ID", "c1"),
        ("CURSOR_TRACE_ID", "r9"),
        ("AI_AGENT", "x"),
        ("WIO_PREFER_HARNESS", "cursor"),
    )
    assert (identity.harness, identity.session, identity.parent) == (
        "cursor",
        "r9",
        None,
    )
    assert identity.matches == ("claude-code", "cursor")
    assert stdio.stderr.tell() == 0


def test_custom_session_mapping_identifies_a_harness() -> None:
    """AC-2 matches harnesses using the effective mappings.

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


@pytest.mark.parametrize(
    ("override", "selected", "unknown"),
    [("", "cursor", ""), (" missing , codex ", "codex", "missing")],
)
def test_preference_also_supplies_shared_fields(
    override: str, selected: str, unknown: str
) -> None:
    """AC-2, AC-4 and AC-5 reuse the raw override while resolving preference."""
    # Given an override shared by two mappings and the extra recorded variables.
    name = "WIO_PREFER_HARNESS"
    log = Log(
        harnesses=freeze(
            {
                "cursor": Harness((name,)),
                "codex": Harness(("CODEX_THREAD_ID",), (name,)),
            }
        ),
        prefer_harness=("cursor",),
        record_env_vars=(name,),
    )
    variables = {name: override, "CODEX_THREAD_ID": "t2"}

    # When both harnesses match.
    environment = FakeEnvironment(Path(), variables)
    stderr = StringIO()
    identity = identify(log, environment, FakeStdio(stderr=stderr))

    # Then the override is read once and supplies its raw value to the winner.
    assert identity.matches == ("cursor", "codex")
    assert identity.harness == selected
    fields = (override, None) if selected == "cursor" else ("t2", override)
    assert (identity.session, identity.parent) == fields
    assert tuple(identity.ids.items()) == tuple(variables.items())
    assert environment.reads.count(name) == 1
    warning = f"warning: {name} names unknown harness {unknown!r}\n" if unknown else ""
    assert stderr.getvalue() == warning


def test_record_only_preference_warns_without_a_harness_match() -> None:
    """AC-5 records an extra override and warns even when no harness matches."""
    # Given an unknown override configured only as an extra recorded variable.
    name = "WIO_PREFER_HARNESS"
    log = replace(_DEFAULT_LOG, record_env_vars=(name,))
    variables = {name: "missing"}

    # When the session is identified without any set session variables.
    identity, warnings = _identify(variables, log)

    # Then the override is recorded verbatim and the unknown name is reported.
    assert identity == SessionIdentity(None, None, None, (), variables)
    assert warnings == "warning: WIO_PREFER_HARNESS names unknown harness 'missing'\n"
