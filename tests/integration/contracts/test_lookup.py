# SPDX-License-Identifier: Apache-2.0
"""Tests of `WorkLookup` on a real repository with real git behind it.

The examples use a Work `k3m9xq`, a leaf under a parent that has a constraint
`C-1`, with the items `AC-1` and `AC-3` in its own sections, whose `deliver` is
the `typed-boundary` stage preset. The config and the templates are those of this
repository. "The working-tree adapter" is the lookup over the working tree and
`HEAD`, and "the index adapter" is the lookup over the index and `HEAD`.
"""

import json
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, override

import pytest

from tests.support import enter, git
from wio.config import ConfigSettings
from wio.contracts.lookup import WorkLookup
from wio.env.adapters import ProcessEnvironment
from wio.io import adapters
from wio.io.views import HeadFiles, IndexFiles
from wio.templates import TemplatesCatalog

if TYPE_CHECKING:
    from tests.sandbox import Sandbox

REPO = Path(__file__).resolve().parents[3]
WORKS = Path(".agents/wio/works")
TYPED_BOUNDARY = [
    "architecture",
    "architecture-review",
    "wiring",
    "wiring-review",
    "implementation",
    "implementation-review",
    "promote-docs",
    "docs-review",
]


@dataclass(frozen=True)
class Project:
    """The lookups over a repository.

    Attributes:
        root: The repository root.
        working: The lookup over the working tree and `HEAD`.
        index: The lookup over the index and `HEAD`.
    """

    root: Path
    working: WorkLookup
    index: WorkLookup


def _work(
    work_id: str,
    *,
    items: tuple[str, ...] = ("AC-1",),
    constraints: tuple[str, ...] = (),
    actions: dict[str, list[str]] | None = None,
    roots: tuple[str, ...] | None = None,
) -> str:
    """Write the text of a leaf Work.

    Args:
        work_id: The Work's id.
        items: The ids of its acceptance criteria.
        constraints: The ids of its constraints, which a parent writes.
        actions: Its own `[actions]`, by action name.
        roots: Its `roots`, or `None` to write none.

    Returns:
        The text of the contract.
    """
    table = "".join(
        f"{name} = {json.dumps(stages)}\n" for name, stages in (actions or {}).items()
    )
    section = f"\n[actions]\n{table}" if actions else ""
    listed = "" if roots is None else f"roots = {json.dumps(list(roots))}\n"
    head = (
        f'<!-- wio\nid = "{work_id}"\ntemplate = "feature.leaf"\n{listed}{section}-->\n'
    )
    criteria = "".join(f"### **{item}** A criterion\n\nText.\n\n" for item in items)
    rules = "".join(f"### {item}\n\nA constraint.\n\n" for item in constraints)
    return (
        f"{head}\n# {work_id}\n\n## Purpose\n\nWhy.\n\n## Goals\n\n- One.\n\n"
        f"## Assumptions\n\nNone.\n\n## Constraints\n\n{rules}"
        f"## Acceptance criteria\n\n{criteria}"
    )


def _write(root: Path, name: str, text: str) -> None:
    """Write a Work's file, making its directories.

    Args:
        root: The repository root.
        name: The path below the Works directory.
        text: The contract.
    """
    path = root / WORKS / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _project(
    sandbox: Sandbox,
    monkeypatch: pytest.MonkeyPatch,
    works: dict[str, str] | None = None,
    *,
    commit: bool = True,
) -> Project:
    """Create a repository with the Works of the examples and commit it.

    Args:
        sandbox: An empty repository directory.
        monkeypatch: The test's monkeypatch, which enters the sandbox.
        works: The Works to write instead of the defaults, by path below the
            Works directory.
        commit: Whether to commit them, so that `HEAD` has them.

    Returns:
        The lookups over it.
    """
    root = sandbox.root.resolve()
    git(sandbox, "init", "-q", "-b", "main", check=True)
    shutil.copy(REPO / ".agents/wio/config.toml", _config(root))
    shutil.copytree(REPO / ".agents/wio/templates", root / ".agents/wio/templates")
    shutil.copytree(REPO / ".agents/wio/rules", root / ".agents/wio/rules")
    defaults = {
        "parent/README.md": _work("a1b2c3", constraints=("C-1",)),
        "parent/k3m9xq/README.md": _work("k3m9xq", items=("AC-1", "AC-3")),
        "m5n6p7/README.md": _work("m5n6p7", actions={"deliver": ["implementation"]}),
        "d4e5f6/README.md": _work("d4e5f6", actions={"deliver": ["implementation"]}),
        "p8q9r1/README.md": _work("p8q9r1", items=()),
    }
    for name, text in (works or defaults).items():
        _write(root, name, text)
    git(sandbox, "add", "-A", check=True)
    if commit:
        git(sandbox, "commit", "-q", "-m", "base", check=True)
    enter(sandbox, monkeypatch)
    return _lookups(root)


