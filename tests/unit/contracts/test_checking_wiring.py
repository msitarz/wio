# SPDX-License-Identifier: Apache-2.0
"""Tests of how the check of the Works is composed from its leaves."""

from argparse import ArgumentParser, Namespace
from pathlib import Path
from typing import TYPE_CHECKING, cast
from unittest.mock import Mock

import pytest

from tests.unit.contracts.helpers import work_with_id
from tests.unit.fakes import ROOT, FakeRepository, FakeStdio, MemoryFileSystem
from wio.contracts import Services, describe
from wio.contracts import checking as module
from wio.models.config import Config, Works
from wio.models.diagnostics import Diagnostic, order_diagnostics
from wio.models.template import Template

if TYPE_CHECKING:
    import io

    from wio.models.diagnostics import Severity

BASE = ".agents/wio/works"


def _marked(work_id: str) -> str:
    """Write a file with a metadata block that holds an id.

    Args:
        work_id: The id.

    Returns:
        The text of the file.
    """
    return f'<!-- wio\nid = "{work_id}"\n-->\n\n# Title\n'


def _run(files: dict[str, str]) -> module._Run:
    """Build what the checks of one Work read from, over files.

    Args:
        files: The files, by path relative to the Works directory.

    Returns:
        The run, whose catalog is never asked.
    """
    disk = MemoryFileSystem({ROOT / BASE / name: text for name, text in files.items()})
    config = Config(works=Works(hierarchy="nesting"))
    return module._Run(  # noqa: SLF001
        ROOT,
        config,
        disk,
        Mock(),
        module.build_hierarchy([], "nesting"),
        module._Templates(ROOT, disk),  # noqa: SLF001
    )


