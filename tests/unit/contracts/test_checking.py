# SPDX-License-Identifier: Apache-2.0
"""Tests of the check of the Works."""

from argparse import Namespace
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, cast, override

import pytest

from tests.unit.fakes import ROOT, FakeRepository, FakeStdio, MemoryFileSystem
from wio.contracts import Services
from wio.contracts.checking import check_works, run_check
from wio.contracts.discovery import discover_works, wrong_optional_fields
from wio.formats import read_metadata_block
from wio.models.config import Action, Config, Defaults, Root, Stage, Works
from wio.models.frozen import freeze
from wio.models.template import Template

if TYPE_CHECKING:
    import io
    from collections.abc import Mapping

    from wio.models.config import HierarchyMode

BASE = ".agents/wio/works"


@dataclass
class _Catalog:
    """A catalog of templates, some of which `wio templates check` rejects."""

    names: tuple[str, ...] = ()
    rejected: tuple[str, ...] = ()
    asked: list[str] = field(default_factory=list)

    def find(self, name: str) -> Template | None:
        """Find a template that is not rejected.

        Args:
            name: The template's name.

        Returns:
            The template, or `None` for a name that this catalog does not hold.
        """
        self.asked.append(name)
        if name not in self.names:
            return None
        path = Path(f"templates/{name}.md")
        return Template(name, "feature", None, None, path, entry=False)

    def is_rejected(self, name: str) -> bool:
        """Tell whether the name is one of the rejected ones.

        Args:
            name: The template's name.

        Returns:
            Whether it is rejected.
        """
        return name in self.rejected


class _Disk(MemoryFileSystem):
    """A file system that fails the nth read of some files."""

    def __init__(self, files: dict[Path, str], fail: dict[Path, int]) -> None:
        """Keep the files and the read of each that fails.

        Args:
            files: The files, by path.
            fail: The number of the read, from 1, that fails for a path.
        """
        super().__init__(files)
        self._fail = fail
        self.reads: dict[Path, int] = {}

    @override
    def read_text(self, path: Path) -> str:
        """Read a file, or fail on the read that was asked to fail.

        Args:
            path: The file.

        Returns:
            Its text.

        Raises:
            OSError: This is the read that fails.
        """
        self.reads[path] = self.reads.get(path, 0) + 1
        if self._fail.get(path) == self.reads[path]:
            raise OSError(5, "I/O error")
        return super().read_text(path)


def _marked(work_id: str, extra: str = "") -> str:
    """Write a Work's file.

    Args:
        work_id: The id.
        extra: The lines of the block after the `id`.

    Returns:
        The text of the file.
    """
    return f'<!-- wio\nid = "{work_id}"\n{extra}-->\n\n# Title\n'


def _config(
    mode: HierarchyMode = "flat",
    defaults: Mapping[str, str | tuple[str, ...]] | None = None,
    roots: tuple[str, ...] = (),
) -> Config:
    """Build a config that declares `deliver`, `amend`, `implementation`, `integrate`.

    Args:
        mode: The hierarchy mode.
        defaults: The `[works.defaults.actions]`.
        roots: The names of the declared roots.

    Returns:
        The settings.
    """
    return Config(
        works=Works(hierarchy=mode, defaults=Defaults(actions=freeze(defaults or {}))),
        actions=freeze({"deliver": Action("d"), "amend": Action("a")}),
        stages=freeze({"implementation": Stage(goal="g")}),
        stage_presets=freeze({"integrate": ("implementation",)}),
        roots=freeze({name: Root(paths=(name,)) for name in roots}),
    )


DEFAULTS = {"deliver": ("implementation",)}
REJECTED = (
    "The template `{}` is rejected by `wio templates check`; run it for the findings"
)
TEMPLATE = '<!-- wio\nkind = "feature"\n\n[actions]\n{actions}\n-->\n'


