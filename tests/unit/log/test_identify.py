# SPDX-License-Identifier: Apache-2.0
"""Contract scenarios for harness session identification.

The scenarios cover the identification boundary through its environment and
standard-stream ports.
"""

import pytest


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
    # Given both harnesses and a config preference for codex.
    # When the session is identified.
    # Then absent, empty, whitespace and comma-only overrides select codex;
    # ' claude-code , ' and 'claude-code,,codex' select claude-code;
    # 'none' leaves the run unresolved; 'none,codex' and 'cursor,codex'
    # select codex and warn about the first item.
    pytest.skip("Pending harness session implementation")


def test_preference_can_miss_the_matching_harnesses() -> None:
    """AC-3 handles unused preferences.

    Run identification through the environment and standard-stream ports.
    """
    # Given a config with cursor but no CURSOR_TRACE_ID.
    # When the session is identified.
    # Then a cursor preference leaves a nested run unresolved, while sole
    # claude-code wins with either a codex preference or a 'none' override.
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
    # Given a malformed parent, malformed recorded id, or repeated malformed name.
    # When the session is identified.
    # Then each malformed variable is absent from ids and warned about once
    # on stderr, without its value. A valid session remains available.
    pytest.skip("Pending harness session implementation")


def test_id_shape_has_exact_boundaries() -> None:
    """AC-4 enforces the id shape.

    Run identification through the environment and standard-stream ports.
    """
    # Given Claude Code's id is empty, 128 or 129 letters long, or includes
    # spaces, punctuation outside the alphabet, or non-ASCII characters.
    # When the session is identified.
    # Then empty gives no match or warning, 128 letters gives a valid session,
    # and each malformed value matches with no session and one warning.
    pytest.skip("Pending harness session implementation")


def test_lookup_is_limited_and_ids_keep_first_occurrence_order() -> None:
    """AC-5 limits environment reads.

    Run identification through the environment and standard-stream ports.
    """
    # Given cursor adds CURSOR_TRACE_ID and AI_AGENT, and the extra list names
    # WIO_PREFER_HARNESS alongside AI_AGENT. SECRET_TOKEN is also set.
    # When the session is identified.
    # Then only CLAUDE_CODE_SESSION_ID, CODEX_THREAD_ID, CODEX_SESSION_ID,
    # CURSOR_TRACE_ID, AI_AGENT and WIO_PREFER_HARNESS are read. The ids
    # keys are CLAUDE_CODE_SESSION_ID, CURSOR_TRACE_ID, AI_AGENT in order.
    pytest.skip("Pending harness session implementation")


def test_custom_session_mapping_identifies_a_harness() -> None:
    """AC-5 uses effective mappings.

    Run identification through the environment and standard-stream ports.
    """
    # Given a configured cursor harness and CURSOR_TRACE_ID=r9 alone.
    # When the session is identified.
    # Then cursor matches and r9 is the session.
    pytest.skip("Pending harness session implementation")
