# SPDX-License-Identifier: Apache-2.0
"""The spec of `GitHistory`, the adapter of the `History` port.

The stub is the spec until the wiring stage of the Work that builds the history
adapter writes the class into `wio.io.adapters` and deletes this stub, so the
spec and the code never coexist.
"""

from collections.abc import Sequence
from pathlib import Path

from wio.env.ports import Environment
from wio.models.commits import Commit

class GitHistory:
    """The revisions of the working directory's repository, as `History`.

    It is given an `Environment` and runs git in the working directory that the
    environment reports, as `GitRepository` does, and raises the same
    `RuntimeError` for a directory that is not usable, outside a repository, or
    when git cannot be run. A revision or range that git rejects raises
    `ValueError` that names it. Every read leaves the repository as it was.
    """

    def __init__(self, environment: Environment) -> None:
        """Keep the environment that tells where the working directory is.

        Args:
            environment: Reports the working directory git runs in.
        """
        ...

    def rev_parse(self, revision: str) -> str:
        """Resolve a revision to a full commit id.

        Args:
            revision: A revision such as `HEAD`.

        Returns:
            The full 40-character id.

        Raises:
            ValueError: If git rejects the revision.
        """
        ...

    def history(self, revision_range: str) -> Sequence[Commit]:
        """List the commits of a revision range.

        Args:
            revision_range: A range such as `main..HEAD`.

        Returns:
            The commits oldest first, parents before children, a merge commit
            included, each with its full id and its message exactly as
            committed; none for an empty range.

        Raises:
            ValueError: If git rejects the range.
        """
        ...

    def first_parents(self, revision: str) -> Sequence[Commit]:
        """List a revision's ancestors along first parents.

        Args:
            revision: The revision to start from, such as `HEAD`.

        Returns:
            The commits newest first, starting with the revision's own; the
            commits that a merge brought in are not in it.

        Raises:
            ValueError: If git rejects the revision.
        """
        ...

    def list_files(self, revision: str) -> Sequence[Path]:
        """List the files of a revision's tree.

        Args:
            revision: The revision, such as `HEAD`.

        Returns:
            The paths relative to the repository root, whatever the working
            directory inside the repository is, sorted.

        Raises:
            ValueError: If git rejects the revision.
        """
        ...

    def show(self, revision: str, path: Path) -> str | None:
        """Read a file as it was at a revision.

        Args:
            revision: The revision, such as `HEAD`.
            path: The file, relative to the repository root.

        Returns:
            The file's content, or `None` when it did not exist then.

        Raises:
            ValueError: If git rejects the revision.
        """
        ...
