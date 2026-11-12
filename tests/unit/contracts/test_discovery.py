# SPDX-License-Identifier: Apache-2.0
"""Tests of the discovery of Works in `wio.contracts`."""

from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from tests.unit.contracts.helpers import paths, where
from tests.unit.fakes import ROOT, MemoryFileSystem
from wio.contracts.discovery import (
    WorkDiscovery,
    discover_works,
    explain_not_a_work,
    find_work,
)
from wio.models.config import Works
from wio.models.works import Work

if TYPE_CHECKING:
    from collections.abc import Iterable, Mapping

    from wio.models.config import HierarchyMode


WORKS = ROOT / "works"
BOM = chr(0xFEFF)
NOT_UTF8 = UnicodeDecodeError("utf-8", b"\xff", 0, 1, "invalid start byte")


def _block(*lines: str, body: str = "# Title\n") -> str:
    """Write a file that opens with a comment block holding the given lines.

    Args:
        *lines: The lines of TOML, one per argument.
        body: The text after the block.

    Returns:
        The text of the file.
    """
    return "\n".join(["<!-- wio", *lines, "-->", "", body])


def _marked(work_id: str, body: str = "# Title\n") -> str:
    """Write a file with a block that holds only an id.

    Args:
        work_id: The id.
        body: The text after the block.

    Returns:
        The text of the file.
    """
    return _block(f'id = "{work_id}"', body=body)


def _disk(
    files: Mapping[str, str],
    links: Iterable[str] = (),
    broken: Mapping[str, Exception] | None = None,
) -> MemoryFileSystem:
    """Build a disk whose files are below the Works directory `works`.

    Args:
        files: The text of each file, by its path below the Works directory.
        links: The paths below the Works directory that are symbolic links.
        broken: The error that reading each path raises, by its path below the
            Works directory.

    Returns:
        The disk.
    """
    return MemoryFileSystem(
        {WORKS / name: text for name, text in files.items()},
        links={WORKS / name for name in links},
        broken={WORKS / name: error for name, error in (broken or {}).items()},
    )


def _find(
    disk: MemoryFileSystem, hierarchy: HierarchyMode = "nesting"
) -> WorkDiscovery:
    """Discover the Works of the disk under the Works directory `works`.

    Args:
        disk: The files.
        hierarchy: `flat` or `nesting`.

    Returns:
        What the walk found.
    """
    return discover_works(ROOT, Works(dir="works", hierarchy=hierarchy), disk)


def _by_path(found: WorkDiscovery) -> dict[str, Work]:
    """Index the Works found by their paths below the Works directory.

    Args:
        found: What the walk found.

    Returns:
        The Works, in the order they were found.
    """
    return {w.path.relative_to("works").as_posix(): w for w in found.works}


def test_marked_files_become_works_with_their_fields_in_the_order_of_their_paths() -> (
    None
):
    """AC-1: a comment block and `+++` front matter are read into a `Work`."""
    # Given a nesting tree with a Work that sets every key, a Work of front
    # matter with a body of `##` only, a Work with no heading, a file with no
    # block, a file whose block is on its second line, a hidden directory with a
    # marked file and a symbolic link to a marked file
    full = _block(
        'id = "k3m9xq"',
        'template = "feature.leaf"',
        'roots = ["wio"]',
        'depends_on = ["a7b2c4"]',
        "[actions]",
        'define = "define-feature"',
        'deliver = ["implementation"]',
        body="# First\n",
    )
    disk = _disk(
        {
            "a/README.md": full,
            "b/spec.md": '+++\nwio = 1\nid = "a7b2c4"\n+++\n\n## Only\n',
            "d/README.md": _marked("p5n2hv", body="Text only.\n"),
            "a/notes.md": "# Notes\n",
            "c/x.md": "\n" + _marked("zzzzzz"),
            ".git/m.md": _marked("hidden"),
            "e/link.md": _marked("linked"),
        },
        links=["e/link.md"],
    )

    # When the Works are discovered
    found = _find(disk)

    # Then there are three Works in the order of their paths with those ids and
    # the titles `First`, `Only` and none, the first with its template, roots,
    # dependencies and both overrides and the others with none, and there is no
    # diagnostic
    works = _by_path(found)
    assert list(works) == ["a/README.md", "b/spec.md", "d/README.md"]
    assert [w.id for w in works.values()] == ["k3m9xq", "a7b2c4", "p5n2hv"]
    assert [w.title for w in works.values()] == ["First", "Only", None]
    first, second, third = works.values()
    assert (first.template, first.roots, first.depends_on) == (
        "feature.leaf",
        ("wio",),
        ("a7b2c4",),
    )
    assert dict(first.actions) == {
        "define": "define-feature",
        "deliver": ("implementation",),
    }
    assert (second.template, second.roots, second.depends_on) == (None, (), ())
    assert (third.template, third.roots, third.depends_on) == (None, (), ())
    assert not second.actions
    assert not third.actions
    assert found.diagnostics == ()
    assert found.left_out == ()


