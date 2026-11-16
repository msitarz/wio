# SPDX-License-Identifier: Apache-2.0
"""Tests of how `show` is composed from its leaves."""

from argparse import ArgumentParser, Namespace
from typing import TYPE_CHECKING, cast
from unittest.mock import Mock

import pytest

from tests.unit.contracts.helpers import BASE, services, work_under_works
from tests.unit.fakes import ROOT, FakeStdio, MemoryFileSystem
from wio.contracts import ContractsCommand, ContractsError, describe
from wio.contracts import showing as module
from wio.contracts.actions import ResolvedAction
from wio.contracts.discovery import discover_works
from wio.contracts.hierarchy import build_hierarchy
from wio.models.config import Config, Defaults, Works
from wio.models.frozen import freeze

if TYPE_CHECKING:
    import io

    from wio.contracts.ports import TemplateCatalog
    from wio.models.config import HierarchyMode
    from wio.models.works import Work

DIRECTORY = ROOT / BASE / "p"


def _marked(block: str) -> str:
    """Write a file with a metadata block.

    Args:
        block: The lines of the block.

    Returns:
        The text of the file.
    """
    return f"<!-- wio\n{block}\n-->\n\n# Title\n"


def _tree(files: dict[str, str]) -> MemoryFileSystem:
    """Put files under the Works directory.

    Args:
        files: The files, by path relative to the Works directory.

    Returns:
        The file system.
    """
    return MemoryFileSystem({ROOT / BASE / name: text for name, text in files.items()})


def _show_args(*arguments: str) -> Namespace:
    """Parse the arguments of `wio contracts show`.

    Args:
        arguments: What follows `show`.

    Returns:
        The parsed namespace.
    """
    parser = ArgumentParser()
    describe().configure(parser)
    return parser.parse_args(["show", *arguments])


