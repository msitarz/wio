# SPDX-License-Identifier: Apache-2.0
"""Preparing a template as the skeleton of a contract."""


def prepare_skeleton(name: str, text: str) -> str:
    """Prepare a template as the skeleton of a contract that follows it.

    The skeleton is the text of a contract without its `id`: a metadata block of
    the template's own form, holding `template` and then the keys and the tables
    of the template's `[contract]` table in the order the template wrote them,
    and the template's body with the directive list taken off each real heading.
    The template's own keys, such as `kind`, `shape`, `description` and
    `[actions]`, the metadata's comments, and an `id` or a `template` inside
    `[contract]` are dropped. A comment block never gets the marker, and `+++`
    front matter has `wio = 1` as its first key. The block is written with the
    line ending of the template's first line and ends with it, and the body
    follows as it was. The same template always gives the same skeleton. It
    reads no file, and `tomlkit` is imported on the first call, not when
    `wio.formats` is imported.

    Args:
        name: The template's name, which is its file's name without `.md`.
        text: The template's text, as the block reader reads it.

    Returns:
        The skeleton's text.

    Raises:
        NotATemplateError: The text has no wio metadata block.
        MetadataBlockError: The block cannot be read, as the block reader says.
        TemplateDirectiveError: A real heading's directive list is wrong. It
            carries the line of the heading in the text and the column of the
            problem.
    """
    raise NotImplementedError
