# SPDX-License-Identifier: Apache-2.0
"""Tests of how `show` finds a Work and its actions."""

from argparse import Namespace
from pathlib import Path
from typing import TYPE_CHECKING, cast

import pytest

from tests.unit.contracts.helpers import BASE, services, work_under_works
from tests.unit.fakes import ROOT, FakeStdio, MemoryFileSystem
from wio.contracts import ContractsError
from wio.contracts.context_view import ContractViews
from wio.contracts.discovery import discover_works
from wio.contracts.hierarchy import build_hierarchy
from wio.contracts.refusal import HINT
from wio.contracts.showing import (
    Related,
    find_target,
    gather_work,
    run_show,
    shown_actions,
)
from wio.models.config import Action, Config, Defaults, Works
from wio.models.frozen import freeze
from wio.models.template import Template

if TYPE_CHECKING:
    import io
    from collections.abc import Collection, Mapping
    from unittest.mock import Mock

    from wio.contracts.ports import TemplateCatalog
    from wio.models.works import Work

DIRECTORY = ROOT / BASE / "p"
SETTINGS = Works(hierarchy="nesting")


def _marked(block: str, body: str = "# Title\n") -> str:
    """Write a file with a metadata block.

    Args:
        block: The lines of the block.
        body: The text after it.

    Returns:
        The text of the file.
    """
    return f"<!-- wio\n{block}\n-->\n\n{body}"


def _tree(files: Mapping[str, str]) -> MemoryFileSystem:
    """Put files under the Works directory.

    Args:
        files: The files, by path relative to the Works directory.

    Returns:
        The file system, which also has an unmarked `README.md` at the root.
    """
    disk = {ROOT / BASE / name: text for name, text in files.items()}
    return MemoryFileSystem({ROOT / "README.md": "# Repository\n", **disk})


def _find(files: MemoryFileSystem, argument: str, directory: Path = ROOT) -> Work:
    """Look an argument up in a tree.

    Args:
        files: The tree.
        argument: The id or the path.
        directory: The working directory.

    Returns:
        The Work.
    """
    discovery = discover_works(ROOT, SETTINGS, files)
    return find_target(discovery, argument, ROOT, directory, SETTINGS, files)


CHILD = _marked('id = "k3m9xq"\ntemplate = "feature.leaf"')
TREE = {
    "p/README.md": _marked('id = "p5n2hv"'),
    "p/c/README.md": CHILD,
    "p/s/README.md": _marked('id = "a7b2c4"'),
}


def test_an_argument_with_a_slash_or_a_md_ending_is_a_path_and_any_other_is_an_id() -> (
    None
):
    """AC-3: path or id."""
    # Given Works and the arguments `<path>`, `k3m9xq` and `a/b`
    files = _tree(TREE)

    # When `find_target` runs on each
    by_path = _find(files, f"{BASE}/p/c/README.md")
    by_id = _find(files, "k3m9xq")

    # Then the path and the id give the Work, and `a/b` is a path, so it cannot
    # be the id of a Work
    assert by_path == by_id
    assert by_id.id == "k3m9xq"
    with pytest.raises(ContractsError, match=r"a/b"):
        _find(files, "a/b")


def test_a_relative_path_is_resolved_against_the_working_directory() -> None:
    """AC-3: a path from a subdirectory."""
    # Given the Works of AC-1 and the working directory `.agents/wio/works/p`
    files = _tree(TREE)

    # When `find_target` runs on `c/README.md`
    work = _find(files, "c/README.md", DIRECTORY)

    # Then it gives the Work `k3m9xq`, and `../p/c/README.md` gives it too
    assert work.id == "k3m9xq"
    assert _find(files, "../p/c/README.md", DIRECTORY).id == "k3m9xq"


def test_an_unknown_id_names_itself_and_the_closest_id_when_there_is_one() -> None:
    """AC-3: an id that no Work has."""
    # Given the Works of AC-1
    files = _tree(TREE)

    # When `find_target` runs on `k3m9xr` and `zzzzzz`
    with pytest.raises(ContractsError) as close:
        _find(files, "k3m9xr")
    with pytest.raises(ContractsError) as far:
        _find(files, "zzzzzz")

    # Then the first raises ``No Work has the id `k3m9xr`. Did you mean
    # `k3m9xq`?`` and the second the same without the question
    assert str(close.value) == "No Work has the id `k3m9xr`. Did you mean `k3m9xq`?"
    assert str(far.value) == "No Work has the id `zzzzzz`."


