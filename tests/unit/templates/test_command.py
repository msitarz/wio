# SPDX-License-Identifier: Apache-2.0
"""Tests of `TemplatesCommand` in `wio.templates`, run against fakes."""

from argparse import Namespace
from dataclasses import dataclass
from typing import TYPE_CHECKING
lazy from pathlib import Path

import pytest

from tests.unit.fakes import ROOT, FakeRepository, FakeStdio, MemoryFileSystem
from wio.errors import ConfigurationError
from wio.formats.directives import COMBINING, DIRECTIVES
from wio.models.config import Config, Templates
from wio.models.diagnostics import Diagnostic
from wio.models.frozen import freeze
from wio.templates import TemplatesCommand, TemplatesError, render_reference
from wio.templates import command as command_module
from wio.templates.errors import CHECK_HINT

if TYPE_CHECKING:
    from collections.abc import Iterable

DIR = ROOT / ".agents" / "wio" / "templates"
BLOCK = '<!-- wio\nkind = "{}"\n-->\n\n# Title\n'


@dataclass
class _Settings:
    """A `Settings` that gives a fixed config, and counts the loads."""

    config: Config
    loads: int = 0

    def load(self) -> Config:
        """Give the config.

        Returns:
            The fixed config.
        """
        self.loads += 1
        return self.config


def _run(
    files: dict[Path, str], kind: str | None = None, show: str | None = None
) -> tuple[FakeStdio, int]:
    """Run `wio templates` over files and a config that declares two kinds.

    Args:
        files: The stored files.
        kind: The value of `--kind` for `list`, or `None`.
        show: The name that `show` is given, or `None` to run `list`.

    Returns:
        The streams and the exit code.
    """
    kinds = freeze({"feature": "feature.draft", "spec": "spec.draft"})
    settings = _Settings(Config(templates=Templates(kinds=kinds)))
    command = TemplatesCommand(settings, FakeRepository(), MemoryFileSystem(files))
    streams = FakeStdio()
    args = Namespace(
        templates_view="list" if show is None else "show",
        templates_help=lambda: "usage",
        kind=kind,
        json=False,
        name=show,
    )
    return streams, command.run(args, streams)


def _text(streams: FakeStdio) -> str:
    """Read what a run wrote to standard output.

    Args:
        streams: The streams of the run.

    Returns:
        The text.
    """
    streams.stdout.seek(0)
    return streams.stdout.read()


def test_bare_templates_writes_its_help_and_loads_no_config() -> None:
    """AC-4: the help is written and the settings are never loaded."""
    # Given a command whose settings count their loads
    settings = _Settings(Config())
    command = TemplatesCommand(settings, FakeRepository(), MemoryFileSystem())
    streams = FakeStdio()
    args = Namespace(templates_view=None, templates_help=lambda: "usage: wio templates")

    # When it runs with no subcommand
    code = command.run(args, streams)

    # Then the help is written, the exit code is 0 and nothing was loaded
    assert (code, _text(streams), settings.loads) == (0, "usage: wio templates", 0)


def test_list_writes_the_templates_of_the_project() -> None:
    """AC-5: the templates found are rendered to standard output."""
    # Given two templates of the declared kind `feature`
    files: dict[Path, str] = {
        DIR / "feature.draft.md": BLOCK.format("feature"),
        DIR / "feature.leaf.md": BLOCK.format("feature"),
    }

    # When `list` runs
    streams, code = _run(files)

    # Then both are listed under the kind, with the entry marked, and it exits 0
    assert _text(streams) == ("feature\n  feature.draft [entry]\n  feature.leaf\n")
    assert code == 0


def test_a_declared_kind_with_no_templates_lists_nothing() -> None:
    """AC-5: `--kind spec` has no templates, and that is no error."""
    # Given a project whose only templates are of the kind `feature`
    files: dict[Path, str] = {DIR / "feature.draft.md": BLOCK.format("feature")}

    # When `list` runs for the declared kind `spec`
    streams, code = _run(files, "spec")

    # Then nothing is written and it exits 0
    assert (_text(streams), code) == ("", 0)


def test_a_kind_that_the_config_does_not_declare_is_refused() -> None:
    """AC-5: `--kind` names a declared kind, or the message lists the declared ones."""
    # Given a config that declares the kinds `feature` and `spec`
    files: dict[Path, str] = {DIR / "feature.draft.md": BLOCK.format("feature")}

    # When `list` runs with the kind `nosuch`
    with pytest.raises(TemplatesError) as caught:
        _run(files, "nosuch")

    # Then the error names the kind and the declared kinds, and carries no finding
    assert "`nosuch`" in str(caught.value)
    assert "`feature`, `spec`" in str(caught.value)
    assert caught.value.diagnostics == ()