def _config(root: Path) -> Path:
    """Make the directory of the config and name its file.

    Args:
        root: The repository root.

    Returns:
        The path of the config file.
    """
    directory = root / ".agents/wio"
    directory.mkdir(parents=True, exist_ok=True)
    return directory / "config.toml"


def _lookups(root: Path) -> Project:
    """Wire the two lookups over the repository that the process is in.

    Args:
        root: The repository root.

    Returns:
        The lookups over the working tree and over the index.
    """
    environment = ProcessEnvironment()
    repository = adapters.GitRepository(environment)
    history = adapters.GitHistory(environment)
    files = adapters.LocalFileSystem()
    settings = ConfigSettings(repository, files)
    catalog = TemplatesCatalog(settings, repository, files)
    head = HeadFiles(history, root)
    index = IndexFiles(repository, history, files, root, WORKS)
    return Project(
        root,
        WorkLookup(settings, repository, catalog, files, [files, head]),
        WorkLookup(settings, repository, catalog, files, [index, head]),
    )


@pytest.mark.slow
def test_the_items_of_a_work_are_its_own(
    sandbox: Sandbox, monkeypatch: pytest.MonkeyPatch
) -> None:
    """AC-1: the working-tree adapter returns the Work's items and not the parent's."""
    # Given `k3m9xq` in the working tree
    project = _project(sandbox, monkeypatch)

    # When `items("k3m9xq")` runs on the working-tree adapter
    items = project.working.items("k3m9xq")

    # Then it returns `AC-1` and `AC-3` and not `C-1`
    assert items == frozenset({"AC-1", "AC-3"})


@pytest.mark.slow
def test_the_pipeline_of_an_action_is_found_in_order(
    sandbox: Sandbox, monkeypatch: pytest.MonkeyPatch
) -> None:
    """AC-2: an action the Work has, and one it lacks."""
    # Given `k3m9xq` in the working tree
    project = _project(sandbox, monkeypatch)

    # When `pipeline("k3m9xq", "deliver")` and `pipeline("k3m9xq", "nosuch")` run
    deliver = project.working.pipeline("k3m9xq", "deliver")
    missing = project.working.pipeline("k3m9xq", "nosuch")

    # Then the first returns the eight stages of `typed-boundary` in order and
    # the second returns `None`
    assert list(deliver or []) == TYPED_BOUNDARY
    assert missing is None


@pytest.mark.slow
def test_a_work_whose_contract_overrides_an_action_uses_its_own(
    sandbox: Sandbox, monkeypatch: pytest.MonkeyPatch
) -> None:
    """AC-2: the Work's `[actions]` replace the template's."""
    # Given a Work `m5n6p7` whose `[actions]` sets
    # `deliver = ["implementation", "implementation-review"]`
    both = ["implementation", "implementation-review"]
    project = _project(
        sandbox,
        monkeypatch,
        {"m5n6p7/README.md": _work("m5n6p7", actions={"deliver": both})},
    )

    # When `pipeline("m5n6p7", "deliver")` runs
    stages = project.working.pipeline("m5n6p7", "deliver")

    # Then it returns `implementation` and `implementation-review`
    assert list(stages or []) == both


@pytest.mark.slow
def test_a_work_that_only_head_has_is_found_by_both_adapters(
    sandbox: Sandbox, monkeypatch: pytest.MonkeyPatch
) -> None:
    """AC-3: a Work that the commit being made deletes is still found."""
    # Given a Work `d4e5f6` in `HEAD` and in neither the working tree nor the
    # index, with the item `AC-1` and `deliver` set to `["implementation"]`
    project = _project(sandbox, monkeypatch)
    git(sandbox, "rm", "-q", "-r", str(WORKS / "d4e5f6"), check=True)

    # When `items("d4e5f6")` and `pipeline("d4e5f6", "deliver")` run on each
    # adapter
    found = [
        (lookup.items("d4e5f6"), list(lookup.pipeline("d4e5f6", "deliver") or []))
        for lookup in (project.working, project.index)
    ]

    # Then each returns `AC-1` and `implementation`
    assert found == [(frozenset({"AC-1"}), ["implementation"])] * 2