def test_the_title_is_the_first_real_heading_at_any_level() -> None:
    """AC-1: a heading in a comment or a code block is not a title."""
    # Given a Work whose body opens with a comment holding `# Hidden`, a fenced
    # block holding `# Code`, and then `## Real`
    body = "<!--\n# Hidden\n-->\n\n```\n# Code\n```\n\n## Real\n"
    disk = _disk({"a/README.md": _marked("k3m9xq", body)})

    # When the Works are discovered
    found = _find(disk)

    # Then its title is `Real`
    assert [w.title for w in found.works] == ["Real"]


def test_discovery_writes_no_file() -> None:
    """AC-1: every file is read through the port and none is written."""
    # Given a tree of Works, one with an error, on a fake file system
    disk = _disk({"a/README.md": _marked("k3m9xq"), "b/README.md": _block("title = 1")})
    before = dict(disk.files)

    # When the Works are discovered
    _find(disk)

    # Then the files are as they were
    assert disk.files == before


def test_a_file_that_cannot_be_identified_is_left_out_with_one_error() -> None:
    """AC-2: seven broken files give seven errors at their places, and no more."""
    # Given a flat tree with a file that is not UTF-8, a block that does not
    # close, invalid TOML on line 3, `wio = 2` on line 2, no `id`, `id = ""`,
    # `id = 12`, and a good Work
    names = ("utf", "open", "toml", "marker", "noid", "empty", "number")
    disk = _disk(
        {
            "bad/utf.md": "",
            "bad/open.md": '<!-- wio\nid = "x"\n',
            "bad/toml.md": '<!-- wio\nid = "x"\nbad =\n-->\n',
            "bad/marker.md": '+++\nwio = 2\nid = "x"\n+++\n',
            "bad/noid.md": _block('title = "t"'),
            "bad/empty.md": _block('id = ""'),
            "bad/number.md": _block("id = 12"),
            "good/README.md": _marked("k3m9xq"),
        },
        broken={"bad/utf.md": NOT_UTF8},
    )

    # When the Works are discovered
    found = _find(disk, "flat")

    # Then the good Work is found and there is one error for each of the seven
    # at their places, and the seven files are in `left_out` and in no other list
    assert list(_by_path(found)) == ["good/README.md"]
    assert sorted(where(found.diagnostics)) == sorted(
        [
            "works/bad/utf.md",
            "works/bad/open.md:1",
            "works/bad/toml.md:3",
            "works/bad/marker.md:2",
            "works/bad/noid.md",
            "works/bad/empty.md",
            "works/bad/number.md",
        ]
    )
    assert sorted(paths(found.left_out)) == sorted(f"works/bad/{n}.md" for n in names)
    assert found.excluded == ()


def test_a_file_that_cannot_be_read_is_left_out_with_the_reason() -> None:
    """AC-2: an `OSError` of the port is one error that gives its reason."""
    # Given a marked file that the file system fails to read with a permission
    # error, beside a good Work
    disk = _disk(
        {"a/README.md": _marked("k3m9xq"), "b/README.md": ""},
        broken={"b/README.md": PermissionError(13, "Permission denied")},
    )

    # When the Works are discovered
    found = _find(disk)

    # Then the good Work is found and one error is at the file's path and says
    # that it cannot be read
    assert list(_by_path(found)) == ["a/README.md"]
    assert [(d.where, d.message) for d in found.diagnostics] == [
        ("works/b/README.md", "The file cannot be read: Permission denied")
    ]