def test_a_file_that_cannot_be_read_again_is_the_one_error_of_its_work(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """No other check runs for a Work whose block was not read."""
    # Given a reread that fails and checks that must not run
    error = Diagnostic("error", f"{BASE}/a/README.md", "The file cannot be read")
    monkeypatch.setattr(module, "_reread", Mock(return_value=error))
    later = Mock()
    monkeypatch.setattr(module, "wrong_optional_fields", later)
    monkeypatch.setattr(module, "_id_error", later)

    # When the Work is checked
    found = module._check_work(work_with_id("a"), _run({}))  # noqa: SLF001

    # Then the error is all it gives
    assert found == [error]
    later.assert_not_called()


def test_every_check_runs_for_a_work_with_the_block_that_was_read(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The leaves get the block, the template that was found and the fields."""
    # Given a block and leaves that each give one finding
    work = work_with_id("a")
    block = Mock(data={})
    template = Template("t", "k", None, None, Path("t.md"), entry=False)

    def finding(name: str) -> Mock:
        """Make a leaf that gives one finding named after it.

        Args:
            name: The name of the finding.

        Returns:
            The mock.
        """
        return Mock(return_value=[Diagnostic("warning", "a", name)])

    monkeypatch.setattr(module, "_reread", Mock(return_value=block))
    monkeypatch.setattr(
        module, "wrong_optional_fields", Mock(return_value=frozenset({"roots"}))
    )
    monkeypatch.setattr(module, "_key_warnings", finding("keys"))
    monkeypatch.setattr(module, "_id_error", finding("id"))
    monkeypatch.setattr(
        module,
        "_template_errors",
        Mock(return_value=(template, [Diagnostic("error", "a", "template")])),
    )
    monkeypatch.setattr(module, "_named_errors", finding("names"))
    resolved = finding("resolved")
    monkeypatch.setattr(module, "_resolved_errors", resolved)
    roots = finding("roots")
    monkeypatch.setattr(module, "_root_errors", roots)
    run = _run({})

    # When the Work is checked
    found = module._check_work(work, run)  # noqa: SLF001

    # Then every leaf contributed, and the resolved and root checks got the
    # template and the fields that discovery reported
    assert [d.message for d in found] == [
        "keys",
        "id",
        "template",
        "names",
        "resolved",
        "roots",
    ]
    assert resolved.call_args.args == (work, template, frozenset({"roots"}), run)
    assert roots.call_args.args[:2] == (work, frozenset({"roots"}))


def test_the_findings_of_discovery_and_the_graph_are_carried_through_once(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A shared id and a cycle are reported as they were, and not again."""
    # Given Works that share an id and two that wait on each other, and a check
    # of each Work that finds nothing
    cycle = {
        "c/README.md": '<!-- wio\nid = "c1"\ndepends_on = ["c2"]\n-->\n',
        "d/README.md": '<!-- wio\nid = "c2"\ndepends_on = ["c1"]\n-->\n',
    }
    files = {
        "a/README.md": _marked("dup"),
        "b/README.md": _marked("dup"),
        **cycle,
    }
    monkeypatch.setattr(module, "_check_work", Mock(return_value=[]))
    run = _run(files)

    # When the Works are checked
    found = module.check_works(ROOT, run.config, run.files, run.catalog)

    # Then each is reported once, in the order of `order_diagnostics`
    messages = [d.message for d in found]
    assert len([m for m in messages if "share" in m]) == 1
    assert len([m for m in messages if m.startswith("Dependency cycle")]) == 1
    assert found == order_diagnostics(found)


def test_a_template_is_read_once_however_many_works_ask(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The second ask for a template's actions is answered from the first."""
    # Given a reader of templates and a read that counts
    read = Mock(return_value={"deliver": "p"})
    monkeypatch.setattr(module, "template_actions", read)
    templates = module._Templates(ROOT, MemoryFileSystem())  # noqa: SLF001
    template = Template("t", "k", None, None, Path("t.md"), entry=False)

    # When it is asked three times
    answers = [templates.actions(template) for _ in range(3)]

    # Then the file was read once and every answer is the same
    assert read.call_count == 1
    assert answers == [{"deliver": "p"}] * 3


class _Settings:
    """A `Settings` that gives the default config."""

    def load(self) -> Config:
        """Give the config.

        Returns:
            The default settings.
        """
        return Config()


def _services() -> Services:
    """Build the services of a project.

    Returns:
        Services over an empty file system.
    """
    return Services(
        _Settings(),
        FakeRepository(),
        MemoryFileSystem(),
        Mock(),
    )


@pytest.mark.parametrize(
    ("severity", "code", "text"),
    [
        ("error", 1, "error: a: x\n"),
        ("warning", 0, "warning: a: x\n"),
        ("note", 0, "note: a: x\n"),
    ],
)
def test_the_command_writes_the_findings_and_exits_by_severity(
    monkeypatch: pytest.MonkeyPatch, severity: str, code: int, text: str
) -> None:
    """Only an error fails the command."""
    # Given a check that finds one thing of the severity
    finding = Diagnostic(cast("Severity", severity), "a", "x")
    monkeypatch.setattr(module, "check_works", Mock(return_value=(finding,)))
    stdio = FakeStdio()

    # When the command runs
    status = module.run_check(_services(), Namespace(json=False), stdio)

    # Then it wrote the line and exits by the severity
    assert cast("io.StringIO", stdio.stdout).getvalue() == text
    assert status == code


def test_the_command_says_that_the_contracts_pass_and_can_write_json(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Nothing to report is a sentence, or an empty array with `--json`."""
    # Given a check that finds nothing
    monkeypatch.setattr(module, "check_works", Mock(return_value=()))
    plain, as_json = FakeStdio(), FakeStdio()

    # When the command runs in each form
    module.run_check(_services(), Namespace(json=False), plain)
    module.run_check(_services(), Namespace(json=True), as_json)

    # Then the sentence and `[]` are written
    assert cast("io.StringIO", plain.stdout).getvalue() == "The contracts pass.\n"
    assert cast("io.StringIO", as_json.stdout).getvalue() == "[]\n"


def test_the_group_has_a_check_subcommand_with_a_json_option() -> None:
    """`wio contracts check --json` is parsed into the entry of the table."""
    # Given the parser of the group
    parser = ArgumentParser()
    describe().configure(parser)

    # When `check` is parsed with and without `--json`
    plain = parser.parse_args(["check"])
    as_json = parser.parse_args(["check", "--json"])

    # Then both choose `check`, and only the second asks for JSON
    assert (plain.contracts_subcommand, plain.json) == ("check", False)
    assert (as_json.contracts_subcommand, as_json.json) == ("check", True)