def test_a_template_error_refuses_the_list_and_lists_nothing() -> None:
    """AC-6: the errors are the message, `check` is named and nothing is written."""
    # Given a valid template and one whose block does not close
    files: dict[Path, str] = {
        DIR / "feature.draft.md": BLOCK.format("feature"),
        DIR / "broken.md": "<!-- wio\nkind = 'x'\n",
    }
    streams = FakeStdio()

    # When `list` runs, with and without a kind
    for kind in (None, "feature"):
        with pytest.raises(TemplatesError) as caught:
            streams, _ = _run(files, kind)

        # Then the message holds the error and names the check, and carries the
        # finding, and standard output is empty
        message = str(caught.value)
        assert "error: .agents/wio/templates/broken.md:1:" in message
        assert "`wio templates check`" in message
        assert [d.where for d in caught.value.diagnostics] == [
            ".agents/wio/templates/broken.md:1"
        ]
        assert _text(streams) == ""


def test_a_template_error_is_reported_before_an_undeclared_kind() -> None:
    """AC-6: a broken project is refused whatever `--kind` names."""
    # Given a template that does not close
    files: dict[Path, str] = {DIR / "broken.md": "<!-- wio\nkind = 'x'\n"}

    # When `list` runs with a kind that the config does not declare
    with pytest.raises(TemplatesError) as caught:
        _run(files, "nosuch")

    # Then the error is the one of the template, not of the kind
    assert "broken.md" in str(caught.value)
    assert "nosuch" not in str(caught.value)


def test_a_template_error_refuses_show_whatever_the_name() -> None:
    """AC-3: a broken neighbour refuses even a valid template, before the name."""
    # Given a valid template and one whose block does not close
    files: dict[Path, str] = {
        DIR / "feature.draft.md": BLOCK.format("feature"),
        DIR / "broken.md": "<!-- wio\nkind = 'x'\n",
    }

    # When `show` runs for the valid template and for a name that does not exist
    for name in ("feature.draft", "nosuch"):
        with pytest.raises(TemplatesError) as caught:
            _run(files, show=name)

        # Then each is refused with the error of the broken file and the hint
        message = str(caught.value)
        assert "error: .agents/wio/templates/broken.md:1:" in message
        assert CHECK_HINT in message


class _RefusingSettings:
    """A `Settings` that refuses as the config loader does outside a repository."""

    def load(self) -> Config:
        """Refuse.

        Raises:
            ConfigurationError: Always, as for a directory outside any repository.
        """
        message = "not inside a git repository"
        raise ConfigurationError(message)


@pytest.mark.parametrize("view", ["list", "show"])
def test_a_directory_outside_a_repository_is_a_refusal_not_a_bug(view: str) -> None:
    """AC-3: the config is loaded before the root, so its refusal is the one given."""
    # Given a settings port that refuses, and a repository port that raises a
    # `RuntimeError` when asked for its root
    command = TemplatesCommand(
        _RefusingSettings(), FakeRepository(top=None), MemoryFileSystem()
    )
    args = Namespace(
        templates_view=view, templates_help=lambda: "usage", kind=None, name="x"
    )

    # When `list` or `show` runs
    with pytest.raises(ConfigurationError) as caught:
        command.run(args, FakeStdio())

    # Then the refusal of the config is raised, not the error of the repository
    assert "not inside a git repository" in str(caught.value)


@pytest.mark.parametrize("as_json", [False, True])
def test_directives_reads_nothing_of_the_project(*, as_json: bool) -> None:
    """AC-3: the table is written before the config, the root and the files."""
    # Given a command whose settings fail when loaded and whose repository fails
    # when asked for its root
    command = TemplatesCommand(
        _RefusingSettings(), FakeRepository(top=None), MemoryFileSystem()
    )
    args = Namespace(
        templates_view="directives",
        templates_help=lambda: "usage",
        kind=None,
        name=None,
        json=as_json,
    )
    streams = FakeStdio()

    # When `directives` runs
    code = command.run(args, streams)

    # Then the table of the parser is written, the exit code is 0, and neither
    # the config nor the repository was touched, or the run would have failed
    streams.stdout.seek(0)
    assert streams.stdout.read() == render_reference(
        DIRECTIVES, COMBINING, as_json=as_json
    )
    assert code == 0


