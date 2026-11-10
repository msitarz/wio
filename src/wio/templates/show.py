# SPDX-License-Identifier: Apache-2.0
"""Showing a template as the skeleton of a contract."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path

    from wio.io.ports import FileSystem
    from wio.templates.discovery import Discovery


def show_skeleton(name: str, found: Discovery, root: Path, files: FileSystem) -> str:
    """Prepare the template with a name as the skeleton of a contract.

    The name is matched exactly, with its case, against the names of the
    templates that were found, and a kind is not a name. The template's text is
    read through `files`, and the skeleton function of `wio.formats` prepares it.
    That function knows no file, so an error it raises is given the file of the
    template here, as a diagnostic whose place is the file's path relative to
    `root` with `/`, followed by `:<line>` and, for a directive list, `:<column>`.

    Args:
        name: The template's name, which is its file's name without `.md`.
        found: What the walk of the templates directory found. Its diagnostics
            are empty, since the caller refuses a project with a template error
            before it shows anything.
        root: The repository root, which the template's path is relative to.
        files: The port that reads the template.

    Returns:
        The skeleton's text, exactly as the skeleton function prepares it.

    Raises:
        TemplatesError: No template has the name, and the message names what was
            given and lists the names that exist; or preparing the skeleton
            failed, and the error carries one diagnostic for the template's file
            and says that `wio templates check` shows every problem.
    """
    raise NotImplementedError
