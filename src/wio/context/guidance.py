# SPDX-License-Identifier: Apache-2.0
"""Write the stage guidance for a context bundle.

The builder reads the configured stage and uses the skill location supplied by
composition so the guidance can refer to the same skill as the header.
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from wio.models.skill import FoundSkill
    from wio.ports import Settings


def stage_guidance(
    settings: Settings, stage_name: str, skill: FoundSkill | None
) -> str:
    """Give a session the guidance for its stage.

    Args:
        settings: Gives the configured stage, which has exactly one of a goal
            and a skill.
        stage_name: The name of the configured stage.
        skill: The caller's lookup result for a stage that names a skill, or
            `None` for a stage with a goal.

    Returns:
        The goal unchanged, including an empty goal, or one line directing the
        session to the skill's repository-relative `SKILL.md` and other files.

    Raises:
        ConfigurationError: The config cannot be loaded.
        KeyError: The config does not declare the stage.
        ValueError: A stage without a goal lacks a skill name or lookup result.
    """
    stage = settings.load().stages[stage_name]
    if stage.goal is not None:
        return stage.goal
    if stage.skill is None or skill is None:
        message = f"Stage `{stage_name}` requires a configured and resolved skill."
        raise ValueError(message)
    return (
        f"This stage's procedure is the skill `{stage.skill}`. Read "
        f"`{skill.directory}/SKILL.md` and follow it; "
        "its other files are in the same directory."
    )