def test_a_shared_id_refuses_only_its_own_lookup() -> None:
    """AC-3: a shared id."""
    # Given two Works with the id `a7b2c4` and a Work that lists it
    files = _tree(
        {
            "a/README.md": _marked('id = "a7b2c4"'),
            "b/README.md": _marked('id = "a7b2c4"'),
            "c/README.md": _marked('id = "k3m9xq"\ndepends_on = ["a7b2c4"]'),
        }
    )

    # When `find_target` runs on `a7b2c4` and on the other Work
    with pytest.raises(ContractsError) as raised:
        _find(files, "a7b2c4")
    other = _find(files, "k3m9xq")

    # Then the first raises the error of discovery with both paths and the hint,
    # and the other Work is found
    message = str(raised.value)
    assert "a/README.md" in message
    assert "b/README.md" in message
    assert message.endswith(HINT)
    assert other.id == "k3m9xq"


def test_a_file_that_is_not_a_work_gives_the_reason_of_discovery() -> None:
    """AC-3: a file that is not a Work."""
    # Given an unmarked file, a path that does not exist and a file outside the
    # Works directory
    files = _tree({**TREE, "p/notes.md": "# Notes\n"})
    arguments = [f"{BASE}/p/notes.md", f"{BASE}/p/missing.md", "README.md"]

    # When `find_target` runs on each
    messages = []
    for argument in arguments:
        with pytest.raises(ContractsError) as raised:
            _find(files, argument)
        messages.append(str(raised.value))

    # Then each raises an error that names the path and a different reason
    assert all(a in m for a, m in zip(arguments, messages, strict=True))
    assert len(set(messages)) == len(messages)


class _Catalog:
    """A stub `TemplateCatalog` over the templates it was given."""

    def __init__(self, names: Collection[str], rejected: Collection[str] = ()) -> None:
        """Keep the templates the catalog knows and the ones it rejects.

        Args:
            names: The names of the templates that `find` gives, each with its
                file at `templates/<name>.md`.
            rejected: The names that `is_rejected` says are rejected.
        """
        self._names = frozenset(names)
        self._rejected = frozenset(rejected)

    def find(self, name: str) -> Template | None:
        """Find a template.

        Args:
            name: The template's name.

        Returns:
            The template, or `None` for a name the stub does not know.
        """
        if name not in self._names:
            return None
        return Template(
            name, "feature", None, None, Path(f"templates/{name}.md"), entry=False
        )

    def is_rejected(self, name: str) -> bool:
        """Say whether a template is rejected.

        Args:
            name: The template's name.

        Returns:
            Whether the stub rejects it.
        """
        return name in self._rejected


def _template(files: MemoryFileSystem, name: str, actions: str) -> None:
    """Write the file of a template that has `[actions]`.

    Args:
        files: The file system.
        name: The template's name.
        actions: The lines of its `[actions]` table.
    """
    block = f'kind = "feature"\n[actions]\n{actions}'
    files.files[ROOT / "templates" / f"{name}.md"] = _marked(block, "# Leaf\n")


CONFIG = Config(
    actions=freeze(
        {
            "define": Action("Define."),
            "deliver": Action("Deliver."),
            "amend": Action("Amend.", on_demand=True),
        }
    ),
    stage_presets=freeze({"define-feature": ("define", "review-contract")}),
    works=Works(defaults=Defaults(actions=freeze({"deliver": ("build",)}))),
)


def _actions(
    work: Work,
    files: MemoryFileSystem | None = None,
    catalog: _Catalog | None = None,
    config: Config = CONFIG,
) -> list[tuple[str, str, bool, str | None, tuple[str, ...], bool]]:
    """Resolve the actions of a Work and flatten them for comparison.

    Args:
        work: The Work.
        files: The file system, with any template files.
        catalog: The catalog, which knows no template when none is given.
        config: The config.

    Returns:
        Each action as its name, source, on-demand flag, preset, stages and
        whether it is removed.
    """
    shown = shown_actions(
        work,
        config,
        cast("TemplateCatalog", catalog or _Catalog([])),
        ROOT,
        files or MemoryFileSystem(),
    )
    return [
        (a.name, a.source, a.on_demand, a.preset, a.stages, a.removed) for a in shown
    ]