@pytest.mark.slow
def test_the_items_of_the_working_tree_and_the_index_may_differ(
    sandbox: Sandbox, monkeypatch: pytest.MonkeyPatch
) -> None:
    """AC-3: each adapter reads its own tree before `HEAD`."""
    # Given `k3m9xq` with the item `AC-3` in the working tree and without it in
    # the index, which differs from `HEAD`, so that the index adapter cannot be
    # told from `HEAD`
    project = _project(
        sandbox,
        monkeypatch,
        {"parent/k3m9xq/README.md": _work("k3m9xq", items=("AC-1", "AC-9"))},
    )
    _write(project.root, "parent/k3m9xq/README.md", _work("k3m9xq", items=("AC-1",)))
    git(sandbox, "add", "-A", check=True)
    _write(
        project.root, "parent/k3m9xq/README.md", _work("k3m9xq", items=("AC-1", "AC-3"))
    )

    # When `items("k3m9xq")` runs on each adapter
    working = project.working.items("k3m9xq")
    index = project.index.items("k3m9xq")

    # Then the working-tree adapter returns `AC-1` and `AC-3` and the index
    # adapter returns `AC-1`
    assert (working, index) == (frozenset({"AC-1", "AC-3"}), frozenset({"AC-1"}))


@pytest.mark.slow
def test_the_pipelines_of_the_working_tree_and_the_index_may_differ(
    sandbox: Sandbox, monkeypatch: pytest.MonkeyPatch
) -> None:
    """AC-3: each adapter reads its own `[actions]` before `HEAD`."""
    # Given `m5n6p7` whose `deliver` is `["implementation"]` in the working tree
    # and `["implementation", "implementation-review"]` in the index
    both = ["implementation", "implementation-review"]
    project = _project(
        sandbox,
        monkeypatch,
        {"m5n6p7/README.md": _work("m5n6p7", actions={"deliver": both})},
    )
    git(sandbox, "add", "-A", check=True)
    _write(
        project.root,
        "m5n6p7/README.md",
        _work("m5n6p7", actions={"deliver": ["implementation"]}),
    )

    # When `pipeline("m5n6p7", "deliver")` runs on each adapter
    working = project.working.pipeline("m5n6p7", "deliver")
    index = project.index.pipeline("m5n6p7", "deliver")

    # Then the working-tree adapter returns `implementation` and the index
    # adapter returns `implementation` and `implementation-review`
    assert (list(working or []), list(index or [])) == (["implementation"], both)


@pytest.mark.slow
def test_a_work_with_no_items_has_an_empty_set_and_not_none(
    sandbox: Sandbox, monkeypatch: pytest.MonkeyPatch
) -> None:
    """AC-4: a Work with no item in its own sections."""
    # Given a Work `p8q9r1` that has no item in its own sections
    project = _project(sandbox, monkeypatch)

    # When `items("p8q9r1")` runs
    items = project.working.items("p8q9r1")

    # Then it returns an empty `frozenset`, not `None`
    assert items == frozenset()


@pytest.mark.slow
def test_an_action_that_the_work_removed_is_none(
    sandbox: Sandbox, monkeypatch: pytest.MonkeyPatch
) -> None:
    """AC-4: an empty list in `[actions]` removes the action."""
    # Given `k3m9xq` with `[actions]` setting `amend = []`
    project = _project(
        sandbox,
        monkeypatch,
        {"parent/k3m9xq/README.md": _work("k3m9xq", actions={"amend": []})},
    )

    # When `pipeline("k3m9xq", "amend")` runs
    stages = project.working.pipeline("k3m9xq", "amend")

    # Then it returns `None`
    assert stages is None


@pytest.mark.slow
def test_an_unknown_id_is_absent(
    sandbox: Sandbox, monkeypatch: pytest.MonkeyPatch
) -> None:
    """AC-4: an id that is in no place gives `None` for both members."""
    # Given an id `zz9zz9` that is in no place
    project = _project(sandbox, monkeypatch)

    # When `items("zz9zz9")` and `pipeline("zz9zz9", "deliver")` run
    items = project.working.items("zz9zz9")
    stages = project.working.pipeline("zz9zz9", "deliver")

    # Then both return `None`
    assert (items, stages) == (None, None)


