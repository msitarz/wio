# SPDX-License-Identifier: Apache-2.0
"""The ports that `wio.contracts` consumes besides the shared ones.

The component that satisfies each is wired in by `wio.cli`; `wio.contracts`
never imports it. Provisional: `find` and `is_rejected` are required as written.
"""

from typing import Protocol

from wio.models.template import Template

class TemplateCatalog(Protocol):
    """The templates of a project, as `wio.contracts` asks for them."""

    def find(self, name: str) -> Template | None:
        """Find a template by name.

        Args:
            name: The template's name, which is its file's name without `.md`.

        Returns:
            The template, whose `path` is relative to the repository root, or
            `None` when no template that could be built has that name, so also
            for one whose file has an error that stops it being built.

        Raises:
            ConfigurationError: The config cannot be loaded.
        """
        ...

    def is_rejected(self, name: str) -> bool:
        """Tell whether `wio templates check` reports an error for a template.

        Args:
            name: The template's name, which is its file's name without `.md`.

        Returns:
            True when an error is reported for a file with that name, including
            a template that `find` does not give and the two files of a repeated
            name, and false for a warning alone, for a name that no file has,
            and for every name when the templates directory itself is refused.

        Raises:
            ConfigurationError: The config cannot be loaded.
        """
        ...
