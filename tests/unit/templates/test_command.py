# SPDX-License-Identifier: Apache-2.0
"""Tests of `TemplatesCommand` in `wio.templates`, run against fakes."""

from argparse import Namespace
from dataclasses import dataclass
lazy from pathlib import Path

import pytest

from tests.unit.fakes import ROOT, FakeRepository, FakeStdio, MemoryFileSystem
from wio.models.config import Config, Templates
from wio.models.frozen import freeze
from wio.templates import TemplatesCommand, TemplatesError

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


def _run(files: dict[Path, str], kind: str | None = None) -> tuple[FakeStdio, int]:
    """Run `wio templates list` over files and a config that declares two kinds.

    Args:
        files: The stored files.
        kind: The value of `--kind`, or `None`.

    Returns:
        The streams and the exit code.
    """
    kinds = freeze({"feature": "feature.draft", "spec": "spec.draft"})
    settings = _Settings(Config(templates=Templates(kinds=kinds)))
    command = TemplatesCommand(settings, FakeRepository(), MemoryFileSystem(files))
    streams = FakeStdio()
    args = Namespace(
        templates_view="list", templates_help=lambda: "usage", kind=kind, json=False
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