def test_the_actions_follow_the_config_then_the_names_it_does_not_declare() -> None:
    """AC-1: actions in the order of the config."""
    # Given a config declaring `define`, `deliver` and `amend`, a template that
    # gives an undeclared `ratify` and a Work whose own `[actions]` give an
    # undeclared `deploy`
    files = MemoryFileSystem()
    _template(files, "t", 'deliver = ["build"]\nratify = ["ship"]\n')
    work = work_under_works(
        "a/README.md", "k3m9xq", template="t", actions={"deploy": ("ship",)}
    )

    # When `shown_actions` runs
    names = [a[0] for a in _actions(work, files, _Catalog(["t"]))]

    # Then the declared actions come first in the config's order, then `deploy`,
    # which the Work lists, and then `ratify`, as written
    assert names == ["deliver", "deploy", "ratify"]


def test_the_defaults_apply_only_without_a_template_and_own_actions_replace() -> None:
    """AC-1: defaults and an override."""
    # Given a Work with no template and one with a template, both with
    # `[works.defaults.actions]`, and an own `deliver` that replaces
    files = MemoryFileSystem()
    _template(files, "t", 'amend = ["ship"]\n')
    plain = work_under_works("a/README.md", "k3m9xq")
    named = work_under_works("b/README.md", "k5m8ps", template="t")
    replaced = work_under_works("c/README.md", "n5p7qr", actions={"deliver": ("ship",)})
    catalog = _Catalog(["t"])

    # When `shown_actions` runs on each
    first = _actions(plain, files, catalog)
    second = _actions(named, files, catalog)
    third = _actions(replaced, files, catalog)

    # Then the first has the defaults and the second only its template, each with
    # the sources saying which, and the own action replaces the default
    assert first == [("deliver", "defaults", False, None, ("build",), False)]
    assert second == [("amend", "template", True, None, ("ship",), False)]
    assert third == [("deliver", "contract", False, None, ("ship",), False)]


def test_an_emptied_action_is_removed_and_an_empty_one_is_not_shown() -> None:
    """AC-1: removed and empty actions."""
    # Given a template with `amend` and a Work whose `[actions]` empty `amend` and
    # `ratify`
    files = MemoryFileSystem()
    _template(files, "t", 'amend = ["ship"]\n')
    work = work_under_works(
        "a/README.md", "k3m9xq", template="t", actions={"amend": (), "ratify": ()}
    )

    # When `shown_actions` runs
    shown = _actions(work, files, _Catalog(["t"]))

    # Then `amend` is removed with the source `contract`, and `ratify` is not
    # shown
    assert shown == [("amend", "contract", True, None, (), True)]


def test_a_work_whose_actions_are_all_emptied_has_them_removed() -> None:
    """AC-1: all actions removed."""
    # Given a template with `deliver` and `amend` and a Work whose `[actions]`
    # empty both
    files = MemoryFileSystem()
    _template(files, "t", 'deliver = ["build"]\namend = ["ship"]\n')
    work = work_under_works(
        "a/README.md", "k3m9xq", template="t", actions={"deliver": (), "amend": ()}
    )

    # When `shown_actions` runs
    shown = _actions(work, files, _Catalog(["t"]))

    # Then both are given as removed with the source `contract`
    assert shown == [
        ("deliver", "contract", False, None, (), True),
        ("amend", "contract", True, None, (), True),
    ]


def test_a_work_with_nothing_to_resolve_has_no_action() -> None:
    """AC-1: a Work that resolves to no action."""
    # Given a config with no defaults and a Work with no template and no
    # `[actions]`
    work = work_under_works("a/README.md", "k3m9xq")

    # When `shown_actions` runs
    shown = _actions(work, config=Config())

    # Then it gives no action
    assert shown == []


@pytest.mark.parametrize("failure", ["missing", "rejected", "unreadable"])
def test_a_template_the_catalog_lacks_or_rejects_gives_no_actions(failure: str) -> None:
    """AC-1: a template that cannot be used."""
    # Given a Work whose template is missing from the catalog, one whose template
    # is rejected and one whose template file cannot be read, each with an own
    # action
    files = MemoryFileSystem()
    _template(files, "t", 'amend = ["ship"]\n')
    if failure == "unreadable":
        files.broken[ROOT / "templates/t.md"] = PermissionError("no")
    catalog = _Catalog(
        [] if failure == "missing" else ["t"],
        rejected=["t"] if failure == "rejected" else [],
    )
    work = work_under_works(
        "a/README.md", "k3m9xq", template="t", actions={"deliver": ("ship",)}
    )

    # When `shown_actions` runs
    shown = _actions(work, files, catalog)

    # Then only the Work's own actions are given
    assert shown == [("deliver", "contract", False, None, ("ship",), False)]


