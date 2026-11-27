# SPDX-License-Identifier: Apache-2.0
"""Unit tests for `wio.describe.render`."""

import json

from wio.describe import (
    describe_command,
    describe_engine,
    render_command_json,
    render_command_text,
    render_engine_json,
    render_engine_text,
)


def test_render_engine_text_is_deterministic_and_ends_with_one_newline() -> None:
    """`render_engine_text` includes version, exit codes, concepts and commands."""
    # Given the live engine description
    engine = describe_engine()

    # When rendered twice as text
    first = render_engine_text(engine)
    second = render_engine_text(engine)

    # Then output is byte-for-byte identical, ends in one newline and has all sections
    assert first == second
    assert first.endswith("\n")
    assert not first.endswith("\n\n")
    assert f"wio {engine.version}" in first
    assert "Exit codes:" in first
    assert "Concepts:" in first
    assert "Commands:" in first


def test_render_engine_json_is_single_line_valid_json() -> None:
    """`render_engine_json` emits a single-line JSON object ending in one newline."""
    # Given the live engine description
    engine = describe_engine()

    # When rendered as JSON
    rendered = render_engine_json(engine)

    # Then it is one line ending in a newline and decodes to the expected fields
    assert rendered.endswith("\n")
    assert "\n" not in rendered[:-1]
    data = json.loads(rendered)
    assert data["version"] == engine.version
    assert [e["code"] for e in data["exit_codes"]] == [0, 1, 2, 70]
    assert [c["name"] for c in data["commands"]] == [c.name for c in engine.commands]


def test_render_command_text_includes_forms_invariants_and_references() -> None:
    """`render_command_text` renders forms, invariants and reference tables."""
    # Given the description of `config`, which has a reference table
    command = describe_command("config")

    # When rendered as text
    rendered = render_command_text(command)

    # Then it ends in one newline and includes forms, invariants and schema keys
    assert rendered.endswith("\n")
    assert not rendered.endswith("\n\n")
    assert "wio config -" in rendered
    assert "Forms:" in rendered
    assert "Invariants:" in rendered
    assert "Config schema keys:" in rendered


def test_render_command_json_is_single_line_valid_json() -> None:
    """`render_command_json` emits a single-line JSON object ending in one newline."""
    # Given the description of `templates`
    command = describe_command("templates")

    # When rendered as JSON
    rendered = render_command_json(command)

    # Then it is one line ending in a newline and decodes with the command name
    assert rendered.endswith("\n")
    assert "\n" not in rendered[:-1]
    data = json.loads(rendered)
    assert data["name"] == "templates"
    assert data["references"]
