# SPDX-License-Identifier: Apache-2.0
"""Deterministic text and JSON renderers for `wio describe`."""

from dataclasses import asdict
from typing import TYPE_CHECKING

from wio.formats import encode_json

if TYPE_CHECKING:
    from wio.describe.models import (
        CommandDescription,
        EngineDescription,
        ReferenceTable,
    )


def render_engine_text(engine: EngineDescription) -> str:
    """Render an `EngineDescription` as concise, deterministic text.

    Args:
        engine: The top-level engine description.

    Returns:
        Multi-line text ending in a single newline.
    """
    lines = [
        f"wio {engine.version}",
        engine.summary,
        "",
        "Exit codes:",
        *(f"  {item.code:<2}  {item.meaning}" for item in engine.exit_codes),
        "",
        "Concepts:",
        *(f"  {item.name:<10}  {item.summary}" for item in engine.concepts),
        "",
        "Commands:",
        *(f"  {item.name:<10}  {item.summary}" for item in engine.commands),
    ]
    return "\n".join(lines) + "\n"


def render_engine_json(engine: EngineDescription) -> str:
    """Render an `EngineDescription` as single-line JSON ending in a newline."""
    return _render_json(engine)


def render_command_text(command: CommandDescription) -> str:
    """Render a `CommandDescription` as concise, deterministic text.

    Args:
        command: The subcommand description.

    Returns:
        Multi-line text ending in a single newline.
    """
    lines = [
        f"wio {command.name} - {command.summary}",
        "",
        "Forms:",
        *(f"  {form.usage}\n    {form.summary}" for form in command.forms),
        "",
        "Invariants:",
        *(f"  - {item}" for item in command.invariants),
    ]
    for table in command.references:
        lines.extend(_render_reference_table(table))
    return "\n".join(lines) + "\n"


def render_command_json(command: CommandDescription) -> str:
    """Render a `CommandDescription` as single-line JSON ending in a newline."""
    return _render_json(command)


def _render_json(description: EngineDescription | CommandDescription) -> str:
    """Encode a description dataclass as a single-line JSON object."""
    return encode_json(asdict(description)) + "\n"


def _render_reference_table(table: ReferenceTable) -> list[str]:
    """Render one code-derived reference table as indented lines."""
    return [
        "",
        f"{table.title}:",
        *(f"  {e.key} ({e.value}): {e.description}" for e in table.entries),
    ]
