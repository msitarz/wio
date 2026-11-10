# SPDX-License-Identifier: Apache-2.0
"""Showing a template as the skeleton of a contract."""

from functools import partial
from pathlib import PurePosixPath
from typing import TYPE_CHECKING

from wio.formats.errors import (
    MetadataBlockError,
    NotATemplateError,
    TemplateDirectiveError,
)
from wio.models.diagnostics import Diagnostic
from wio.templates.errors import TemplatesError, refusal
lazy from wio.formats import prepare_skeleton

_error = partial(Diagnostic, "error")
"""Make an error diagnostic from a place and a message."""

if TYPE_CHECKING:
    from pathlib import Path

    from wio.io.ports import FileSystem
    from wio.models.template import Template
    from wio.templates.discovery import Discovery


def show_skeleton(name: str, found: Discovery, root: Path, files: FileSystem) -> str:
    """Prepare the template with a name as the skeleton of a contract.

    The name is matched exactly, with its case, against the names of the
    templates that were found, and a kind is not a name. The template's text is
    read through `files`, and the skeleton function of `wio.formats` prepares it.
    That function knows no file, so an error it raises is given the file of the
    template here, as a diagnostic whose place is the file's path relative to
    `root` with `/`, followed by `:<line>` and, for a directive list, `:<column>`.
    A text with no block has no line, so its place is the bare path. A failure to
    read the file after the walk found it, an `OSError` or a `UnicodeDecodeError`,
    is worded the way the walk words it, as one diagnostic for the file.

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
            given and lists the names that exist in the order the walk returns
            them, which is sorted, or says that no template exists when there is
            none; or preparing or reading the skeleton failed, and the error
            carries one diagnostic for the template's file and ends with
            `CHECK_HINT`.
    """
    template = _named(name, found)
    place = PurePosixPath(template.path).as_posix()
    try:
        return prepare_skeleton(name, files.read_text(root / template.path))
    except UnicodeDecodeError as error:
        raise refusal([_error(place, "The file is not valid UTF-8")]) from error
    except OSError as error:
        message = f"The file cannot be read: {error.strerror}"
        raise refusal([_error(place, message)]) from error
    except TemplateDirectiveError as error:
        where = f"{place}:{error.line}:{error.column}"
        raise refusal([_error(where, error.message)]) from error
    except MetadataBlockError as error:
        raise refusal([_error(f"{place}:{error.line}", error.message)]) from error
    except NotATemplateError as error:
        raise refusal([_error(place, str(error))]) from error


def _named(name: str, found: Discovery) -> Template:
    """Find the template with a name.

    Args:
        name: The name asked for, matched exactly.
        found: What the walk found.

    Returns:
        The template.

    Raises:
        TemplatesError: No template has the name; the message names it and lists
            the names that exist, or says that none exists.
    """
    for template in found.templates:
        if template.name == name:
            return template
    names = ", ".join(f"`{template.name}`" for template in found.templates)
    known = f"the templates are {names}" if names else "no template exists"
    message = f"Unknown template `{name}`; {known}"
    raise TemplatesError(message)
