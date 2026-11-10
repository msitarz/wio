# SPDX-License-Identifier: Apache-2.0
"""The `wio templates` command: show the templates of the project."""

from typing import TYPE_CHECKING, Literal, cast

lazy from wio.formats import DIRECTIVES
lazy from wio.templates.discovery import discover
lazy from wio.templates.errors import TemplatesError, refusal
lazy from wio.templates.listing import render_list
lazy from wio.templates.reference import render_reference as render_directives
lazy from wio.templates.show import show_skeleton

if TYPE_CHECKING:
    from argparse import Namespace
    from collections.abc import Callable, Iterable

    from wio.io.ports import FileSystem, Repository, Stdio
    from wio.models.config import Templates
    from wio.models.template import Template
    from wio.ports import Settings
    from wio.templates.discovery import Discovery


class Arguments:
    """The attributes of the parsed arguments that `TemplatesCommand.run` reads.

    The parser set up by `wio.templates.describe()` sets them; the command reads
    them from the `Namespace` it is given, so this class only documents and types
    them.
    """

    templates_view: Literal["list", "show", "directives"] | None
    """The subcommand chosen, `None` for bare `wio templates`."""

    templates_help: Callable[[], str]
    """Returns the usage of `wio templates`; set by the parser, so bare
    `wio templates` prints it without loading the config."""

    kind: str | None
    """The kind that `list` is limited to; present for `list`."""

    json: bool
    """Whether `list` or `directives` writes JSON; present for both."""

    name: str
    """The name of the template that `show` prints; present for `show`."""


class TemplatesCommand:
    """Runs `wio templates`: its help, `list`, `show` and `directives`."""

    def __init__(
        self, settings: Settings, repository: Repository, files: FileSystem
    ) -> None:
        """Keep the ports the command reads through.

        Args:
            settings: Loads the config, whose `[templates]` table says where the
                templates are and which one is each kind's entry.
            repository: Finds the repository root.
            files: Lists the templates directory and reads the templates.
        """
        self._files = files
        self._settings = settings
        self._repository = repository

    def run(self, args: Namespace, stdio: Stdio) -> int:
        """Run `wio templates` as the arguments ask.

        Args:
            args: What the parser read, as `Arguments` describes it.
            stdio: Where the output and the errors go.

        Returns:
            The exit code, 0. Bare `wio templates` writes its help and loads no
            config. `list` writes the templates to `stdio.stdout`, limited to
            `--kind` when it is given, as one JSON array with `--json`, and
            nothing for a declared kind with no templates. `show` writes the
            skeleton of the template with the name, exactly as it is prepared,
            to `stdio.stdout` and nothing to `stdio.stderr`. `directives` writes
            the table of the directive grammar, as an indented list or as one
            JSON array with `--json`, and reads no config, no repository and no
            file of the project, so it works anywhere.

        Raises:
            ConfigurationError: The config has an error.
            TemplatesError: A template or the templates directory has an error,
                which `list` and `show` refuse to work around: it carries the
                errors and says that `wio templates check` shows every problem.
                Or `--kind` names a kind that the config does not declare, and
                the message names it and the declared kinds. Or `show` names a
                template that does not exist, and the message names it and lists
                the names that exist; or preparing the skeleton failed, which
                `show_skeleton` words. The command line exits 2.
        """
        arguments = cast("Arguments", args)
        if arguments.templates_view is None:
            stdio.stdout.write(arguments.templates_help())
            return 0
        if arguments.templates_view == "directives":
            # Before the config is loaded: the table is the parser's, and the
            # command reads nothing of the project, so it works anywhere.
            stdio.stdout.write(render_directives(DIRECTIVES, as_json=arguments.json))
            return 0
        config = self._settings.load()
        root = self._repository.root()
        found = discover(root, config.templates, self._files)
        _refuse_problems(found)
        if arguments.templates_view == "show":
            skeleton = show_skeleton(arguments.name, found, root, self._files)
            stdio.stdout.write(skeleton)
            return 0
        shown = _of_kind(found.templates, arguments.kind, config.templates)
        stdio.stdout.write(render_list(shown, as_json=arguments.json))
        return 0


def _refuse_problems(found: Discovery) -> None:
    """Refuse to list around a problem in the templates.

    Args:
        found: What the walk found.

    Raises:
        TemplatesError: The walk reported a diagnostic. Its message is the
            diagnostics rendered, then a line that names `wio templates check`.
    """
    if found.diagnostics:
        raise refusal(found.diagnostics)


def _of_kind(
    templates: Iterable[Template], kind: str | None, settings: Templates
) -> tuple[Template, ...]:
    """Limit the templates to one declared kind, or keep them all.

    Args:
        templates: The templates the walk found.
        kind: The kind asked for, or `None` for every kind.
        settings: The `[templates]` table, which declares the kinds.

    Returns:
        The templates of the kind, or all of them when no kind was asked for.

    Raises:
        TemplatesError: The kind is not declared.
    """
    if kind is None:
        return tuple(templates)
    _require_declared(kind, settings)
    return tuple(template for template in templates if template.kind == kind)


def _require_declared(kind: str, settings: Templates) -> None:
    """Check that a kind is one that the config declares.

    Args:
        kind: The kind asked for.
        settings: The `[templates]` table, which declares the kinds.

    Raises:
        TemplatesError: The kind is not declared; the message names it and the
            declared kinds, or says that none is declared.
    """
    if kind in settings.kinds:
        return
    declared = ", ".join(f"`{name}`" for name in sorted(settings.kinds))
    known = f"the declared kinds are {declared}" if declared else "none is declared"
    message = f"Unknown kind `{kind}`; {known}"
    raise TemplatesError(message)
