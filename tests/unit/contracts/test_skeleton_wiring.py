# SPDX-License-Identifier: Apache-2.0
"""Tests of how `skeleton` is composed from its leaves."""

from argparse import ArgumentParser, Namespace
from pathlib import Path
from typing import TYPE_CHECKING, cast
from unittest.mock import Mock

import pytest

from tests.unit.contracts.helpers import marked, services, works_tree
from tests.unit.fakes import ROOT, FakeStdio, MemoryFileSystem
from wio.contracts import ContractsCommand, ContractsError, describe
from wio.contracts import skeleton as module
from wio.contracts.skeleton import Skeleton, plan_skeleton
from wio.models.template import Template

if TYPE_CHECKING:
    import io

TEMPLATE = Template(
    "feature.parent", "feature", None, None, Path("t/p.md"), entry=False
)


def _args(*arguments: str) -> Namespace:
    """Parse the arguments of `wio contracts skeleton`.

    Args:
        arguments: What follows `skeleton`.

    Returns:
        The parsed namespace.
    """
    parser = ArgumentParser()
    describe().configure(parser)
    return parser.parse_args(["skeleton", *arguments])


def test_skeleton_refuses_a_missing_work_before_it_reads_anything(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The usage error comes before the tree, even one that is incomplete."""
    # Given a tree with a Work left out and a discovery that must not run
    files = works_tree(
        {"a/README.md": marked('id = "k3m9xq"'), "b/README.md": marked("")}
    )
    discover = Mock()
    monkeypatch.setattr(module, "discover_works", discover)
    stdio = FakeStdio()

    # When `skeleton feature.parent` runs with no `--work`
    with pytest.raises(ContractsError) as raised:
        ContractsCommand(services(files)).run(_args("feature.parent"), stdio)

    # Then the usage error points to `wio templates show`, nothing was read and
    # nothing was written
    assert "wio templates show" in str(raised.value)
    discover.assert_not_called()
    assert cast("io.StringIO", stdio.stdout).getvalue() == ""


def test_skeleton_judges_the_tree_before_the_work_and_the_template(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A Work left out refuses the command before any lookup."""
    # Given a tree with a Work left out and lookups that must not run
    files = works_tree(
        {"a/README.md": marked('id = "k3m9xq"'), "b/README.md": marked("")}
    )
    find, template = Mock(), Mock()
    monkeypatch.setattr(module, "find_by_id", find)
    monkeypatch.setattr(module, "find_template", template)
    stdio = FakeStdio()

    # When `skeleton feature.parent --work k3m9xq` runs
    with pytest.raises(ContractsError) as raised:
        ContractsCommand(services(files)).run(
            _args("feature.parent", "--work", "k3m9xq"), stdio
        )

    # Then the hint of `check` is raised and neither lookup ran
    assert "wio contracts check" in str(raised.value)
    find.assert_not_called()
    template.assert_not_called()
    assert cast("io.StringIO", stdio.stdout).getvalue() == ""


def test_skeleton_composes_the_lookups_the_plan_and_the_two_streams(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The skeleton goes to standard output and the note to standard error."""
    # Given a tree with a shared id, which does not refuse the tree, and leaves
    # that give a Work, a template and a skeleton with a note
    files = works_tree(
        {
            "a/README.md": marked('id = "a7b2c4"'),
            "b/README.md": marked('id = "a7b2c4"'),
        }
    )
    work = Mock()
    work.path = Path("w/README.md")
    find = Mock(return_value=work)
    template = Mock(return_value=TEMPLATE)
    planned = Mock(spec=Skeleton)
    planned.text = "skeleton\n"
    planned.note.return_value = "note\n"
    plan = Mock(return_value=planned)
    monkeypatch.setattr(module, "find_by_id", find)
    monkeypatch.setattr(module, "find_template", template)
    monkeypatch.setattr(module, "plan_skeleton", plan)
    stdio = FakeStdio()

    # When `skeleton feature.parent --work a7b2c4 --keep roots --keep x` runs
    code = ContractsCommand(services(files)).run(
        _args("feature.parent", "--work", "a7b2c4", "--keep", "roots", "--keep", "x"),
        stdio,
    )

    # Then the lookups got the id and the name, the plan got the template, the
    # Work, the keys, the root and the files, and each stream got its text
    assert find.call_args.args[1] == "a7b2c4"
    assert template.call_args.args[0] == "feature.parent"
    assert template.call_args.kwargs == {"entry": False}
    assert plan.call_args.args[:4] == (TEMPLATE, work, ["roots", "x"], ROOT)
    planned.note.assert_called_once_with(work.path)
    assert (
        code,
        cast("io.StringIO", stdio.stdout).getvalue(),
        cast("io.StringIO", stdio.stderr).getvalue(),
    ) == (0, "skeleton\n", "note\n")


def test_plan_skeleton_checks_the_keys_of_the_work_before_it_carries_them(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The template is prepared, the Work's keys are read again and checked."""
    # Given a template, a Work with a `roots` key and leaves that check and carry
    files = MemoryFileSystem(
        {
            ROOT / "t/p.md": marked("[contract]\nroots = []"),
            ROOT / "w/README.md": marked('id = "k3m9xq"\nroots = ["api"]'),
        }
    )
    work = Mock()
    work.path = Path("w/README.md")
    check, carry = Mock(), Mock(return_value="carried")
    prepare = Mock(return_value="prepared")
    monkeypatch.setattr(module, "check_keep", check)
    monkeypatch.setattr(module, "carry_keys", carry)
    monkeypatch.setattr(module, "prepare_skeleton", prepare)

    # When the skeleton is planned with `--keep roots`
    planned = plan_skeleton(TEMPLATE, work, ["roots"], ROOT, files)

    # Then the template was prepared under its name, the keys of the Work were
    # checked in the order of its file, and the carried skeleton is returned
    assert prepare.call_args.args[0] == "feature.parent"
    check.assert_called_once_with(["roots"], ("id", "roots"))
    carry.assert_called_once_with(
        "prepared", {"id": "k3m9xq", "roots": ["api"]}, ["roots"]
    )
    assert planned == "carried"