def _check(
    files: Mapping[str, str],
    config: Config | None = None,
    catalog: _Catalog | None = None,
    fail: Mapping[str, int] | None = None,
) -> list[tuple[str, str, str]]:
    """Check Works, and the templates they follow, held in memory.

    Args:
        files: The files by path relative to the repository root, or to the
            Works directory for a path that has no `/` at the start of its
            directory name such as `a/README.md`.
        config: The settings, which declare `deliver`, with the defaults.
        catalog: The catalog, which holds no template by default.
        fail: The number of the read, from 1, that fails for a file.

    Returns:
        The severity, the place and the message of each finding, in order.
    """
    paths = {
        ROOT / (name if name.startswith("templates/") else f"{BASE}/{name}"): text
        for name, text in files.items()
    }
    failing = {
        ROOT / (name if name.startswith("templates/") else f"{BASE}/{name}"): at
        for name, at in (fail or {}).items()
    }
    disk = _Disk(paths, failing)
    chosen = config or _config(defaults=DEFAULTS)
    found = check_works(ROOT, chosen, disk, catalog or _Catalog())
    return [(d.severity, d.where, d.message) for d in found]


def _at(name: str) -> str:
    """Write the place of a Work's file.

    Args:
        name: The file relative to the Works directory.

    Returns:
        The place a diagnostic has.
    """
    return f"{BASE}/{name}"


def test_a_missing_and_a_rejected_template_are_told_apart() -> None:
    """Each is an error that names the template, and the second points to the check."""
    # Given Works that name a missing template, a rejected one, one that is
    # fine, and none
    catalog = _Catalog(names=("good",), rejected=("bad", "unclosed"))
    files = {
        "a/README.md": _marked("a1", 'template = "nosuch"\n'),
        "b/README.md": _marked("b1", 'template = "bad"\n'),
        "c/README.md": _marked("c1", 'template = "unclosed"\n'),
        "d/README.md": _marked("d1", 'template = "good"\n'),
        "e/README.md": _marked("e1"),
        "templates/good.md": TEMPLATE.format(actions='deliver = ["implementation"]'),
    }

    # When the Works are checked
    found = _check(files, catalog=catalog)

    # Then the first is missing, the next two are rejected, and no Work with a
    # template error is also told that it has no action
    assert found == [
        ("error", _at("a/README.md"), "The template `nosuch` does not exist"),
        (
            "error",
            _at("b/README.md"),
            REJECTED.format("bad"),
        ),
        (
            "error",
            _at("c/README.md"),
            REJECTED.format("unclosed"),
        ),
    ]


def test_the_names_of_a_works_own_actions_must_be_declared() -> None:
    """An undeclared action, preset and stage are errors, and a repeat is one."""
    # Given Works that follow a template with `deliver` and `amend`, whose
    # `[actions]` hold the faults of the contract
    catalog = _Catalog(names=("t.leaf",))
    tpl = TEMPLATE.format(
        actions='deliver = ["implementation"]\namend = ["implementation"]'
    )
    faults = {
        "a": 'shipp = ["implementation"]',
        "b": 'deliver = "nosuch"',
        "c": 'deliver = ["implementation", "implementation"]',
        "d": 'deliver = ["gone"]',
        "e": "deliver = []",
    }
    files = {
        f"{d}/README.md": _marked(
            f"w{d}", f'template = "t.leaf"\n\n[actions]\n{line}\n'
        )
        for d, line in faults.items()
    }
    files["templates/t.leaf.md"] = tpl

    # When the Works are checked
    found = _check(files, _config(defaults=DEFAULTS), catalog)

    # Then the first four are errors with the words of the contract, and the
    # empty list is not one, because `amend` remains
    assert found == [
        (
            "error",
            _at("a/README.md"),
            "The action `shipp` is not declared in `[actions]` of the config",
        ),
        (
            "error",
            _at("b/README.md"),
            "The stage preset `nosuch` of action `deliver` is not declared",
        ),
        (
            "error",
            _at("c/README.md"),
            "The stage `implementation` appears twice in action `deliver`",
        ),
        (
            "error",
            _at("d/README.md"),
            "The stage `gone` of action `deliver` is not declared",
        ),
    ]


def test_a_stage_preset_that_is_declared_and_a_repeat_of_an_undeclared_stage() -> None:
    """A declared preset passes, and an undeclared stage that repeats is told twice."""
    # Given a Work with a declared preset, and one whose stage is undeclared and
    # repeated
    files = {
        "a/README.md": _marked("a1", '\n[actions]\ndeliver = "integrate"\n'),
        "b/README.md": _marked("b1", '\n[actions]\ndeliver = ["gone", "gone"]\n'),
    }

    # When the Works are checked
    found = _check(files)

    # Then the first gives nothing, and the second one error for the stage and
    # one for the repeat
    assert found == [
        (
            "error",
            _at("b/README.md"),
            "The stage `gone` appears twice in action `deliver`",
        ),
        (
            "error",
            _at("b/README.md"),
            "The stage `gone` of action `deliver` is not declared",
        ),
    ]