def _stderr(streams: FakeStdio) -> str:
    """Read what a run wrote to standard error.

    Args:
        streams: The streams of the run.

    Returns:
        The text.
    """
    streams.stderr.seek(0)
    return streams.stderr.read()


@dataclass
class _Seen:
    """What the replaced check and rendering were given."""

    expected_args: tuple[object, ...] = ()
    check_args: tuple[object, ...] = ()
    rendered: tuple[Diagnostic, ...] = ()


def _check_run(
    monkeypatch: pytest.MonkeyPatch,
    found: list[Diagnostic],
    *,
    as_json: bool = False,
    seen: _Seen | None = None,
) -> tuple[FakeStdio, int]:
    """Run `wio templates check` with the check and its rendering replaced.

    Args:
        monkeypatch: The fixture that restores the replacements.
        found: What the replaced `check_templates` finds.
        as_json: The value of `--json`.
        seen: Where to record what the check and the rendering were given.

    Returns:
        The streams and the exit code.
    """
    record = seen if seen is not None else _Seen()

    def finds(*args: object) -> tuple[Diagnostic, ...]:
        """Record what the check is asked, and give the canned findings.

        Args:
            *args: What `check_templates` was given.

        Returns:
            The findings.
        """
        record.check_args = args
        return tuple(found)

    def renders(diagnostics: Iterable[Diagnostic], *, as_json: bool) -> str:
        """Say how many findings were rendered, and in which form.

        Args:
            diagnostics: The findings.
            as_json: Whether JSON was asked for.

        Returns:
            A line that tells both.
        """
        record.rendered = tuple(diagnostics)
        return f"{len(record.rendered)} json={as_json}\n"

    monkeypatch.setattr(command_module, "check_templates", finds)
    monkeypatch.setattr(command_module, "render_check", renders)

    def refuses(*_: object) -> None:
        """Fail the test: `check` must not walk the templates to refuse them.

        Args:
            *_: What `discover` was given.

        Raises:
            AssertionError: Always.
        """
        message = "`check` must not refuse around a template error"
        raise AssertionError(message)

    monkeypatch.setattr(command_module, "discover", refuses)
    settings = _Settings(Config(templates=Templates()))
    files = MemoryFileSystem({})
    record.expected_args = (settings.config, ROOT, files)
    command = TemplatesCommand(settings, FakeRepository(), files)
    streams = FakeStdio()
    args = Namespace(
        templates_view="check", templates_help=lambda: "usage", json=as_json
    )
    return streams, command.run(args, streams)


def test_check_exits_1_for_an_error_and_writes_what_it_rendered(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """AC-1: an error fails the check, and the output is the rendering."""
    # Given a check that finds an error and a warning
    found = [Diagnostic("error", "a.md", "x"), Diagnostic("warning", "a.md:2", "y")]

    # When `check --json` runs
    seen = _Seen()
    streams, code = _check_run(monkeypatch, found, as_json=True, seen=seen)

    # Then the check got the root, the loaded config and the file port, the
    # rendering got its findings in order and was asked for JSON, it is the only
    # output, the templates were not walked to refuse them, and the exit code is 1
    assert seen.check_args == (
        seen.expected_args[1],
        seen.expected_args[0],
        seen.expected_args[2],
    )
    assert seen.rendered == tuple(found)
    assert (_text(streams), _stderr(streams), code) == ("2 json=True\n", "", 1)


def test_check_exits_0_for_a_warning_alone_and_for_nothing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """AC-7: a warning does not fail the check, and nothing found passes."""
    # Given a check that finds only a warning, and one that finds nothing
    # When each runs
    _, warned = _check_run(monkeypatch, [Diagnostic("warning", "a.md:2", "y")])
    _, clean = _check_run(monkeypatch, [])

    # Then both exit 0
    assert (warned, clean) == (0, 0)


def test_check_with_a_config_that_is_refused_raises_before_any_check() -> None:
    """AC-1: the config's error is raised, so the command line exits 2."""

    # Given a settings port whose config has an error
    @dataclass
    class Refusing:
        """A `Settings` that refuses."""

        def load(self) -> Config:
            """Refuse.

            Raises:
                ConfigurationError: Always.
            """
            message = "bad config"
            raise ConfigurationError(message)

    command = TemplatesCommand(Refusing(), FakeRepository(), MemoryFileSystem({}))
    args = Namespace(templates_view="check", templates_help=lambda: "usage", json=False)

    # When `check` runs
    with pytest.raises(ConfigurationError) as caught:
        command.run(args, FakeStdio())

    # Then the error is the config's
    assert "bad config" in str(caught.value)
