# SPDX-License-Identifier: Apache-2.0
"""Tests of the id and the place of a new Work."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Literal, override

import pytest

from tests.unit.contracts.helpers import work_with_id
from tests.unit.fakes import ROOT, MemoryFileSystem
from wio.contracts import (
    ContractsError,
    NameArguments,
    RandomIds,
    WorkDiscovery,
    choose_slug,
    decide_place,
    discover_works,
    new_id,
    write_new,
)
from wio.models.config import Works as WorksSettings

if TYPE_CHECKING:
    from collections.abc import Iterable, Mapping, Sequence

WORKS = ".agents/wio/works"
EMPTY = WorkDiscovery((), (), (), (), (), ())


@dataclass
class _Disk(MemoryFileSystem):
    """A file system that also holds empty directories and records its writes."""

    empty: set[Path] = field(default_factory=set)
    written: list[Path] = field(default_factory=list)

    @override
    def exists(self, path: Path) -> bool:
        """Tell whether a file or a directory exists.

        Args:
            path: The path.

        Returns:
            True for a file, for a directory with files and for an empty one.
        """
        return path in self.empty or super().exists(path)

    @override
    def is_dir(self, path: Path) -> bool:
        """Tell whether a path is a directory.

        Args:
            path: The path.

        Returns:
            True for a directory with files or an empty one.
        """
        return path in self.empty or super().is_dir(path)

    @override
    def write_text(self, path: Path, text: str) -> None:
        """Store a text and record the path.

        Args:
            path: The file.
            text: Its content.
        """
        self.written.append(path)
        super().write_text(path, text)


def _marked(work_id: str | None) -> str:
    """Write a file with a metadata block.

    Args:
        work_id: The id, or `None` for a block with no `id`.

    Returns:
        The text of the file.
    """
    line = 'template = "feature.leaf"' if work_id is None else f'id = "{work_id}"'
    return f"<!-- wio\n{line}\n-->\n\n# Title\n"


def _disk(
    files: Mapping[str, str | None],
    links: Iterable[str] = (),
    empty: Iterable[str] = (),
) -> _Disk:
    """Build a file system under the Works directory.

    Args:
        files: The files, by path relative to the Works directory; a value of
            `None` is a file with a block that has no `id`, and a text that does
            not start with `<` is the id of a Work.
        links: The symbolic links, relative to the Works directory.
        empty: The empty directories, relative to the Works directory.

    Returns:
        The file system.
    """
    base = ROOT / WORKS
    return _Disk(
        {
            base / name: text if text and text.startswith("<") else _marked(text)
            for name, text in files.items()
        },
        links={base / name for name in links},
        empty={base / name for name in empty},
    )


def _place(
    disk: _Disk,
    mode: Literal["flat", "nesting"] = "nesting",
    **given: str | None,
) -> Path:
    """Decide the place of a new Work in what a disk holds.

    Args:
        disk: The file system.
        mode: The hierarchy mode.
        **given: The options that were typed.

    Returns:
        The place.
    """
    settings = WorksSettings(dir=WORKS, hierarchy=mode)
    found = discover_works(ROOT, settings, disk)
    options: dict[str, str | None] = {
        "slug": None,
        "title": None,
        "path": None,
        "parent": None,
    }
    options.update(given)
    return decide_place(ROOT, settings, found, disk, NameArguments(**options))


def _refusal(
    disk: _Disk, mode: Literal["flat", "nesting"] = "nesting", **given: str | None
) -> str:
    """Decide a place that is refused.

    Args:
        disk: The file system.
        mode: The hierarchy mode.
        **given: The options that were typed.

    Returns:
        The message of the error.
    """
    with pytest.raises(ContractsError) as raised:
        _place(disk, mode, **given)
    return str(raised.value)


def _slug(**given: str | None) -> str:
    """Choose the slug of a call.

    Args:
        **given: The options that were typed.

    Returns:
        The slug.
    """
    options: dict[str, str | None] = {
        "slug": None,
        "title": None,
        "path": None,
        "parent": None,
    }
    options.update(given)
    return choose_slug(NameArguments(**options))


def test_a_slug_is_derived_from_a_title_by_one_rule() -> None:
    """The slug is ASCII, lowercase, joined by single `-` and at most 48 long."""
    # Given titles with accents, letters to write out, runs of separators, a
    # character that is dropped and a title that is long
    titles = [
        "Read config.toml",
        "Łódź café",
        "Straße æon",
        "  --A  B--  ",
        "aпb",
        "a" * 47 + " b",
    ]

    # When the slug of each is derived
    slugs = [_slug(title=title) for title in titles]

    # Then they are as the rule gives them, the last cut at 48 characters
    assert slugs == [
        "read-config-toml",
        "lodz-cafe",
        "strasse-aeon",
        "a-b",
        "ab",
        "a" * 47,
    ]


@pytest.mark.parametrize(
    ("letter", "written"),
    [
        ("ł", "l"),
        ("ø", "o"),
        ("đ", "d"),
        ("ð", "d"),
        ("ħ", "h"),
        ("ı", "i"),
        ("æ", "ae"),
        ("œ", "oe"),
        ("ß", "ss"),
        ("þ", "th"),
    ],
)
def test_each_letter_of_the_table_is_written_out(letter: str, written: str) -> None:
    """A letter that does not fold to ASCII is written out, not dropped."""
    # Given a title with the letter between two others
    title = f"x{letter}x"

    # When the slug is derived
    slug = _slug(title=title)

    # Then the letter is written out as the table says
    assert slug == f"x{written}x"


def test_the_slug_is_cut_at_exactly_48_characters() -> None:
    """The limit is 48: a longer title gives 48 characters and no more."""
    # Given a title of 48 letters, a space and another letter
    title = "a" * 48 + " b"

    # When the slug is derived
    slug = _slug(title=title)

    # Then it holds the 48 letters
    assert slug == "a" * 48


def test_a_title_with_no_usable_letter_asks_for_a_slug() -> None:
    """A title that leaves nothing is an error that names `--slug`."""
    # Given a title with no ASCII letter or digit
    title = "Привет"

    # When the slug is derived
    with pytest.raises(ContractsError) as raised:
        _slug(title=title)

    # Then the error asks for `--slug`
    assert "--slug" in str(raised.value)


def test_a_given_slug_must_be_lowercase_kebab_case() -> None:
    """A slug that could hide the Work or leave its directory is refused."""
    # Given slugs of which two are kebab case and eight are not
    good = ["login", "2026-11-02-login-design"]
    bad = [".draft", "a/b", "..", "Login", "a_b", "a--b", "-a", ""]

    # When each is checked
    used = [_slug(slug=slug) for slug in good]
    refused = []
    for slug in bad:
        with pytest.raises(ContractsError) as raised:
            _slug(slug=slug)
        refused.append(str(raised.value))

    # Then the good ones are used as written, and each other says what a slug is
    assert used == good
    assert all(
        "lowercase letters and digits joined by single `-`" in m for m in refused
    )


def test_an_empty_slug_counts_as_given_even_with_a_title() -> None:
    """An empty `--slug` is not replaced by the title."""
    # Given an empty slug and a title
    # When the slug is chosen
    with pytest.raises(ContractsError) as raised:
        _slug(slug="", title="Child")

    # Then the slug is refused for its form
    assert "lowercase letters and digits" in str(raised.value)


def test_a_slug_wins_over_a_title_when_both_are_given() -> None:
    """The slug is used as written, whatever the title says."""
    # Given a slug and a title that differ
    # When the slug is chosen
    slug = _slug(slug="child", title="Other")

    # Then it is the given one
    assert slug == "child"


def _nesting_disk() -> _Disk:
    """Build the Works of the first scenario of AC-3.

    Returns:
        A Work `p5n2hv` at `p/README.md` and `k3m9xq` at `q/spec.md`.
    """
    return _disk({"p/README.md": "p5n2hv", "q/spec.md": "k3m9xq"})


def test_the_default_place_follows_the_arguments_under_nesting() -> None:
    """The place is below the Works directory, or the directory of the parent."""
    # Given two Works under nesting and the title `Child`
    disk = _nesting_disk()

    # When the place is decided with the title alone, with each parent, and with
    # a slug and a title
    found = [
        _place(disk, title="Child"),
        _place(disk, title="Child", parent="p5n2hv"),
        _place(disk, title="Child", parent="k3m9xq"),
        _place(disk, slug="child", title="Other"),
    ]

    # Then the paths are those of the Works directory and of the parents, and the
    # last is accepted with both options
    assert [p.as_posix() for p in found] == [
        f"{WORKS}/child/README.md",
        f"{WORKS}/p/child/README.md",
        f"{WORKS}/q/child/README.md",
        f"{WORKS}/child/README.md",
    ]


def test_options_that_exclude_each_other_or_name_nothing_are_refused() -> None:
    """Each call that cannot be decided gives the error of its own."""
    # Given the Works, an empty directory `child` and two Works sharing an id
    disk = _disk(
        {
            "p/README.md": "p5n2hv",
            "q/spec.md": "k3m9xq",
            "s/README.md": "a7b2c4",
            "t/README.md": "a7b2c4",
        },
        empty=["child"],
    )

    # When the place is decided with no name, with `--path` and `--slug`, with
    # `--path` and `--parent`, with an unknown parent, a shared one and a title
    # whose directory exists
    messages = [
        _refusal(disk),
        _refusal(disk, path=f"{WORKS}/x/y.md", slug="x"),
        _refusal(disk, path=f"{WORKS}/x/y.md", parent="p5n2hv"),
        _refusal(disk, parent="k3m9xr", title="Child"),
        _refusal(disk, parent="a7b2c4", title="Child"),
        _refusal(disk, title="Child"),
    ]

    # Then each is the error that says so, naming what it needs
    assert "name is required" in messages[0]
    assert "exclude each other" in messages[1]
    assert "exclude each other" in messages[2]
    assert "`k3m9xr`" in messages[3]
    assert "closest is `k3m9xq`" in messages[3]
    assert "shared" in messages[4]
    assert f"`{WORKS}/child`" in messages[5]
    assert "exists" in messages[5]


def test_a_parent_needs_nesting() -> None:
    """Under flat a parent is an error, before the slug is looked at."""
    # Given `flat` and a Work
    disk = _disk({"p/README.md": "p5n2hv"})

    # When the place is decided with a parent, and with a parent and a bad slug
    message = _refusal(disk, "flat", parent="p5n2hv", title="Child")
    first = _refusal(disk, "flat", parent="p5n2hv", slug="Bad")

    # Then both say `--parent` needs `nesting`
    assert "`--parent` needs" in message
    assert "nesting" in message
    assert first == message


def test_a_path_must_be_one_that_a_work_could_have() -> None:
    """Only a file that would be a Work and does not exist is accepted."""
    # Given a Work under nesting, a symbolic link `link` and the paths
    disk = _disk({"p/README.md": "p5n2hv"}, links=["link"])
    refused = {
        "/tmp/x.md": "relative",
        f"{WORKS}/../x.md": "with no `..`",
        "docs/x.md": "not under the Works directory",
        f"{WORKS}/.hidden/x.md": "hidden directory `.hidden`",
        f"{WORKS}/q/spec.txt": "`.md`",
        f"{WORKS}/q/spec.MD": "`.md`",
        f"{WORKS}/p/README.md": "holds a marked file",
        f"{WORKS}/top.md": "directly in the Works directory",
        f"{WORKS}/p/other.md": "holds a marked file",
        f"{WORKS}/link/x.md": f"symbolic link `{WORKS}/link`",
    }

    # When each is checked as the path of a new Work
    accepted = _place(disk, path=f"{WORKS}/q/spec.md")
    messages = {path: _refusal(disk, path=path) for path in refused}

    # Then the first is accepted, and each other names the path and says why
    assert accepted == Path(f"{WORKS}/q/spec.md")
    for path, reason in refused.items():
        assert path in messages[path]
        assert reason in messages[path]


def test_a_directory_that_exists_and_a_file_that_was_left_out() -> None:
    """An existing directory is no obstacle, and a left-out file counts."""
    # Given a directory `q` that exists and a marked file in `r` with no `id`
    disk = _disk({"q/notes.txt": "kept", "r/one.md": None})

    # When `q/new.md` and `r/two.md` are checked
    accepted = _place(disk, path=f"{WORKS}/q/new.md")
    message = _refusal(disk, path=f"{WORKS}/r/two.md")

    # Then the first is accepted and the second says the directory holds a
    # marked file already
    assert accepted == Path(f"{WORKS}/q/new.md")
    assert "holds a marked file already" in message
    assert f"{WORKS}/r/one.md" in message


def test_only_a_directory_is_hidden_and_an_empty_directory_is_no_obstacle() -> None:
    """A file name that starts with a dot is allowed, and so is an empty directory."""
    # Given an empty directory `e`
    disk = _disk({"p/README.md": "p5n2hv"}, empty=["e"])

    # When a path with a hidden file name and one in the empty directory are
    # checked
    hidden = _place(disk, path=f"{WORKS}/q/.x.md")
    inside = _place(disk, path=f"{WORKS}/e/new.md")

    # Then both are accepted
    assert [hidden.name, inside.name] == [".x.md", "new.md"]


def test_a_bad_slug_is_refused_before_an_unknown_parent() -> None:
    """The slug is judged before the parent is looked up."""
    # Given a Work and a slug that is not valid with a parent that has no Work
    disk = _disk({"p/README.md": "p5n2hv"})

    # When the place is decided
    message = _refusal(disk, slug="Bad", parent="zzzzzz")

    # Then the error is about the slug
    assert "slug" in message
    assert "zzzzzz" not in message


def test_a_directory_whose_files_a_collision_excluded_holds_marked_files() -> None:
    """A directory with two marked files, both excluded, takes no third."""
    # Given a directory with two marked files under nesting
    disk = _disk({"c/a.md": "aaaaaa", "c/b.md": "bbbbbb"})

    # When a path in that directory is checked
    message = _refusal(disk, path=f"{WORKS}/c/new.md")

    # Then the directory holds a marked file already
    assert "holds a marked file already" in message


def test_under_flat_a_path_may_be_at_the_top_or_beside_awork_with_id() -> None:
    """The rules of nesting do not apply under flat."""
    # Given `flat` and a Work in `p`
    disk = _disk({"p/README.md": "p5n2hv"})

    # When `top.md` and `p/other.md` are checked
    found = [
        _place(disk, "flat", path=f"{WORKS}/top.md"),
        _place(disk, "flat", path=f"{WORKS}/p/other.md"),
    ]

    # Then both are accepted
    assert [p.as_posix() for p in found] == [f"{WORKS}/top.md", f"{WORKS}/p/other.md"]


@dataclass
class _Entropy:
    """An `Entropy` that gives prepared bytes, the last again after them."""

    calls: Sequence[bytes]
    counts: list[int] = field(default_factory=list)

    def random_bytes(self, count: int) -> bytes:
        """Give the next prepared bytes.

        Args:
            count: How many bytes were asked for.

        Returns:
            The next call's bytes, or the last when none is left.
        """
        self.counts.append(count)
        return self.calls[min(len(self.counts), len(self.calls)) - 1]


def test_an_id_is_drawn_from_the_bytes_until_it_is_free() -> None:
    """A candidate that a Work has is drawn again."""
    # Given bytes 0 to 5, then 6 to 11, an empty tree and one with `012345`
    first, second = bytes(range(6)), bytes(range(6, 12))

    # When an id is drawn for each
    free = new_id(RandomIds(_Entropy([first, second])), [])
    taken = new_id(RandomIds(_Entropy([first, second])), [work_with_id("012345")])

    # Then they are `012345` and `6789ab`, of the alphabet only
    assert (free, taken) == ("012345", "6789ab")
    assert set(free + taken) <= set("0123456789abcdefghjkmnpqrstvwxyz")


def test_only_the_low_five_bits_of_a_byte_make_a_character() -> None:
    """Bytes above 31 wrap around the alphabet."""
    # Given bytes 255, 32, 33, 250, 128 and 31
    entropy = _Entropy([bytes([255, 32, 33, 250, 128, 31])])

    # When an id is drawn
    found = new_id(RandomIds(entropy), [])

    # Then each byte gave the character of its low five bits, in one call of six
    assert found == "z01t0z"
    assert entropy.counts == [6]


def test_a_shared_id_is_taken_and_the_draw_gives_up_after_100_tries() -> None:
    """A shared id is drawn past, and a tree that holds every draw ends in error."""
    # Given a tree that shares `012345`, and one that holds it with an `Entropy`
    # that repeats its bytes
    first, second = bytes(range(6)), bytes(range(6, 12))
    shared = [work_with_id("012345"), work_with_id("012345")]
    stuck = _Entropy([first])

    # When an id is drawn for each
    drawn = new_id(RandomIds(_Entropy([first, second])), shared)
    with pytest.raises(ContractsError) as raised:
        new_id(RandomIds(stuck), [work_with_id("012345")])

    # Then the first is `6789ab`, and the second asked exactly 100 times for six
    # bytes and gave an error
    assert drawn == "6789ab"
    assert stuck.counts == [6] * 100
    assert "100" in str(raised.value)


def test_deciding_writes_nothing_and_the_guard_never_overwrites() -> None:
    """The place is decided without a write, and only the guard writes."""
    # Given `flat`, a recording file system and a path that exists
    disk = _disk({"old/spec.md": "old001"})
    free, old = Path(f"{WORKS}/new/spec.md"), Path(f"{WORKS}/old/spec.md")
    before = dict(disk.files)

    # When the place is decided for each, and the guard writes to each
    decided = _place(disk, "flat", path=free.as_posix())
    refusal = _refusal(disk, "flat", path=old.as_posix())
    write_new(disk, ROOT, free, "fresh")
    with pytest.raises(ContractsError) as raised:
        write_new(disk, ROOT, old, "lost")

    # Then deciding wrote nothing and refused the existing path by name, the
    # guard wrote the free one and refused the other the same way
    assert decided == free
    assert old.as_posix() in refusal
    assert disk.written == [ROOT / free]
    assert disk.files[ROOT / free] == "fresh"
    assert {k: v for k, v in disk.files.items() if k != ROOT / free} == before
    assert old.as_posix() in str(raised.value)
