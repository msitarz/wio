# SPDX-License-Identifier: Apache-2.0
"""Finding the templates of a project and building a `Template` from each."""

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path

    from wio.io.ports import FileSystem
    from wio.models.config import Templates
    from wio.models.diagnostics import Diagnostic
    from wio.models.template import Template


@dataclass(frozen=True)
class Discovery:
    """What one walk of the templates directory found.

    Attributes:
        templates: The templates built, sorted by name. A template with a
            problem of its own is left out, and the others are still here.
        diagnostics: Every problem found, each an error that names its place:
            the file, the two files of a duplicate name, or the directory. They
            are sorted as `sort_diagnostics` sorts them.
    """

    templates: tuple[Template, ...]
    diagnostics: tuple[Diagnostic, ...]


def discover(root: Path, settings: Templates, files: FileSystem) -> Discovery:
    """Walk the templates directory and build a template for each marked file.

    The walk is that of the Works directory: it reads files ending in `.md` with
    their case, skips directories whose names start with `.`, follows no
    symbolic link, and takes a file for a template when its metadata block starts
    on its first line. A template is named by its file. It reads files only
    through `files` and writes none.

    A missing directory is no problem when `settings.dir` is the default
    `.agents/wio/templates`, and holds no templates. Any other directory that is
    missing, is not a directory or is a symbolic link is an error, and nothing
    is walked. A file that cannot be read or decoded, a block that cannot be
    read, a `kind` that is missing or not a string, a `shape` or `description`
    that is not a string and a name that two files share are errors too, and the
    other templates are still found.

    Args:
        root: The repository root, which `settings.dir` and the templates' paths
            are relative to.
        settings: The `[templates]` table of the config, normalized and checked
            in its shape.
        files: The port that lists directories and reads files.

    Returns:
        The templates and the diagnostics.
    """
    raise NotImplementedError