def test_a_repeat_that_a_work_inherits_from_its_template_is_reported_at_the_work() -> (
    None
):
    """No other command judges a pipeline that a template gives."""
    # Given a template whose action repeats a stage, and a Work that follows it
    # with no action of its own
    catalog = _Catalog(names=("t.dup",))
    files = {
        "a/README.md": _marked("a1", 'template = "t.dup"\n'),
        "templates/t.dup.md": TEMPLATE.format(
            actions='deliver = ["implementation", "implementation"]'
        ),
    }

    # When the Work is checked
    found = _check(files, catalog=catalog)

    # Then the repeat is an error at the Work's file
    assert found == [
        (
            "error",
            _at("a/README.md"),
            "The stage `implementation` appears twice in action `deliver`",
        )
    ]


def test_a_repeat_in_a_default_or_a_stage_preset_is_not_judged_here() -> None:
    """`wio config check` judges those."""
    # Given defaults that repeat a stage and a Work that follows none
    config = _config(defaults={"deliver": ("implementation", "implementation")})

    # When the Work is checked
    found = _check({"a/README.md": _marked("a1")}, config)

    # Then nothing is reported
    assert found == []


def test_a_work_that_resolves_to_no_action_is_an_error() -> None:
    """The defaults are not layered under a named template."""
    # Given a project with no defaults, one whose Work removes the only action of
    # its template, and one with defaults
    only = TEMPLATE.format(actions='deliver = ["implementation"]')
    catalog = _Catalog(names=("only",))
    removed = {
        "a/README.md": _marked("a1", 'template = "only"\n\n[actions]\ndeliver = []\n'),
        "templates/only.md": only,
    }

    # When each Work is checked
    none = _check({"a/README.md": _marked("a1")}, _config())
    gone = _check(removed, _config(defaults=DEFAULTS), catalog)
    fine = _check({"a/README.md": _marked("a1")}, _config(defaults=DEFAULTS))

    # Then the first two give `The Work resolves to no action` and the third nothing
    expected = [("error", _at("a/README.md"), "The Work resolves to no action")]
    assert none == expected
    assert gone == expected
    assert fine == []


def test_a_template_with_no_actions_leaves_a_work_with_none() -> None:
    """The defaults do not stand in for a named template that has no action."""
    # Given a template with no `[actions]`, and defaults
    catalog = _Catalog(names=("t",))
    files = {
        "a/README.md": _marked("a1", 'template = "t"\n'),
        "templates/t.md": '<!-- wio\nkind = "feature"\n-->\n',
    }

    # When the Work is checked
    found = _check(files, _config(defaults=DEFAULTS), catalog)

    # Then it resolves to no action
    assert [m for _, _, m in found] == ["The Work resolves to no action"]


def test_a_root_that_the_config_does_not_declare_is_an_error() -> None:
    """The error, the warning and one note for each omitted root."""
    # Given a nesting tree with an undeclared root, a leaf that lists
    # `@descendants`, and a parent that leaves out roots of its children
    files = {
        "a/README.md": _marked("a1", 'roots = ["nosuch"]\n'),
        "b/README.md": _marked("b1", 'roots = ["api", "@descendants"]\n'),
        "c/README.md": _marked("c1", 'roots = ["web"]\n'),
        "c/x/README.md": _marked("c2", 'roots = ["api"]\n'),
        "c/y/README.md": _marked("c3", 'roots = ["db"]\n'),
    }

    # When the Works are checked
    found = _check(files, _config("nesting", DEFAULTS, ("api", "web", "db")))

    # Then the error, the warning and the two notes are reported
    assert found == [
        (
            "error",
            _at("a/README.md"),
            "The root `nosuch` is not declared in `[roots]` of the config",
        ),
        (
            "warning",
            _at("b/README.md"),
            "The Work has no children, so `@descendants` adds no root",
        ),
        (
            "note",
            _at("c/README.md"),
            "Its roots leave out `api`, which a descendant uses",
        ),
        (
            "note",
            _at("c/README.md"),
            "Its roots leave out `db`, which a descendant uses",
        ),
    ]