def test_a_preset_is_given_with_its_stages_and_an_undeclared_one_with_none() -> None:
    """AC-5: an undeclared preset."""
    # Given a Work whose actions name a declared and an undeclared stage preset
    work = work_under_works(
        "a/README.md",
        "k3m9xq",
        actions={"define": "define-feature", "ratify": "nosuch"},
    )

    # When `shown_actions` runs, with no defaults
    shown = _actions(work, config=Config(stage_presets=CONFIG.stage_presets))

    # Then the declared preset has its stages, and the undeclared one is kept as
    # written with no stages
    assert shown == [
        (
            "define",
            "contract",
            False,
            "define-feature",
            ("define", "review-contract"),
            False,
        ),
        ("ratify", "contract", False, "nosuch", (), False),
    ]


def test_related_works_are_found_by_id_and_a_missing_or_shared_id_is_told() -> None:
    """AC-3: related works."""
    # Given a Work that lists a missing id, the id of a Work with no title and an
    # id that two Works share
    files = _tree(
        {
            "a/README.md": _marked('id = "k3m9xq"'),
            "b/README.md": _marked('id = "n5p7qr"', ""),
            "c/README.md": _marked('id = "a7b2c4"', "# Twin\n"),
            "d/README.md": _marked('id = "a7b2c4"', "# Twin two\n"),
        }
    )
    works = list(discover_works(ROOT, SETTINGS, files).works)
    lister = work_under_works(
        "a/README.md", "k3m9xq", depends_on=("y4k2mq", "n5p7qr", "a7b2c4")
    )
    found = build_hierarchy([lister, *works[1:]], "nesting")

    # When `gather_work` runs
    shown = gather_work(lister, found, Config(), services(files))

    # Then the missing id is not found, the untitled Work has no title and the
    # shared id is once for each Work
    assert shown.depends_on == (
        Related("y4k2mq", None, found=False),
        Related("n5p7qr", None, found=True),
        Related("a7b2c4", "Twin", found=True),
        Related("a7b2c4", "Twin two", found=True),
    )


def test_the_resolved_roots_and_the_dependents_come_from_the_hierarchy() -> None:
    """AC-2: roots and dependents."""
    # Given a parent that lists `@descendants` and two Works that list a sibling
    parent = work_under_works("p/README.md", "p5n2hv", roots=("e2e", "@descendants"))
    child = work_under_works(
        "p/c/README.md", "k3m9xq", title="Child", roots=("api",), depends_on=("a7b2c4",)
    )
    sibling = work_under_works("p/s/README.md", "a7b2c4", title="Sibling")
    other = work_under_works(
        "p/o/README.md", "k5m8ps", title="Other", depends_on=("a7b2c4",)
    )
    files = _tree(
        {
            f"{w.path.relative_to(BASE)}": _marked(f'id = "{w.id}"')
            for w in (parent, child, sibling, other)
        }
    )
    found = build_hierarchy([parent, child, sibling, other], "nesting")
    wired = services(files)

    # When `gather_work` runs on the parent and on the sibling
    first = gather_work(parent, found, Config(), wired)
    second = gather_work(sibling, found, Config(), wired)

    # Then the parent's resolved roots are its own and its children's, and the
    # sibling has both dependents in the order of their paths
    assert first.resolved_roots == ("api", "e2e")
    assert second.dependents == (
        Related("k3m9xq", "Child", found=True),
        Related("k5m8ps", "Other", found=True),
    )


def test_an_incomplete_tree_refuses_the_command_before_the_argument_is_looked_up() -> (
    None
):
    """AC-4: an incomplete tree."""
    # Given a tree with a Work left out and a good Work
    files = _tree({"a/README.md": _marked('id = "k3m9xq"'), "b/README.md": _marked("")})
    stdio = FakeStdio()

    # When `run_show` runs on the good Work
    with pytest.raises(ContractsError) as raised:
        run_show(services(files), Namespace(work="k3m9xq", json=False), stdio)

    # Then nothing is written to standard output and the error and the hint are
    # raised
    assert str(raised.value).endswith(HINT)
    assert cast("io.StringIO", stdio.stdout).getvalue() == ""