def test_a_wrong_optional_field_is_empty_and_reported_and_the_work_stays() -> None:
    """AC-3: six wrong fields give six errors and five Works."""
    # Given a nesting tree with `roots = "api"` on a parent whose child has
    # `depends_on = [1]`, an `[actions]` string and a numeric `template`,
    # `roots = ["a", 1]`, and `[actions]` with `define = 5`
    disk = _disk(
        {
            "p/README.md": _block('id = "p1"', 'roots = "api"'),
            "p/c/README.md": _block('id = "c1"', "depends_on = [1]"),
            "q/README.md": _block('id = "q1"', 'actions = "x"', "template = 2"),
            "r/README.md": _block('id = "r1"', 'roots = ["a", 1]'),
            "s/README.md": _block('id = "s1"', "[actions]", "define = 5"),
        }
    )

    # When the Works are discovered
    found = _find(disk)

    # Then all five Works are found with the wrong fields empty, and there is
    # one error for each of the six fields at its file
    works = _by_path(found)
    assert sorted(w.id for w in works.values()) == ["c1", "p1", "q1", "r1", "s1"]
    assert works["p/README.md"].roots == ()
    assert works["p/c/README.md"].depends_on == ()
    assert not works["q/README.md"].actions
    assert works["q/README.md"].template is None
    assert works["r/README.md"].roots == ()
    assert not works["s/README.md"].actions
    assert sorted(where(found.diagnostics)) == [
        "works/p/README.md",
        "works/p/c/README.md",
        "works/q/README.md",
        "works/q/README.md",
        "works/r/README.md",
        "works/s/README.md",
    ]
    assert found.incomplete == ()


def test_a_shared_id_keeps_both_works_and_refuses_its_lookup() -> None:
    """AC-4: one error names both paths, and the lookup yields it and no Work."""
    # Given a flat tree where two Works share `k3m9xq` and a third has `p5n2hv`
    disk = _disk(
        {
            "a/README.md": _marked("k3m9xq"),
            "b/README.md": _marked("k3m9xq"),
            "c/README.md": _marked("p5n2hv"),
        }
    )

    # When the Works are discovered and `k3m9xq`, `p5n2hv` and `zzzzzz` are
    # looked up
    found = _find(disk, "flat")
    shared = find_work(found, "k3m9xq")
    other = find_work(found, "p5n2hv")
    missing = find_work(found, "zzzzzz")

    # Then all three Works are found, one error is at the two paths joined by a
    # comma and a space and names the id, the first lookup yields that
    # diagnostic, the second the Work and the third none
    assert len(found.works) == 3
    assert where(found.diagnostics) == ["works/a/README.md, works/b/README.md"]
    assert "k3m9xq" in found.diagnostics[0].message
    assert shared == found.diagnostics[0]
    assert isinstance(other, Work)
    assert other.path == Path("works/c/README.md")
    assert missing is None
    assert found.ambiguous == found.diagnostics
    assert found.incomplete == ()


def _collision_tree() -> MemoryFileSystem:
    """Build the files of the first scenario of AC-5.

    Returns:
        A disk with `a/one.md` and `a/two.md`, `top.md` directly in the Works
        directory and `b/README.md`.
    """
    return _disk(
        {
            "a/one.md": _marked("k3m9xq"),
            "a/two.md": _marked("a7b2c4"),
            "top.md": _marked("p5n2hv"),
            "b/README.md": _marked("s5t3wx"),
        }
    )


def test_a_directory_with_two_marked_files_holds_no_work_under_nesting() -> None:
    """AC-5: one error names both files, and a top-level file is not a Work."""
    # Given a nesting tree with `a/one.md` and `a/two.md`, `top.md` directly in
    # the Works directory, and `b/README.md`
    disk = _collision_tree()

    # When the Works are discovered
    found = _find(disk)

    # Then only `b/README.md` is a Work, one error is at the two files of `a`
    # and names the directory, and one error is at `works/top.md` and says that
    # a Work cannot sit directly in the Works directory
    assert list(_by_path(found)) == ["b/README.md"]
    assert sorted(where(found.diagnostics)) == [
        "works/a/one.md, works/a/two.md",
        "works/top.md",
    ]
    by_place = {d.where: d.message for d in found.diagnostics}
    assert "`works/a`" in by_place["works/a/one.md, works/a/two.md"]
    assert "cannot sit directly in the Works directory" in by_place["works/top.md"]


