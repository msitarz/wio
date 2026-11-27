# SPDX-License-Identifier: Apache-2.0
"""Resolution of paths through the filesystem port."""

from typing import TYPE_CHECKING

from wio.io.adapters import LocalFileSystem

if TYPE_CHECKING:
    from pathlib import Path


def test_resolve_follows_links_for_a_missing_target(tmp_path: Path) -> None:
    """A missing file below a symbolic link resolves to its real path."""
    # Given a link to a directory and a file not yet written inside it
    target = tmp_path / "target"
    target.mkdir()
    link = tmp_path / "link"
    link.symlink_to(target, target_is_directory=True)

    # When the missing file's path is resolved
    found = LocalFileSystem().resolve(link / "missing.md")

    # Then the path names the file under the real directory
    assert found == target.resolve() / "missing.md"