@pytest.mark.xfail(strict=True, raises=NotImplementedError)
def test_bundle_view_matches_show_for_a_child_with_inherited_sections() -> None:
    """Cover AC-1 with a parent whose template passes on its glossary."""
    # Given a child whose parent passes on a glossary through its template
    files = _tree(
        {
            "p/README.md": _marked(
                'id = "p5n2hv"\ntemplate = "feature.parent"',
                "# Parent\n\n## Glossary\n\nA term and its meaning.\n",
            ),
            "p/c/README.md": _marked('id = "k3m9xq"', "# Child\n"),
        }
    )
    path = Path("templates/feature.parent.md")
    files.files[ROOT / path] = _marked(
        'wio = 1\nkind = "feature"', "## Glossary <!-- wio: inherit -->\n"
    )
    wired = services(files, Config(works=SETTINGS))
    catalog = cast("Mock", wired.catalog)
    catalog.find.return_value = Template(
        "feature.parent", "feature", "parent", None, path, entry=False
    )
    catalog.is_rejected.return_value = False
    stdio = FakeStdio()
    run_show(wired, Namespace(work="k3m9xq", json=False), stdio)
    shown = cast("io.StringIO", stdio.stdout).getvalue().split("\n----\n\n", 1)[1]

    # When the contract's resolved view is requested for the bundle
    provider = ContractViews(wired)
    view = provider.view(provider.resolved("k3m9xq"))

    # Then the whole view matches show, including the inherited glossary
    assert "### Glossary\n\nA term and its meaning." in shown
    assert view == shown


@pytest.mark.xfail(strict=True, raises=NotImplementedError)
def test_bundle_view_is_empty_for_a_contract_with_only_metadata() -> None:
    """Cover AC-2 with a Work that has neither a body nor a parent."""
    # Given a top Work with only a metadata block
    files = _tree({"c/README.md": _marked('id = "k3m9xq"', "").rstrip() + "\n"})
    provider = ContractViews(services(files, Config(works=SETTINGS)))

    # When the contract's resolved view is requested for the bundle
    view = provider.view(provider.resolved("k3m9xq"))

    # Then the view is empty
    assert view == ""


@pytest.mark.xfail(strict=True, raises=NotImplementedError)
@pytest.mark.parametrize(
    "tree",
    [
        {"a/README.md": _marked('id = "a7b2c4"')},
        {
            "a/README.md": _marked('id = "a7b2c4"'),
            "a/other.md": _marked('id = "p5n2hv"'),
            "c/README.md": _marked('id = "k3m9xq"'),
        },
        {
            "a/README.md": _marked('id = "k3m9xq"'),
            "c/README.md": _marked('id = "k3m9xq"'),
        },
    ],
    ids=["unknown-id", "incomplete-tree", "shared-id"],
)
def test_bundle_view_refuses_the_same_work_as_show(tree: dict[str, str]) -> None:
    """Cover the refusals required by AC-3.

    Args:
        tree: The Works of one refusal scenario, by relative path.
    """
    # Given a tree that show refuses when asked for the Work
    wired = services(_tree(tree), Config(works=SETTINGS))
    with pytest.raises(ContractsError) as shown:
        run_show(wired, Namespace(work="k3m9xq", json=False), FakeStdio())

    # When the same Work is requested for the bundle
    with pytest.raises(ContractsError) as refused:
        ContractViews(wired).resolved("k3m9xq")

    # Then the refusal names the same problem as show
    assert str(refused.value) == str(shown.value)


@pytest.mark.xfail(strict=True, raises=NotImplementedError)
def test_bundle_view_resolves_a_work_with_an_optional_metadata_fault() -> None:
    """Cover AC-3 when the fault leaves the Works tree complete."""
    # Given a Work with a malformed optional field
    files = _tree({"c/README.md": _marked('id = "k3m9xq"\nroots = 42', "# Child\n")})
    provider = ContractViews(services(files, Config(works=SETTINGS)))

    # When the Work is resolved and its view printed
    contract = provider.resolved("k3m9xq")
    view = provider.view(contract)

    # Then the Work and its body are still available
    assert contract.work.id == "k3m9xq"
    assert view == "# Child\n"