def test_a_marked_file_that_is_left_out_still_counts_in_its_directory() -> None:
    """AC-5: a missing `id` gives two errors, and a file that is not UTF-8 one."""
    # Given a nesting tree with `a/one.md` and `a/two.md` whose block has no
    # `id`, and a directory with a marked file and a file that is not UTF-8
    disk = _disk(
        {
            "a/one.md": _marked("k3m9xq"),
            "a/two.md": _block('title = "t"'),
            "b/one.md": _marked("a7b2c4"),
            "b/bin.md": "",
        },
        broken={"b/bin.md": NOT_UTF8},
    )

    # When the Works are discovered
    found = _find(disk)

    # Then there is no Work in `a`, one error for the collision and one for the
    # missing id, and the other directory holds its Work and the one error of
    # the file that cannot be decoded
    assert list(_by_path(found)) == ["b/one.md"]
    assert sorted(where(found.diagnostics)) == sorted(
        ["works/a/one.md, works/a/two.md", "works/a/two.md", "works/b/bin.md"]
    )


def test_under_flat_a_directory_may_hold_any_number_of_works() -> None:
    """AC-6: the files of the nesting collision are all Works."""
    # Given a flat tree with the files of the first collision scenario
    disk = _collision_tree()

    # When the Works are discovered
    found = _find(disk, "flat")

    # Then `a/one.md`, `a/two.md`, `top.md` and `b/README.md` are Works and
    # there is no diagnostic
    assert list(_by_path(found)) == ["a/one.md", "a/two.md", "b/README.md", "top.md"]
    assert found.diagnostics == ()


def test_a_missing_default_directory_holds_no_works() -> None:
    """AC-7: the default Works directory may be missing without a diagnostic."""
    # Given the default Works directory missing
    disk = MemoryFileSystem({ROOT / "other.md": ""})

    # When the Works are discovered
    found = discover_works(ROOT, Works(), disk)

    # Then there is no Work and no diagnostic
    assert found == WorkDiscovery((), (), (), (), (), ())


@pytest.mark.parametrize(
    ("disk", "message"),
    [
        (MemoryFileSystem({ROOT / "x": ""}), "does not exist"),
        (MemoryFileSystem({ROOT / "elsewhere": ""}), "is not a directory"),
        (
            MemoryFileSystem(
                {ROOT / "elsewhere" / "a.md": _marked("k3m9xq")},
                links={ROOT / "elsewhere"},
            ),
            "must not be a symbolic link",
        ),
    ],
    ids=["missing", "a file", "a symbolic link"],
)
def test_a_works_directory_that_cannot_be_walked_is_one_error(
    disk: MemoryFileSystem, message: str
) -> None:
    """AC-7: missing, a file and a symbolic link each give one error."""
    # Given a configured Works directory that is missing, one that is a file and
    # one that is a symbolic link to a directory
    settings = Works(dir="elsewhere")

    # When the Works are discovered for each
    found = discover_works(ROOT, settings, disk)

    # Then each gives no Work and one error whose message begins `The Works
    # directory` and whose place is the directory as written
    assert found.works == ()
    assert where(found.diagnostics) == ["elsewhere"]
    assert found.diagnostics[0].message.startswith("The Works directory")
    assert found.diagnostics[0].message.endswith(message)


def test_the_works_and_the_diagnostics_are_in_a_fixed_order() -> None:
    """AC-1: the Works by their paths and the diagnostics as `order_diagnostics`."""
    # Given a tree written in the reverse of its order, with an error in a later
    # file at line 2, one in an earlier file, and a shared id
    disk = _disk(
        {
            "z/README.md": _marked("dup"),
            "y/README.md": _marked("dup"),
            "m/b.md": "+++\nwio = 2\n+++\n",
            "m/a.md": _block('title = "t"'),
            "a/README.md": _marked("first"),
        }
    )

    # When the Works are discovered twice
    first = _find(disk, "flat")
    second = _find(disk, "flat")

    # Then both results are equal, the Works are sorted by the string of their
    # paths, and the errors of a file come before the error of two files
    assert first == second
    assert list(_by_path(first)) == ["a/README.md", "y/README.md", "z/README.md"]
    assert where(first.diagnostics) == [
        "works/m/a.md",
        "works/m/b.md:2",
        "works/y/README.md, works/z/README.md",
    ]


