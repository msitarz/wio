# SPDX-License-Identifier: Apache-2.0
"""The header of a bundle: what a session was given, readable at a glance."""

from typing import TYPE_CHECKING

from wio.context.guidance import escape_skill_field

if TYPE_CHECKING:
    from wio.models.config import Stage


def header(
    work_id: str,
    title: str | None,
    action: str,
    stage_name: str,
    stage: Stage,
    rules: int,
    size_bytes: int,
    size_lines: int,
    skill: tuple[str, str, str] | None,
) -> str:
    """Build the header of a bundle."""
    named = f"{work_id} ({title})" if title else work_id
    lines = [
        f"work: {named}",
        f"action: {action}",
        f"stage: {stage_name}",
        f"gate: {_gate(stage)}",
        f"session: {_session(stage)}",
        f"rules: {rules}",
        f"size: {size_bytes} bytes, {size_lines} lines (body)",
        f"command: wio context {work_id} {action} {stage_name}",
    ]
    if skill is not None:
        name, directory, files = skill
        shown_name = escape_skill_field(name)
        shown_directory = escape_skill_field(directory)
        lines.append(f"skill: {shown_name} ({shown_directory}, files {files})")
    return "\n".join(lines)


def _gate(stage: Stage) -> str:
    """Say whether a stage is a gate, and who judges it when a person does."""
    if not stage.gate:
        return "no"
    return "yes" if stage.judge is None else "yes, judged by a person"


def _session(stage: Stage) -> str:
    """Give a stage's advice on the session that runs it."""
    advice = "" if stage.continuable else ", do not continue it"
    return f"{stage.session}{advice}"
