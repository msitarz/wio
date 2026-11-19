# SPDX-License-Identifier: Apache-2.0
"""Contract scenarios for harness session identification.

The scenarios cover the identification boundary through its environment and
standard-stream ports.
"""

import pytest


def test_one_harness_supplies_session() -> None:
    """AC-1 identifies a sole harness and its session.

    The scenario exercises the public identification boundary.
    """
    # Given only Claude Code or Codex variables, with Codex thread and session variants.
    # When the session is identified.
    # Then the matching session and distinct parent are returned.
    pytest.skip("Pending harness session implementation")


def test_multiple_matches_stay_unresolved() -> None:
    """AC-2 does not guess a harness from ambiguous or absent matches.

    The scenario exercises the public identification boundary.
    """
    # Given both built-in harnesses or only AI_AGENT, with no preference.
    # When the session is identified.
    # Then the result keeps the matches and ids with no selected harness.
    pytest.skip("Pending harness session implementation")


def test_preference_selects_nested_harness() -> None:
    """AC-3 resolves nested sessions by preference.

    The scenario exercises the public identification boundary.
    """
    # Given nested harnesses and a config preference or environment override.
    # When the session is identified.
    # Then the first preferred match wins and unknown names are warned about.
    pytest.skip("Pending harness session implementation")


def test_malformed_values_are_dropped() -> None:
    """AC-4 validates each named id once without leaking its value.

    The scenario exercises the public identification boundary.
    """
    # Given malformed session, parent and recorded ids, including repeated names.
    # When the session is identified.
    # Then invalid ids are omitted and warned about once, without exposing values.
    pytest.skip("Pending harness session implementation")


def test_only_configured_names_are_read() -> None:
    """AC-5 limits reads and preserves first occurrence order.

    The scenario exercises the public identification boundary.
    """
    # Given a custom harness, repeated names and a variable outside the config.
    # When the session is identified.
    # Then only configured names and the override are read, and ids are ordered.
    pytest.skip("Pending harness session implementation")