def test_show_judges_the_tree_before_it_looks_the_argument_up(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A Work left out refuses the command, and nothing is written."""
    # Given a tree with a Work left out and a lookup that must not run
    files = _tree({"a/README.md": _marked('id = "k3m9xq"'), "b/README.md": _marked("")})
    find = Mock()
    monkeypatch.setattr(module, "find_target", find)
    stdio = FakeStdio()

    # When `show` runs on the good Work
    with pytest.raises(ContractsError) as raised:
        ContractsCommand(services(files, directory=DIRECTORY)).run(
            _show_args("k3m9xq"), stdio
        )

    # Then the errors and the hint are raised, the lookup did not run and nothing
    # was written
    assert "wio contracts check" in str(raised.value)
    find.assert_not_called()
    assert cast("io.StringIO", stdio.stdout).getvalue() == ""


@pytest.mark.parametrize("mode", ["flat", "nesting"])
def test_show_composes_the_lookup_the_gathering_and_the_rendering(
    monkeypatch: pytest.MonkeyPatch, mode: HierarchyMode
) -> None:
    """The leaves get the argument, directory and mode, and the text is written."""
    # Given a tree with a shared id, which does not refuse the tree, and leaves
    # that give a Work, what is shown of it and the text
    files = _tree(
        {
            "a/README.md": _marked('id = "a7b2c4"'),
            "b/README.md": _marked('id = "a7b2c4"'),
        }
    )
    config = Config(works=Works(hierarchy=mode))
    work = work_under_works("a/README.md", "a7b2c4")
    find = Mock(return_value=work)
    shown = Mock()
    gather = Mock(return_value=shown)
    render = Mock(return_value="text\n")
    monkeypatch.setattr(module, "find_target", find)
    monkeypatch.setattr(module, "gather_work", gather)
    monkeypatch.setattr(module, "render_show", render)
    stdio = FakeStdio()

    # When `show a7b2c4 --json` runs
    code = ContractsCommand(services(files, config, directory=DIRECTORY)).run(
        _show_args("a7b2c4", "--json"), stdio
    )

    # Then the lookup got the argument, the root and the working directory, the
    # gathering got the Work, a hierarchy and the config, and the rendering got
    # what it gathered and the JSON flag
    assert find.call_args.args[1:4] == ("a7b2c4", ROOT, DIRECTORY)
    found = gather.call_args.args[1]
    assert found.works == build_hierarchy(find_works(files), mode).works
    assert gather.call_args.args[0] is work
    assert gather.call_args.args[2] is config
    render.assert_called_once_with(shown, as_json=True)
    assert (code, cast("io.StringIO", stdio.stdout).getvalue()) == (0, "text\n")


def find_works(files: MemoryFileSystem) -> list[Work]:
    """Read the Works that a tree holds.

    Args:
        files: The files of the tree.

    Returns:
        The Works as discovery found them.
    """

    return list(discover_works(ROOT, Works(), files).works)


@pytest.mark.parametrize(
    ("argument", "lookup"),
    [
        ("p/c/README.md", "path"),
        ("notes.md", "path"),
        ("a/b", "path"),
        ("k3m9xq", "id"),
    ],
)
def test_an_argument_is_a_path_when_it_has_a_slash_or_ends_in_md(
    monkeypatch: pytest.MonkeyPatch, argument: str, lookup: str
) -> None:
    """The form of the argument chooses the lookup, and the other is not run."""
    # Given leaves for a path and for an id
    work = work_under_works("a/README.md", "k3m9xq")
    by_path = Mock(return_value=work)
    by_id = Mock(return_value=work)
    monkeypatch.setattr(module, "_by_path", by_path)
    monkeypatch.setattr(module, "_by_id", by_id)

    # When the argument is looked up
    found = module.find_target(Mock(), argument, ROOT, DIRECTORY, Works(), Mock())

    # Then only the lookup of its form ran, and it gave the Work
    assert found is work
    assert (by_path.called, by_id.called) == (lookup == "path", lookup == "id")


def test_the_view_the_parent_and_the_relations_come_from_the_hierarchy(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The gathering assembles the Work from the hierarchy, the actions and the view."""
    # Given a parent, a child that lists a sibling and a dependent of the child,
    # and leaves that give the related dependencies and the actions
    parent = work_under_works("p/README.md", "p5n2hv", roots=("e2e", "@descendants"))
    child = work_under_works(
        "p/c/README.md", "k3m9xq", depends_on=("a7b2c4",), roots=("api",)
    )
    sibling = work_under_works("p/s/README.md", "a7b2c4", title=None)
    other = work_under_works("p/o/README.md", "k5m8ps", depends_on=("k3m9xq",))
    files = _tree(
        {"p/c/README.md": _marked('id = "k3m9xq"') + "\nOwn.\n"}
        | {"p/README.md": _marked('id = "p5n2hv"')}
    )
    found = build_hierarchy([parent, child, sibling, other], "nesting")
    related = (module.Related("a7b2c4", None, found=True),)
    monkeypatch.setattr(module, "_related_ids", Mock(return_value=related))
    actions = (Mock(),)
    monkeypatch.setattr(module, "shown_actions", Mock(return_value=actions))
    wired = services(files, directory=DIRECTORY)

    # When the child is gathered
    shown = module.gather_work(child, found, Config(), wired)

    # Then the parent, the resolved roots, the dependents, the dependencies and
    # the actions are the leaves' and the hierarchy's, and the view is the Work's
    assert shown.parent == module.Related("p5n2hv", None, found=True)
    assert shown.resolved_roots == ("api",)
    assert shown.dependents == (module.Related("k5m8ps", None, found=True),)
    assert shown.depends_on == related
    assert shown.actions == actions
    assert shown.view.startswith("<!--") is False
    assert "Own." in shown.view


def test_a_top_work_has_no_parent(monkeypatch: pytest.MonkeyPatch) -> None:
    """A Work with no parent has none in what is gathered."""
    # Given a Work alone in a flat tree
    work = work_under_works("a/README.md", "k3m9xq")
    files = _tree({"a/README.md": _marked('id = "k3m9xq"')})
    found = build_hierarchy([work], "flat")
    monkeypatch.setattr(module, "_related_ids", Mock(return_value=()))
    monkeypatch.setattr(module, "shown_actions", Mock(return_value=()))

    # When it is gathered
    shown = module.gather_work(
        work, found, Config(), services(files, directory=DIRECTORY)
    )

    # Then it has no parent
    assert shown.parent is None


def test_a_work_with_no_template_takes_the_defaults_and_not_a_template(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The defaults are layered under a Work that names no template, and only then."""
    # Given a config with defaults, a Work that overrides one action and a leaf
    # that orders what it is given
    config = Config(
        works=Works(defaults=Defaults(actions=freeze({"deliver": ("build",)})))
    )
    work = work_under_works("a/README.md", "k3m9xq", actions={"deliver": ("ship",)})
    order = Mock(return_value=())
    monkeypatch.setattr(module, "_in_config_order", order)
    pipelines = Mock()
    monkeypatch.setattr(module, "_template_pipelines", pipelines)

    # When its actions are resolved
    module.shown_actions(work, config, Mock(), ROOT, MemoryFileSystem())

    # Then the Work's own action replaces the default, the source is the Work's,
    # and no template was read
    resolved = order.call_args.args[0]
    assert resolved == (ResolvedAction("deliver", ("ship",), "work", removed=False),)
    pipelines.assert_not_called()


def test_a_work_with_a_template_takes_its_actions_and_never_the_defaults(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A named template is the only source of default actions."""
    # Given defaults, a template that gives `deliver` and `amend`, and a Work that
    # empties `amend`
    config = Config(
        works=Works(defaults=Defaults(actions=freeze({"ratify": ("build",)})))
    )
    work = work_under_works(
        "a/README.md", "k3m9xq", template="t", actions={"amend": ()}
    )
    order = Mock(return_value=())
    monkeypatch.setattr(module, "_in_config_order", order)
    pipelines = Mock(return_value={"deliver": ("build",), "amend": ("amend",)})
    monkeypatch.setattr(module, "_template_pipelines", pipelines)
    catalog = cast("TemplateCatalog", Mock())

    # When its actions are resolved
    module.shown_actions(work, config, catalog, ROOT, MemoryFileSystem())

    # Then the template was read for its name, the default is not in the result,
    # the template's action has the source `template` and the emptied one is
    # removed
    assert pipelines.call_args.args[0] == "t"
    assert order.call_args.args[0] == (
        ResolvedAction("deliver", ("build",), "template", removed=False),
        ResolvedAction("amend", (), "work", removed=True),
    )