def test_the_works_directory_itself_may_start_with_a_dot() -> None:
    """AC-1: only a directory below the Works directory is hidden by its name."""
    # Given the Works directory `.works` with a Work, and a hidden directory
    # below it with another
    disk = MemoryFileSystem(
        {
            ROOT / ".works" / "w" / "README.md": _marked("k3m9xq"),
            ROOT / ".works" / ".h" / "README.md": _marked("a7b2c4"),
        }
    )

    # When the Works are discovered
    found = discover_works(ROOT, Works(dir=".works", hierarchy="nesting"), disk)

    # Then the first Work is found and the second is not
    assert [w.id for w in found.works] == ["k3m9xq"]


def _error_trees() -> dict[str, WorkDiscovery]:
    """Discover six trees, each with one kind of problem.

    Returns:
        What each walk found, by the problem it has.
    """
    shut = discover_works(ROOT, Works(dir="x"), MemoryFileSystem({ROOT / "y": ""}))
    return {
        "left out": _find(_disk({"a/README.md": _block('title = "t"')})),
        "collision": _find(
            _disk({"a/one.md": _marked("a1"), "a/two.md": _marked("a2")})
        ),
        "top": _find(_disk({"top.md": _marked("a1")})),
        "directory": shut,
        "shared": _find(
            _disk({"a/README.md": _marked("a1"), "b/README.md": _marked("a1")})
        ),
        "field": _find(_disk({"a/README.md": _block('id = "a1"', "roots = 1")})),
    }


@pytest.mark.parametrize("name", ["left out", "collision", "top", "directory"])
def test_an_error_that_leaves_the_tree_incomplete_is_marked_so(name: str) -> None:
    """AC-2, AC-5, AC-7: a Work left out, a collision, a top-level file, a directory."""
    # Given a tree with that problem
    # When the Works are discovered
    found = _error_trees()[name]

    # Then its error is in `incomplete` and not in `ambiguous`
    assert found.diagnostics != ()
    assert found.incomplete == found.diagnostics
    assert found.ambiguous == ()


def test_a_shared_id_is_ambiguous_and_a_wrong_field_is_neither() -> None:
    """AC-3, AC-4: a shared id is not incomplete, and a wrong field is neither."""
    # Given a tree with a shared id and a tree with only a wrong optional field
    # When the Works are discovered for each
    found = _error_trees()

    # Then the shared id has its error in `ambiguous` and not in `incomplete`,
    # and the other has neither, though its error is in `diagnostics`
    assert found["shared"].ambiguous == found["shared"].diagnostics != ()
    assert found["shared"].incomplete == ()
    assert found["field"].diagnostics != ()
    assert (found["field"].incomplete, found["field"].ambiguous) == ((), ())


def test_the_marked_files_of_a_collision_are_excluded_and_not_left_out() -> None:
    """AC-5: the files of a collided directory and a top-level file are `excluded`."""
    # Given the nesting tree of the first collision scenario and one with a file
    # that is left out
    plain = _find(_collision_tree())
    mixed = _find(
        _disk({"a/one.md": _marked("k3m9xq"), "a/two.md": _block('title = "t"')})
    )

    # When the Works are discovered (above)

    # Then `a/one.md`, `a/two.md` and `top.md` are in `excluded` and not in
    # `left_out`, and in the second scenario `a/two.md`, which has no `id`, is in
    # `left_out` and not in `excluded`, so the two lists are disjoint
    assert paths(plain.excluded) == [
        "works/a/one.md",
        "works/a/two.md",
        "works/top.md",
    ]
    assert plain.left_out == ()
    assert paths(mixed.left_out) == ["works/a/two.md"]
    assert paths(mixed.excluded) == ["works/a/one.md"]


def _reasons_disk() -> MemoryFileSystem:
    """Build a nesting tree with a file for each reason of AC-8.

    Returns:
        The disk.
    """
    disk = _disk(
        {
            "good/README.md": _marked("good"),
            "x.txt": "text",
            "link.md": _marked("linked"),
            "lnk/inner.md": _marked("inner"),
            ".h/m.md": _marked("hidden"),
            ".h/plain.md": "# Plain\n",
            "plain/README.md": "# Plain\n",
            "late/README.md": "\n" + _marked("late"),
            "fm/README.md": '+++\nid = "fm"\n+++\n',
            "two/one.md": _marked("one"),
            "two/other.md": _marked("other"),
            "top.md": _marked("top"),
            "open/README.md": '<!-- wio\nid = "open"\n',
        },
        links=["link.md", "lnk"],
    )
    disk.files[ROOT / "docs" / "o.md"] = _marked("outside")
    return disk