def test_a_note_for_an_omitted_root_is_given_even_when_it_is_not_declared() -> None:
    """The child gets the error for the root and the parent a note for it."""
    # Given a parent whose child names a root that the config does not declare
    files = {
        "p/README.md": _marked("p1"),
        "p/c/README.md": _marked("c1", 'roots = ["nosuch"]\n'),
    }

    # When the Works are checked
    found = _check(files, _config("nesting", DEFAULTS))

    # Then the child has the error and the parent the note
    assert found == [
        (
            "note",
            _at("p/README.md"),
            "Its roots leave out `nosuch`, which a descendant uses",
        ),
        (
            "error",
            _at("p/c/README.md"),
            "The root `nosuch` is not declared in `[roots]` of the config",
        ),
    ]


def test_under_flat_a_work_that_lists_descendants_is_warned() -> None:
    """Nothing has children under flat, and `@descendants` is no root."""
    # Given `flat` and a Work that lists `@descendants`
    files = {"a/README.md": _marked("a1", 'roots = ["@descendants"]\n')}

    # When the Work is checked
    found = _check(files, _config("flat", DEFAULTS, ("api",)))

    # Then it gets the warning, and no error for an undeclared root
    assert found == [
        (
            "warning",
            _at("a/README.md"),
            "The Work has no children, so `@descendants` adds no root",
        )
    ]


def test_every_concern_is_checked_for_every_work_once() -> None:
    """Each Work gets its findings once, and what depends on one reported is skipped."""
    # Given a Work with an unknown key, an undeclared root and an undeclared
    # action, a parent whose `roots` is a string with a child, and a Work whose
    # template is a number
    files = {
        "a/README.md": _marked(
            "a1",
            "bogus_key = 1\nroots = ['nosuch']\n\n"
            "[actions]\nshipp = ['implementation']\n",
        ),
        "c/README.md": _marked("c1", 'roots = "api"\n'),
        "c/x/README.md": _marked("c2", 'roots = ["api"]\n'),
        "t/README.md": _marked("t1", "template = 1\n"),
    }

    # When the Works are checked
    found = _check(files, _config("nesting", DEFAULTS, ("api",)))

    # Then the first gets a warning and two errors, the parent the error of
    # discovery and no note, and the last the error of discovery only
    assert found == [
        (
            "error",
            _at("a/README.md"),
            "The action `shipp` is not declared in `[actions]` of the config",
        ),
        (
            "error",
            _at("a/README.md"),
            "The root `nosuch` is not declared in `[roots]` of the config",
        ),
        (
            "warning",
            _at("a/README.md"),
            "Unknown key `bogus_key` in the metadata",
        ),
        ("error", _at("c/README.md"), "`roots` must be an array of strings"),
        ("error", _at("t/README.md"), "`template` must be a string"),
    ]


def test_a_work_whose_actions_discovery_reported_is_not_resolved() -> None:
    """The error of discovery is all that a wrong `[actions]` gives."""
    # Given a Work whose `[actions]` is a string
    files = {"a/README.md": _marked("a1", 'actions = "x"\n')}

    # When the Work is checked
    found = _check(files)

    # Then there is the error of discovery and nothing about resolving
    assert [m for _, _, m in found] == [
        "`[actions]` must be a table whose values are a string or an array of strings"
    ]


def test_a_work_with_a_missing_template_still_has_its_own_names_checked() -> None:
    """Only the resolved checks are skipped for a template that is missing."""
    # Given a Work that names a missing template and an undeclared action
    files = {
        "a/README.md": _marked(
            "a1", 'template = "nosuch"\n\n[actions]\nshipp = ["implementation"]\n'
        )
    }

    # When the Work is checked
    found = [m for _, _, m in _check(files)]

    # Then it gets the error for the template and for the action, and none about
    # resolving
    assert found == [
        "The action `shipp` is not declared in `[actions]` of the config",
        "The template `nosuch` does not exist",
    ]


