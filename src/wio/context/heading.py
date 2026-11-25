# SPDX-License-Identifier: Apache-2.0
"""The header of a bundle: what a session was given, readable at a glance."""

from typing import TYPE_CHECKING

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
    states what it is given and looks nothing up.

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
    del work_id, title, action, stage_name, stage, rules
    del size_bytes, size_lines, skill
    raise NotImplementedError