REASONS = {
    "gone.md": ["works/gone.md", "does not exist or is not a file"],
    "good": ["works/good", "does not exist or is not a file"],
    "x.txt": ["works/x.txt", "Markdown"],
    "link.md": ["works/link.md", "symbolic link"],
    "lnk/inner.md": ["works/lnk", "symbolic link"],
    "../docs/o.md": ["docs/o.md", "outside the Works directory"],
    ".h/m.md": ["works/.h/m.md", "`.h`", "hidden"],
    ".h/plain.md": ["works/.h/plain.md", "`.h`", "hidden"],
    "plain/README.md": ["works/plain/README.md", "no metadata block"],
    "late/README.md": ["works/late/README.md", "no metadata block"],
    "fm/README.md": ["works/fm/README.md", "`+++` front matter", "`wio` key"],
    "two/one.md": ["works/two/one.md", "works/two/other.md", "other marked files"],
    "top.md": ["works/top.md", "directly in the Works directory", "`works`"],
    "open/README.md": ["works/open/README.md", "left out", "does not close"],
}


@pytest.mark.parametrize("name", list(REASONS))
def test_each_file_that_is_not_a_work_has_the_first_reason_that_applies(
    name: str,
) -> None:
    """AC-8: each path of the list names its subject."""
    # Given a nesting tree with a file for each reason, and one path of them
    disk = _reasons_disk()
    settings = Works(dir="works", hierarchy="nesting")

    # When the reason it is not a Work is asked for
    reason = explain_not_a_work(ROOT, Path("works") / name, settings, disk)

    # Then the reason names the path, the other files, the Works directory or the
    # error of discovery as its subject
    assert reason is not None
    assert all(subject in reason for subject in REASONS[name])


def test_a_work_has_no_reason_and_the_path_may_be_absolute_or_relative() -> None:
    """AC-8: a Work has none, and the two ways of writing a path agree."""
    # Given a nesting tree with a Work and a file that is not one
    disk = _reasons_disk()
    settings = Works(dir="works", hierarchy="nesting")

    # When the reason is asked for the Work, and for the other file written
    # relative to the root and absolute
    work = explain_not_a_work(ROOT, Path("works/good/README.md"), settings, disk)
    relative = explain_not_a_work(ROOT, Path("works/x.txt"), settings, disk)
    absolute = explain_not_a_work(ROOT, ROOT / "works" / "x.txt", settings, disk)

    # Then the Work has none and the other two reasons are equal
    assert work is None
    assert relative is not None
    assert relative == absolute


def test_under_flat_a_shared_directory_is_no_reason() -> None:
    """AC-8: the two collision reasons apply to nesting alone."""
    # Given a flat tree with two marked files in a directory and one directly in
    # the Works directory
    disk = _collision_tree()
    settings = Works(dir="works", hierarchy="flat")

    # When the reason each is not a Work is asked for
    reasons = [
        explain_not_a_work(ROOT, Path("works") / name, settings, disk)
        for name in ("a/one.md", "a/two.md", "top.md")
    ]

    # Then none has a reason
    assert reasons == [None, None, None]


def test_the_title_is_the_first_of_several_headings() -> None:
    """AC-1: the first heading is the title, whatever comes after it."""
    # Given a Work whose body has `# A` and then `## B`
    disk = _disk({"a/README.md": _marked("k3m9xq", "# A\n\n## B\n")})

    # When the Works are discovered
    found = _find(disk)

    # Then its title is `A`
    assert [w.title for w in found.works] == ["A"]


