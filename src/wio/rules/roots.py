# SPDX-License-Identifier: Apache-2.0
"""The roots that count for a stage of a Work, and the roots that hold a file.

Both are computed from values alone, the config and what the caller names, so a
listing and a bundle choose the same roots. A Work's own roots come through the
`WorkRoots` port, which `wio.rules` never reads a file for.
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import PurePosixPath

    from wio.models.config import Config
    from wio.rules.ports import WorkRoots


def stage_roots(
    config: Config, stage: str | None, work_id: str, work_roots: WorkRoots
) -> tuple[str, ...]:
    """Find the roots that a stage selects for a Work.

    A stage with no `roots`, and a call with no stage, select the Work's roots.
    A stage with `roots` selects exactly those, where `@work` stands for the
    Work's roots and `[]` selects none. The names are sorted and each is once.
    It does no input or output, and the result does not depend on the order of
    the roots of the config or of a stage's `roots`.

    Args:
        config: The settings, whose roots and stages are read.
        stage: The stage's name, or `None` for the roots of the Work.
        work_id: The Work's id.
        work_roots: Gives the roots of the Work.

    Returns:
        The names of the roots that count.

    Raises:
        KeyError: The stage, the Work, a root of the Work or a root of the stage
            is not known; it names what was not found.
        ValueError: The stage selects the Work's roots, without `roots` or
            through `@work`, and the Work has none.
    """
    del config, stage, work_id, work_roots
    raise NotImplementedError


def roots_of_path(config: Config, path: PurePosixPath) -> tuple[str, ...]:
    """Find the roots that contain a file.

    A file is in a root when its path is one of the root's paths or lies under
    it, by whole path components. The path is relative to the repository root,
    normalized and written with `/`, and need not exist. It does no input or
    output.

    Args:
        config: The settings, whose roots are read.
        path: The file's path.

    Returns:
        Every root that contains it, sorted by name, or none.
    """
    msg = "the roots of a path"
    raise NotImplementedError(msg)
