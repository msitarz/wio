# SPDX-License-Identifier: Apache-2.0
"""The roots that count for a stage of a Work, and the roots that hold a file.

Both are computed from values alone, the config and what the caller names, so a
listing and a bundle choose the same roots. A Work's own roots come through the
`WorkRoots` port, which `wio.rules` never reads a file for.
"""

from pathlib import PurePosixPath
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Sequence

    from wio.models.config import Config
    from wio.rules.ports import WorkRoots

_WORK = "@work"
"""The entry of a stage's `roots` that stands for the Work's roots."""


def stage_roots(
    config: Config, stage: str | None, work_id: str, work_roots: WorkRoots
) -> tuple[str, ...]:
    """Find the roots that a stage selects for a Work.

    A stage with no `roots`, and a call with no stage, select the Work's roots.
    A stage with `roots` selects exactly those, where `@work` stands for the
    Work's roots and `[]` selects none. The names are sorted and each is once.
    It does no input or output, and the result does not depend on the order of
    the roots of the config or of a stage's `roots`.

    The stage is checked first, then its own roots, and the Work is looked up and
    its roots checked against the config only when the stage selects them, so a
    stage with only its own roots never fails for the Work.

    Args:
        config: The settings, whose roots and stages are read.
        stage: The stage's name, or `None` for the roots of the Work.
        work_id: The Work's id.
        work_roots: Gives the roots of the Work.

    Returns:
        The names of the roots that count.

    Raises:
        KeyError: The stage, the Work, a root of the Work or a root of the stage
            is not known. Its first argument is the name that was not found.
        ValueError: The stage selects the Work's roots, without `roots` or
            through `@work`, and the Work has none.
    """
    listed = _stage_roots_of(config, stage)
    own = _checked(config, [name for name in listed or () if name != _WORK])
    if listed is not None and _WORK not in listed:
        return own
    return _merged(own, _work_roots(config, work_id, work_roots))


def _stage_roots_of(config: Config, stage: str | None) -> Sequence[str] | None:
    """Read the `roots` of a stage."""
    if stage is None:
        return None
    return config.stages[stage].roots


def _checked(config: Config, names: Sequence[str]) -> tuple[str, ...]:
    """Check that roots are roots of the config."""
    for name in names:
        if name not in config.roots:
            raise KeyError(name)
    return tuple(sorted(set(names)))


def _work_roots(config: Config, work_id: str, work_roots: WorkRoots) -> tuple[str, ...]:
    """Find the roots of a Work that a stage selects."""
    found = work_roots.roots_of(work_id)
    if found is None:
        raise KeyError(work_id)
    if not found:
        msg = f"The Work `{work_id}` has no roots."
        raise ValueError(msg)
    return _checked(config, found)


def _merged(own: tuple[str, ...], work: tuple[str, ...]) -> tuple[str, ...]:
    """Join the roots of a stage with those of the Work."""
    return tuple(sorted({*own, *work}))


def roots_of_path(config: Config, path: PurePosixPath) -> tuple[str, ...]:
    """Find the roots that contain a file.

    A file is in a root when its path is one of the root's paths or lies under
    it, by whole path components. The path is relative to the repository root,
    normalized and written with `/`, and need not exist. It does no input or
    output, and the result does not depend on the order of the roots or of a
    root's paths.

    Args:
        config: The settings, whose roots are read.
        path: The file's path.

    Returns:
        Every root that contains it, sorted by name, or none.
    """
    return tuple(
        name
        for name, root in sorted(config.roots.items())
        if any(_within(path, given) for given in root.paths)
    )


def _within(path: PurePosixPath, root: str) -> bool:
    """Tell whether a path is a root's path or lies under it."""
    base = PurePosixPath(root)
    return path == base or base in path.parents