def test_a_block_that_cannot_be_read_counts_in_its_directory() -> None:
    """AC-5: an unclosed block is marked, so it collides, and is also reported."""
    # Given a nesting tree with a good `a/one.md` and an `a/two.md` whose block
    # does not close
    disk = _disk({"a/one.md": _marked("k3m9xq"), "a/two.md": '<!-- wio\nid = "x"\n'})

    # When the Works are discovered
    found = _find(disk)

    # Then there is no Work, one error is at both files and one is at the block
    # of the second, which is left out, and the first is excluded
    assert found.works == ()
    assert sorted(where(found.diagnostics)) == [
        "works/a/one.md, works/a/two.md",
        "works/a/two.md:1",
    ]
    assert paths(found.left_out) == ["works/a/two.md"]
    assert paths(found.excluded) == ["works/a/one.md"]


def test_a_file_that_cannot_be_read_does_not_count_in_its_directory() -> None:
    """AC-5: a file that fails to read is not known to be marked."""
    # Given a nesting tree with a good `a/one.md` and an `a/two.md` that the file
    # system fails to read
    disk = _disk(
        {"a/one.md": _marked("k3m9xq"), "a/two.md": ""},
        broken={"a/two.md": PermissionError(13, "Permission denied")},
    )

    # When the Works are discovered
    found = _find(disk)

    # Then `a/one.md` is a Work and the only error is that of the other file
    assert list(_by_path(found)) == ["a/one.md"]
    assert where(found.diagnostics) == ["works/a/two.md"]


def test_a_file_left_out_directly_in_the_works_directory_is_explained_as_left_out() -> (
    None
):
    """AC-8: a file that cannot be decoded is not marked, so not the direct reason."""
    # Given a nesting tree with a file that is not UTF-8 directly in the Works
    # directory, and a marked file with no `id` beside it
    disk = _disk(
        {"gone.md": "", "noid.md": _block('title = "t"')}, broken={"gone.md": NOT_UTF8}
    )
    settings = Works(dir="works", hierarchy="nesting")

    # When the reason each is not a Work is asked for
    gone = explain_not_a_work(ROOT, Path("works/gone.md"), settings, disk)
    noid = explain_not_a_work(ROOT, Path("works/noid.md"), settings, disk)

    # Then the first is left out for its own error and the second is directly in
    # the Works directory
    assert gone is not None
    assert "left out" in gone
    assert "UTF-8" in gone
    assert noid is not None
    assert "directly in the Works directory" in noid


def test_a_symbolic_link_outside_the_works_directory_is_a_link_first() -> None:
    """AC-8: the symbolic link comes before the Works directory in the list."""
    # Given a symbolic link to a marked file outside the Works directory
    disk = _disk({"good/README.md": _marked("good")})
    disk.files[ROOT / "docs" / "l.md"] = _marked("linked")
    disk.links.add(ROOT / "docs" / "l.md")

    # When the reason it is not a Work is asked for
    reason = explain_not_a_work(ROOT, Path("docs/l.md"), Works(dir="works"), disk)

    # Then it is a symbolic link and not a file outside the Works directory
    assert reason is not None
    assert "symbolic link" in reason


def test_a_hidden_file_is_a_work_and_a_link_above_the_root_is_no_reason() -> None:
    """AC-1, AC-8: only a directory is hidden by its name, and the root's own path."""
    # Given a tree with a Work in `.h.md` and the repository under a link
    disk = _disk({".h.md": _marked("hidden"), "a/README.md": _marked("k3m9xq")})
    disk.links.add(ROOT)
    settings = Works(dir="works", hierarchy="flat")

    # When the Works are discovered and the reasons are asked for
    found = discover_works(ROOT, settings, disk)
    hidden = explain_not_a_work(ROOT, Path("works/.h.md"), settings, disk)
    other = explain_not_a_work(ROOT, Path("works/a/README.md"), settings, disk)

    # Then `.h.md` is a Work like the other, and neither has a reason
    assert [w.id for w in found.works] == ["hidden", "k3m9xq"]
    assert (hidden, other) == (None, None)


@pytest.mark.parametrize(
    "text",
    ['+++\nid = "x"\n+++\n', BOM + '+++\r\nid = "x"\r\n+++\r\n'],
    ids=["lf", "bom crlf"],
)
def test_front_matter_with_no_wio_key_is_a_reason_in_any_line_ending(text: str) -> None:
    """AC-8: a BOM and CRLF do not hide the `+++` line."""
    # Given a file with `+++` front matter and no `wio` key
    disk = _disk({"a/README.md": text})

    # When the reason it is not a Work is asked for
    reason = explain_not_a_work(
        ROOT, Path("works/a/README.md"), Works(dir="works"), disk
    )

    # Then it names the front matter
    assert reason is not None
    assert "front matter" in reason


