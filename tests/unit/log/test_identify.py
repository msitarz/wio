# SPDX-License-Identifier: Apache-2.0
"""Contract scenarios for harness session identification.

The scenarios cover the identification boundary through its environment and
standard-stream ports.
"""

from unittest.mock import Mock, call

import pytest

from tests.unit.fakes import FakeStdio
from wio.log.identify import SessionIdentity, identify
from wio.models.config import Log


def test_claude_code_records_its_session() -> None:
    """AC-1 identifies Claude Code.

    Run identification through the environment and standard-stream ports.
    """
    # Given CLAUDE_CODE_SESSION_ID=c1 and AI_AGENT=claude-code_2.
    # When the session is identified.
    # Then the sole match is claude-code with session c1 and no parent, and
    # ids holds both variables.
    pytest.skip("Pending harness session implementation")


def test_codex_uses_thread_then_session() -> None:
    """AC-1 identifies Codex and its parent.

    Run identification through the environment and standard-stream ports.
    """
    # Given CODEX_SESSION_ID=s1 and CODEX_THREAD_ID set to s1, t2, or unset.
    # When the session is identified.
    # Then the sole match is codex and the session/parent pairs are (s1, None),
    # (t2, s1), and (s1, None), respectively.
    pytest.skip("Pending harness session implementation")


def test_nested_matches_stay_unresolved() -> None:
    """AC-2 retains both matches in order.

    Run identification through the environment and standard-stream ports.
    """
    # Given CLAUDE_CODE_SESSION_ID=c1, CODEX_THREAD_ID=t2, CODEX_SESSION_ID=s1.
    # When the session is identified.
    # Then harness, session and parent are None, matches is (claude-code, codex),
    # and ids holds those three variables in that order.
    pytest.skip("Pending harness session implementation")


def test_ai_agent_alone_does_not_identify_a_harness() -> None:
    """AC-2 records AI_AGENT as an id.

    Run identification through the environment and standard-stream ports.
    """
    # Given only AI_AGENT=x.
    # When the session is identified.
    # Then harness, session and parent are None, matches is empty, and
    # ids is {AI_AGENT: x}.
    pytest.skip("Pending harness session implementation")


def test_preference_resolves_nested_matches() -> None:
    """AC-3 applies the override syntax.

    Run identification through the environment and standard-stream ports.
    """
    # Given CLAUDE_CODE_SESSION_ID=c1, CODEX_THREAD_ID=t2, CODEX_SESSION_ID=s1,
    # and a config preference for codex.
    # When the session is identified with each preference override.
    # Then absent, empty, whitespace and comma-only overrides give (codex, t2, s1);
    # ' claude-code , ' and 'claude-code,,codex' give (claude-code, c1, None);
    # 'none' gives (None, None, None); and 'none,codex' and 'cursor,codex'
    # give (codex, t2, s1) and warn about the first item.
    pytest.skip("Pending harness session implementation")


def test_preference_can_miss_the_matching_harnesses() -> None:
    """AC-3 handles unused preferences.

    Run identification through the environment and standard-stream ports.
    """
    # Given a config with cursor but no CURSOR_TRACE_ID.
    # When the session is identified.
    # Then a cursor preference in a nested run gives (None, None, None).
    # A sole Claude Code match with id c1 gives (claude-code, c1, None)
    # with either a codex preference or a 'none' override.
    pytest.skip("Pending harness session implementation")


def test_unknown_preference_is_warned_about_on_a_sole_match() -> None:
    """AC-3 validates every override.

    Run identification through the environment and standard-stream ports.
    """
    # Given only claude-code matches and the override names cursor.
    # When the session is identified.
    # Then claude-code wins and the warning names cursor.
    pytest.skip("Pending harness session implementation")


def test_first_set_session_can_be_malformed() -> None:
    """AC-4 retains the selected harness.

    Run identification through the environment and standard-stream ports.
    """
    # Given CODEX_THREAD_ID is malformed and CODEX_SESSION_ID=s1.
    # When the session is identified.
    # Then codex matches with no session or parent, ids only holds
    # CODEX_SESSION_ID, and the warning names CODEX_THREAD_ID alone.
    pytest.skip("Pending harness session implementation")