def test_a_file_that_cannot_be_read_again_is_one_error_and_a_template_is_skipped() -> (
    None
):
    """The second read of a Work fails, and a template fails on its `[actions]`."""
    # Given a file system that fails the second read of a Work's file and the
    # first read of a template's file, which the catalog does not make
    catalog = _Catalog(names=("t",))
    files = {
        "a/README.md": _marked("a1"),
        "b/README.md": _marked("b1", 'template = "t"\n'),
        "c/README.md": _marked("c1", 'template = "t"\n'),
        "templates/t.md": TEMPLATE.format(actions='deliver = ["implementation"]'),
    }

    # When the Works are checked
    found = _check(files, catalog=catalog, fail={"a/README.md": 2, "templates/t.md": 1})

    # Then the first Work has one error at its file, and the Works of the template
    # give no diagnostic at all
    assert found == [
        ("error", _at("a/README.md"), "The file cannot be read: I/O error")
    ]


def test_a_file_that_is_not_text_the_second_time_is_one_error() -> None:
    """The wording is that of discovery."""

    # Given a Work whose file turns out not to be UTF-8 on the second read
    class _Binary(_Disk):
        @override
        def read_text(self, path: Path) -> str:
            """Fail with a decoding error on the second read.

            Args:
                path: The file.

            Returns:
                Its text.

            Raises:
                UnicodeDecodeError: On the second read.
            """
            self.reads[path] = self.reads.get(path, 0) + 1
            if self.reads[path] == 2:
                error = UnicodeDecodeError("utf-8", b"\xff", 0, 1, "invalid start byte")
                raise error
            return MemoryFileSystem.read_text(self, path)

    disk = _Binary({ROOT / BASE / "a/README.md": _marked("a1")}, {})

    # When the Work is checked
    found = check_works(ROOT, _config(defaults=DEFAULTS), disk, _Catalog())

    # Then there is one error that says the file is not valid UTF-8
    assert [(d.where, d.message) for d in found] == [
        (_at("a/README.md"), "The file is not valid UTF-8")
    ]


def test_a_template_is_read_once_however_many_works_follow_it() -> None:
    """The template's file is read for its actions the first time only."""
    # Given three Works that follow one template
    catalog = _Catalog(names=("t",))
    files = {f"{d}/README.md": _marked(f"w{d}", 'template = "t"\n') for d in "abc"}
    files["templates/t.md"] = TEMPLATE.format(actions='deliver = ["implementation"]')
    paths = {
        ROOT / (n if n.startswith("templates/") else f"{BASE}/{n}"): t
        for n, t in files.items()
    }
    disk = _Disk(paths, {})

    # When the Works are checked
    check_works(ROOT, _config(defaults=DEFAULTS), disk, catalog)

    # Then the template's file was read once, and each Work's file twice, once by
    # discovery and once by the check
    assert disk.reads[ROOT / "templates/t.md"] == 1
    assert [disk.reads[ROOT / BASE / f"{d}/README.md"] for d in "abc"] == [2, 2, 2]


def test_the_findings_of_discovery_and_the_graph_are_carried_through_once() -> None:
    """A shared id and a cycle are reported as discovery and the graph word them."""
    # Given two Works that share an id and two that wait on each other
    files = {
        "a/README.md": _marked("dup"),
        "b/README.md": _marked("dup"),
        "c/README.md": _marked("c1", 'depends_on = ["c2"]\n'),
        "d/README.md": _marked("c2", 'depends_on = ["c1"]\n'),
    }

    # When the Works are checked
    found = [m for _, _, m in _check(files)]

    # Then each is reported once
    assert len([m for m in found if m.startswith("Works share the id")]) == 1
    assert len([m for m in found if m.startswith("Dependency cycle")]) == 1
    assert len(found) == 2


def test_a_wio_marker_is_not_an_unknown_key() -> None:
    """A comment block and a `+++` block both give no warning for the marker."""
    # Given a Work with each form of block
    front = '+++\nwio = 1\nid = "f1"\n+++\n\n# Title\n'
    files = {"a/README.md": _marked("a1"), "b/README.md": front}

    # When the Works are checked
    found = _check(files)

    # Then neither is told that `wio` is unknown
    assert found == []


