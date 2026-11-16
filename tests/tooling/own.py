# SPDX-License-Identifier: Apache-2.0
"""What the tests of this repository's own templates and Works share."""

import hashlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = Path(sys.executable).parent / "wio"
"""The `wio` command installed beside this interpreter."""


def hash_files(directory: Path) -> dict[str, str]:
    """Hash every file below a directory.

    Args:
        directory: The directory.

    Returns:
        The SHA-256 of each file, by its path relative to the directory.
    """
    return {
        str(path.relative_to(directory)): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(directory.rglob("*"))
        if path.is_file()
    }