@pytest.mark.slow
def test_an_id_that_two_works_share_is_absent_and_not_read_from_head(
    sandbox: Sandbox, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A shared id answers absent and is not looked up in the next view."""
    # Given `k3m9xq` in `HEAD`, and a second Work with the same id in the working
    # tree
    project = _project(sandbox, monkeypatch)
    _write(project.root, "twin/README.md", _work("k3m9xq"))

    # When `items("k3m9xq")` runs on the working-tree adapter
    items = project.working.items("k3m9xq")

    # Then it returns `None`, although `HEAD` holds exactly one such Work
    assert items is None


@pytest.mark.slow
def test_a_repository_with_no_commit_is_looked_up_without_an_error(
    sandbox: Sandbox, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The first commit of a repository finds the staged Works and no old one."""
    # Given a repository whose Works are staged and that has no commit
    project = _project(sandbox, monkeypatch, commit=False)

    # When a Work and an unknown id are looked up on each adapter
    found = [lookup.items("k3m9xq") for lookup in (project.working, project.index)]
    unknown = [lookup.items("zz9zz9") for lookup in (project.working, project.index)]

    # Then the Work is found, and the unknown id is absent and raises nothing
    assert found == [frozenset({"AC-1", "AC-3"})] * 2
    assert unknown == [None, None]


@pytest.mark.slow
def test_a_file_that_is_not_text_keeps_no_other_work_from_being_found(
    sandbox: Sandbox, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A Work file that is not UTF-8, committed or staged, is left out."""
    # Given a committed file below the Works directory that is not UTF-8 text, and
    # a staged one
    project = _project(sandbox, monkeypatch)
    bad = project.root / WORKS / "bad" / "README.md"
    bad.parent.mkdir()
    bad.write_bytes(b"\xff\xfe not text")
    git(sandbox, "add", "-A", check=True)
    git(sandbox, "commit", "-q", "-m", "bad", check=True)
    staged = project.root / WORKS / "staged" / "README.md"
    staged.parent.mkdir()
    staged.write_bytes(b"\xff\xfe not text")
    git(sandbox, "add", "-A", check=True)

    # When a Work and an unknown id are looked up on each adapter
    found = [lookup.items("k3m9xq") for lookup in (project.working, project.index)]
    unknown = [lookup.items("zz9zz9") for lookup in (project.working, project.index)]

    # Then the Work is found, the unknown id is absent, and nothing is raised
    assert found == [frozenset({"AC-1", "AC-3"})] * 2
    assert unknown == [None, None]


_TREE = {
    "p/README.md": _work("pppppp", roots=("e2e", "@descendants")),
    "p/a/README.md": _work("aaaaaa", roots=("api",)),
    "p/b/README.md": _work("bbbbbb", roots=("@descendants",)),
    "p/b/c/README.md": _work("cccccc", roots=("web", "web")),
    "x/README.md": _work("xxxxxx"),
    "y/README.md": _work("yyyyyy", roots=("@descendants",)),
}


@pytest.mark.slow
def test_the_expanded_roots_of_a_work_are_given_by_its_id(
    sandbox: Sandbox, monkeypatch: pytest.MonkeyPatch
) -> None:
    """AC-1: `@descendants` is expanded through the children, sorted and once."""
    # Given a tree of Works with roots in the working tree
    project = _project(sandbox, monkeypatch, _TREE)

    # When the roots of four Works are asked for
    found = [
        project.working.roots_of(i) for i in ("pppppp", "bbbbbb", "aaaaaa", "cccccc")
    ]

    # Then each is expanded, each name once and sorted
    assert found == [("api", "e2e", "web"), ("web",), ("api",), ("web",)]


@pytest.mark.slow
def test_an_unknown_work_has_no_roots_and_an_empty_one_has_an_empty_tuple(
    sandbox: Sandbox, monkeypatch: pytest.MonkeyPatch
) -> None:
    """AC-2: `None` for an id that no Work has, `()` for no roots."""
    # Given a Work with no roots and a leaf that lists `@descendants`
    project = _project(sandbox, monkeypatch, _TREE)

    # When the roots of those and of an unknown id are asked for
    found = [project.working.roots_of(i) for i in ("xxxxxx", "yyyyyy", "none")]

    # Then the first two are empty and the last is absent
    assert found == [(), (), None]


class _Recording(adapters.LocalFileSystem):
    """A file system that records every write."""

    def __init__(self) -> None:
        """Start with no writes."""
        super().__init__()
        self.writes: list[Path] = []

    @override
    def write_text(self, path: Path, text: str) -> None:
        """Record and make a write.

        Args:
            path: The file.
            text: What to write.
        """
        self.writes.append(path)
        super().write_text(path, text)

    @override
    def append_text(self, path: Path, text: str) -> None:
        """Record and make an append.

        Args:
            path: The file.
            text: What to append.
        """
        self.writes.append(path)
        super().append_text(path, text)


@pytest.mark.slow
def test_asking_for_roots_writes_nothing(
    sandbox: Sandbox, monkeypatch: pytest.MonkeyPatch
) -> None:
    """AC-3: `roots_of` on a recording file system records no write."""
    # Given a repository and a lookup over a file system that records writes
    _project(sandbox, monkeypatch, _TREE)
    files = _Recording()
    environment = ProcessEnvironment()
    repository = adapters.GitRepository(environment)
    settings = ConfigSettings(repository, files)
    catalog = TemplatesCatalog(settings, repository, files)
    lookup = WorkLookup(settings, repository, catalog, files, [files])

    # When the roots of a Work are asked for
    found = lookup.roots_of("pppppp")

    # Then they are found and nothing was written
    assert found == ("api", "e2e", "web")
    assert files.writes == []