def test_discovery_and_the_check_agree_on_which_fields_are_of_a_wrong_type() -> None:
    """The fields of `wrong_optional_fields` are those that discovery reports."""
    # Given a Work with every optional key of a wrong type
    text = _marked("a1", 'template = 1\nroots = "a"\ndepends_on = [1]\nactions = 3\n')
    disk = MemoryFileSystem({ROOT / BASE / "a/README.md": text})
    block = read_metadata_block(text)
    assert block is not None

    # When discovery reads it and the fields are type-tested
    found = discover_works(ROOT, Works(), disk)
    wrong = wrong_optional_fields(block.data)

    # Then there is one error of discovery for each field named
    assert wrong == {"template", "roots", "depends_on", "actions"}
    assert len(found.diagnostics) == len(wrong)
    keys = {
        key
        for key in wrong
        if any(
            f"`{key}`" in d.message or f"`[{key}]`" in d.message
            for d in found.diagnostics
        )
    }
    assert keys == wrong


@pytest.mark.parametrize(
    ("extra", "severity", "code"),
    [("depend_on = []\n", "warning", 0), ('id2 = "x"\n', "warning", 0)],
)
def test_the_command_exits_0_for_a_warning(
    extra: str, severity: str, code: int
) -> None:
    """A warning is printed and does not fail the command."""
    # Given a Work with an unknown key
    disk = MemoryFileSystem({ROOT / BASE / "a/README.md": _marked("a1", extra)})
    services = Services(_Settings(), FakeRepository(), disk, _Catalog())
    stdio = FakeStdio()

    # When the command runs
    status = run_check(services, Namespace(json=False), stdio)

    # Then the warning is written and the exit code is 0
    assert cast("io.StringIO", stdio.stdout).getvalue().startswith(f"{severity}: ")
    assert status == code


class _Settings:
    """A `Settings` that gives the config that declares `deliver`."""

    def load(self) -> Config:
        """Give the config.

        Returns:
            The settings.
        """
        return _config(defaults=DEFAULTS)


def test_the_command_exits_1_for_an_error_and_says_when_the_contracts_pass() -> None:
    """An error fails the command, and nothing found is a sentence or `[]`."""
    # Given a Work with an id that is refused, and a Work with no problem
    bad = MemoryFileSystem({ROOT / BASE / "a/README.md": _marked("a b")})
    good = MemoryFileSystem({ROOT / BASE / "a/README.md": _marked("a1")})
    streams = [FakeStdio() for _ in range(3)]

    # When the command runs on each, and on the good one with `--json`
    failed = run_check(
        Services(_Settings(), FakeRepository(), bad, _Catalog()),
        Namespace(json=False),
        streams[0],
    )
    passed = run_check(
        Services(_Settings(), FakeRepository(), good, _Catalog()),
        Namespace(json=False),
        streams[1],
    )
    as_json = run_check(
        Services(_Settings(), FakeRepository(), good, _Catalog()),
        Namespace(json=True),
        streams[2],
    )

    # Then the first exits 1 with the error, and the others exit 0 with the
    # sentence and `[]`
    texts = [cast("io.StringIO", s.stdout).getvalue() for s in streams]
    assert failed == 1
    assert texts[0].startswith("error: ")
    assert (passed, as_json) == (0, 0)
    assert texts[1:] == ["The contracts pass.\n", "[]\n"]


def test_an_undeclared_root_that_is_listed_twice_is_one_error() -> None:
    """The error is for the name, not for each time it is written."""
    # Given a Work that lists an undeclared root twice
    files = {"a/README.md": _marked("a1", 'roots = ["nosuch", "nosuch"]\n')}

    # When the Work is checked
    found = _check(files, _config("flat", DEFAULTS, ("api",)))

    # Then there is one error
    assert [m for _, _, m in found] == [
        "The root `nosuch` is not declared in `[roots]` of the config"
    ]


def test_a_parent_that_lists_descendants_is_not_warned() -> None:
    """The warning is for a Work with no children."""
    # Given a parent that lists `@descendants`, and a child with a root
    files = {
        "p/README.md": _marked("p1", 'roots = ["@descendants"]\n'),
        "p/c/README.md": _marked("c1", 'roots = ["api"]\n'),
    }

    # When the Works are checked
    found = _check(files, _config("nesting", DEFAULTS, ("api",)))

    # Then nothing is reported, because the parent passes the root up
    assert found == []