def test_values_are_validated_once() -> None:
    """AC-4 discards malformed values without leaking them.

    Run identification through the environment and standard-stream ports.
    """
    # Given CODEX_THREAD_ID=t2, CODEX_SESSION_ID='bad value!' and AI_AGENT=x/y.
    # When the session is identified.
    # Then the result is (codex, t2, None), ids only holds CODEX_THREAD_ID=t2,
    # and exactly two stderr warnings name the malformed variables, omitting
    # both raw values.
    pytest.skip("Pending harness session implementation")


def test_a_malformed_variable_named_twice_warns_once() -> None:
    """AC-4 diagnoses the variable once across lists.

    The session lookup and extra recording both name the same variable.
    """
    # Given cursor maps session to AI_AGENT, which is also in record_env_vars,
    # and AI_AGENT=x/y.
    # When the session is identified.
    # Then cursor matches with no session, no id is recorded, and exactly one
    # stderr warning names AI_AGENT without its value.
    pytest.skip("Pending harness session implementation")


def test_id_shape_has_exact_boundaries() -> None:
    """AC-4 enforces the id shape.

    Run identification through the environment and standard-stream ports.
    """
    # Given Claude Code's id is empty, 128 or 129 letters long, or includes
    # spaces, punctuation outside the alphabet, or non-ASCII characters.
    # When the session is identified.
    # Then empty gives no match or warning, 128 letters gives a valid session,
    # and each malformed value matches with no session or id and one
    # warning that names the variable without its value.
    pytest.skip("Pending harness session implementation")


def test_lookup_is_limited_and_ids_keep_first_occurrence_order() -> None:
    """AC-5 limits environment reads.

    Run identification through the environment and standard-stream ports.
    """
    # Given cursor maps session to CURSOR_TRACE_ID and AI_AGENT, the extra
    # list names AI_AGENT and WIO_PREFER_HARNESS, and a recording fake has
    # values c1 for CLAUDE_CODE_SESSION_ID, r9 for CURSOR_TRACE_ID, x for AI_AGENT,
    # WIO_PREFER_HARNESS=cursor and SECRET_TOKEN=hunter2.
    # When the session is identified with the recording Environment fake.
    # Then every configured name and WIO_PREFER_HARNESS are read, and nothing
    # else. The names are CLAUDE_CODE_SESSION_ID, CODEX_THREAD_ID, CODEX_SESSION_ID,
    # CURSOR_TRACE_ID, AI_AGENT and WIO_PREFER_HARNESS. The ordered ids are
    # CLAUDE_CODE_SESSION_ID=c1, CURSOR_TRACE_ID=r9 and AI_AGENT=x.
    pytest.skip("Pending harness session implementation")


def test_custom_session_mapping_identifies_a_harness() -> None:
    """AC-5 uses effective mappings.

    Run identification through the environment and standard-stream ports.
    """
    # Given a configured cursor harness and CURSOR_TRACE_ID=r9 alone.
    # When the session is identified.
    # Then cursor matches and r9 is the session.
    pytest.skip("Pending harness session implementation")


def test_the_preference_is_reserved_in_harness_lists() -> None:
    """AC-5 excludes the override from session and parent lookup.

    A configured name for the override cannot give its value a second role.
    """
    # Given cursor names WIO_PREFER_HARNESS as its only session variable
    # and Codex names it as its only parent variable. Claude Code has c1,
    # Codex has thread t2, and the override is codex.
    # When the session is identified.
    # Then the genuine matches are (claude-code, codex), the override selects
    # (codex, t2, None), and ids contains the Claude Code and Codex variables
    # only. With neither of those variables set, no harness matches.
    pytest.skip("Pending harness session implementation")


def test_identify_connects_the_environment_and_standard_streams() -> None:
    """Exercise the wired entry point with an empty environment.

    Every configured lookup is made through Environment.get.
    """
    # Given the built-in mappings and an environment with no set variables.
    environment = Mock()
    environment.get.return_value = None
    stdio = FakeStdio()

    # When the session is identified.
    identity = identify(Log(), environment, stdio)

    # Then no fields are set and only the configured inputs were requested.
    assert identity == SessionIdentity(None, None, None, (), {})
    assert environment.method_calls == [
        call.get("CLAUDE_CODE_SESSION_ID"),
        call.get("CODEX_THREAD_ID"),
        call.get("CODEX_SESSION_ID"),
        call.get("AI_AGENT"),
        call.get("WIO_PREFER_HARNESS"),
    ]
    assert stdio.stderr.tell() == 0
