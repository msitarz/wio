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
    """Build the header of a bundle.

    Its first three lines name the Work, with its title when it has one, the
    action and the stage, so a wrong stage is caught at once. It then says
    whether the stage is a gate and, for a gate, whether a person judges it,
    which session the stage advises, the number of rules, the size of the body,
    the command that gives this bundle again and, for a stage with a skill,
    where the skill was found. The command names the Work, the action and the
    stage and no option that only changes where the bundle goes. The header
    states what it is given and looks nothing up. It escapes the displayed
    skill name and directory in the same way as stage guidance.

    Args:
        work_id: The Work's id.
        title: The Work's title, if it has one.
        action: The action, as parsed.
        stage_name: The stage, as parsed.
        stage: The stage's settings.
        rules: The number of rules that the bundle prints.
        size_bytes: The size of the body in UTF-8 bytes.
        size_lines: The number of lines of the body.
        skill: For a stage with a skill, its name, the directory it was found
            in, relative to the repository, and the hash of its files. The
            caller passes it exactly when the stage has a skill.

    Returns:
        The lines joined by newlines, with no blank line and no newline at the
        end.
    """
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
