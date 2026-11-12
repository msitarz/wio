# SPDX-License-Identifier: Apache-2.0
"""The actions a Work resolves to, and where each one comes from."""

from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    from collections.abc import Mapping
    from pathlib import Path

    from wio.io.ports import FileSystem
    from wio.models.template import Template

type Pipeline = str | tuple[str, ...]
"""A stage preset id, or the stages of an action, as a Work or a template writes
them."""
type ActionSource = Literal["work", "template", "defaults"]
"""Where a resolved action comes from: the Work's own `[actions]`, its template,
or the config's `[works.defaults.actions]`."""


@dataclass(frozen=True)
class ResolvedAction:
    """One action of a Work after its own `[actions]` replaced the inherited ones.

    It is immutable. It keeps the source of the action and whether the Work
    removed it, which `wio contracts show` prints and the check does not need.

    Attributes:
        name: The action's name.
        pipeline: What the action runs as the source wrote it, which is empty for
            an action that the Work removed.
        source: The Work, when its own `[actions]` name the action, otherwise the
            template or the config defaults that the Work inherits from.
        removed: Whether the Work's own `[actions]` give the action an empty list,
            which removes it from the Work.
    """

    name: str
    pipeline: Pipeline
    source: ActionSource
    removed: bool


def resolve_actions(
    own: Mapping[str, Pipeline],
    inherited: Mapping[str, Pipeline],
    inherited_from: Literal["template", "defaults"],
) -> tuple[ResolvedAction, ...]:
    """Layer a Work's own `[actions]` over what it inherits.

    Each action that the Work names replaces that action of what it inherits, an
    empty list removing it, and the actions that it does not name are inherited.
    The caller passes the template's actions for a Work that names a template and
    the config defaults for a Work that names none, so the defaults are never
    layered under a named template, and an empty list among the inherited actions
    is the same as leaving the action out.

    Args:
        own: The Work's own `[actions]`, in the order it wrote them.
        inherited: The actions of the template, or of the config defaults, in the
            order they were written.
        inherited_from: Which of the two `inherited` is.

    Returns:
        One entry for each action that either names, the inherited ones first in
        their order and then the Work's own in its order, each with its source.
        An action that the Work removed is an entry with `removed` set, and an
        empty inherited list gives no entry.
    """
    raise NotImplementedError


def template_actions(
    template: Template, root: Path, files: FileSystem
) -> dict[str, Pipeline] | None:
    """Read the `[actions]` of a template from its file.

    Args:
        template: The template, whose `path` is relative to the repository root.
        root: The repository root.
        files: The port that reads the file.

    Returns:
        The actions in the order written, empty for a template that has none, or
        `None` when the file cannot be read, decoded or parsed, or when its
        `[actions]` are not a table of a stage preset or an array of stages each.
        It reports nothing, because `wio templates check` reports a template.
    """
    raise NotImplementedError