def test_a_name_that_ends_in_an_upper_case_md_is_not_markdown() -> None:
    """AC-8: the suffix is `.md` with that case, and the reason names the path."""
    # Given a file `R.MD`
    disk = _disk({"R.MD": _marked("upper")})

    # When the reason it is not a Work is asked for
    reason = explain_not_a_work(ROOT, Path("works/R.MD"), Works(dir="works"), disk)

    # Then it is not a Markdown file, and the path is written relative to the root
    assert reason == "`works/R.MD` is not a Markdown file: its name must end in `.md`"


def test_a_file_name_with_a_colon_or_a_comma_has_its_reason() -> None:
    """AC-8: the reasons come from what was read, not from the text of an error."""
    # Given a nesting tree with `a/x:y.md` that has no `id`, and `b/p, q.md` and
    # `b/r.md`, both marked
    disk = _disk(
        {
            "a/x:y.md": _block('title = "t"'),
            "b/p, q.md": _marked("pq"),
            "b/r.md": _marked("r"),
        }
    )
    settings = Works(dir="works", hierarchy="nesting")

    # When the reason each is not a Work is asked for
    colon = explain_not_a_work(ROOT, Path("works/a/x:y.md"), settings, disk)
    comma = explain_not_a_work(ROOT, Path("works/b/p, q.md"), settings, disk)
    other = explain_not_a_work(ROOT, Path("works/b/r.md"), settings, disk)

    # Then the first is left out for the missing id, and the other two name each
    # other
    assert colon is not None
    assert "left out" in colon
    assert "`id`" in colon
    assert comma == (
        "`works/b/p, q.md` is in a directory with other marked files: works/b/r.md"
    )
    assert other == (
        "`works/b/r.md` is in a directory with other marked files: works/b/p, q.md"
    )


@pytest.mark.parametrize(
    ("lines", "token"),
    [
        ('title = "t"', "`id`"),
        ("id = 12", "`id`"),
        ('id = ""', "`id`"),
        ('id = "a"\ntemplate = 1', "`template`"),
        ('id = "a"\nroots = 1', "`roots`"),
        ('id = "a"\ndepends_on = 1', "`depends_on`"),
        ('id = "a"\nactions = 1', "`[actions]`"),
    ],
)
def test_each_error_names_the_key_it_is_about(lines: str, token: str) -> None:
    """AC-2, AC-3: the message says which key is wrong."""
    # Given a Work with one wrong key
    disk = _disk({"a/README.md": _block(lines)})

    # When the Works are discovered
    found = _find(disk)

    # Then its one error names the key
    assert [token in d.message for d in found.diagnostics] == [True]


def test_three_works_that_share_an_id_are_one_error_at_all_three_paths() -> None:
    """AC-4: the place lists every path and the message does not count them."""
    # Given three Works with one id
    disk = _disk({f"{n}/README.md": _marked("k3m9xq") for n in "abc"})

    # When the Works are discovered
    found = _find(disk, "flat")

    # Then one error is at the three paths and names the id
    assert where(found.diagnostics) == [
        "works/a/README.md, works/b/README.md, works/c/README.md"
    ]
    assert found.diagnostics[0].message == "Works share the id `k3m9xq`"


def test_each_shared_id_has_its_own_error_in_the_lookup_and_in_order() -> None:
    """AC-4: two groups of Works sharing an id give two errors, each for its id."""
    # Given a flat tree where `a` and `b` share `k` and `c` and `d` share `j`
    disk = _disk(
        {
            "a/R.md": _marked("k"),
            "b/R.md": _marked("k"),
            "c/R.md": _marked("j"),
            "d/R.md": _marked("j"),
        }
    )

    # When the Works are discovered and each id is looked up
    found = _find(disk, "flat")
    first = find_work(found, "k")
    second = find_work(found, "j")

    # Then each lookup yields the error that names its own paths, and the two
    # errors are in `ambiguous` in the order of `diagnostics`
    assert where(found.diagnostics) == [
        "works/a/R.md, works/b/R.md",
        "works/c/R.md, works/d/R.md",
    ]
    assert first == found.diagnostics[0]
    assert second == found.diagnostics[1]
    assert found.ambiguous == found.diagnostics
