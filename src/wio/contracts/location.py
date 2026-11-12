# SPDX-License-Identifier: Apache-2.0
"""The id and the place of a new Work."""

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Final, Literal, Protocol

from wio.contracts.errors import ContractsError

if TYPE_CHECKING:
    from collections.abc import Iterable

    from wio.contracts.discovery import WorkDiscovery
    from wio.env.ports import Entropy
    from wio.io.ports import FileSystem
    from wio.models.config import Works as WorksSettings
    from wio.models.works import Work

ID_ALPHABET: Final = "0123456789abcdefghjkmnpqrstvwxyz"
"""The characters of an id: no `i`, `l`, `o` or `u`, so it cannot be mistaken
for a digit."""
ID_LENGTH: Final = 6
"""How many characters an id has, and how many bytes one draw reads."""
MAX_DRAWS: Final = 100
"""How many ids are drawn before the command gives up."""
SLUG_LIMIT: Final = 48
"""The longest slug that a title gives."""


@dataclass(frozen=True)
class NameArguments:
    """The options of `new` that name the Work and say where it goes.

    Provisional: the new leaf may add a field it needs. It is immutable and
    holds each option as typed, `None` when it was not given, so that an empty
    `--slug` counts as given.

    Attributes:
        slug: The `--slug`, the name of the Work's directory, used as written.
        title: The `--title`, from which a slug is derived when there is no
            `--slug`.
        path: The `--path`, the file of the new Work relative to the repository
            root.
        parent: The `--parent`, the id of the parent Work.
    """

    slug: str | None
    title: str | None
    path: str | None
    parent: str | None


class IdGenerator(Protocol):
    """Draws the candidate ids of new Works, so another source may replace it."""

    def draw(self) -> str:
        """Draw one candidate id, without looking at the tree.

        Returns:
            A string of `ID_LENGTH` characters of `ID_ALPHABET`.
        """
        ...


class RandomIds:
    """The one `IdGenerator`: each id is read from `Entropy`.

    One draw is one `Entropy.random_bytes(ID_LENGTH)` call, and each byte gives
    the character of its low five bits, so the alphabet is used evenly.
    """

    def __init__(self, entropy: Entropy) -> None:
        """Keep the call that reads bytes, the only source of randomness of an id.

        Args:
            entropy: The port that gives random bytes.
        """
        self._read = entropy.random_bytes

    def draw(self) -> str:
        """Draw one candidate id with one call of `random_bytes`.

        Returns:
            Six characters of `ID_ALPHABET`.
        """
        raise NotImplementedError


def new_id(generator: IdGenerator, works: Iterable[Work]) -> str:
    """Draw ids until one is not the id of a Work in the tree.

    Args:
        generator: Where the candidates come from.
        works: The Works of the tree. One that shares its id with another counts
            once and is as taken as any other.

    Returns:
        The first candidate that no Work has.

    Raises:
        ContractsError: `MAX_DRAWS` candidates in a row were taken.
    """
    taken = {work.id for work in works}
    for _ in range(MAX_DRAWS):
        candidate = generator.draw()
        if candidate not in taken:
            return candidate
    message = f"No free id was found in {MAX_DRAWS} draws"
    raise ContractsError(message)


def choose_slug(arguments: NameArguments) -> str:
    """Pick the name of a Work's directory from `--slug` or `--title`.

    A `--slug` is used as written, an empty one included, and must be lowercase
    letters and digits in groups joined by single `-`, so that it can never start
    with `.`, hold `/` or `..` and hide the Work.

    Without a `--slug` it is derived from the title. The title is lowercased and
    the letters `ł ø đ ð ħ ı æ œ ß þ` are written as `l o d d h i ae oe ss th`.
    The other accents fold to ASCII and every character still not ASCII is
    dropped. Each run of characters outside `a-z0-9` becomes one `-`, `-` is
    trimmed from both ends, the slug is cut at `SLUG_LIMIT` characters and a
    trailing `-` is trimmed again.

    Args:
        arguments: The options; `--slug` or `--title` is given.

    Returns:
        The slug.

    Raises:
        ContractsError: A given slug is not of that form, with a message that
            says what a slug is, or a title gives an empty one, with a message
            that asks for `--slug`.
    """
    raise NotImplementedError


def decide_place(
    root: Path,
    settings: WorksSettings,
    discovery: WorkDiscovery,
    files: FileSystem,
    arguments: NameArguments,
) -> Path:
    """Decide the file of a new Work, and write nothing.

    The default place is `<Works directory>/<slug>/README.md`, and under
    `nesting` with a parent it is `<the directory of the parent's file>/<slug>/
    README.md`. A `--path` is used as it is when a Work could have it: relative
    to the root without `..`, ending in `.md`, under the Works directory, below
    no hidden directory, through no symbolic link, and under `nesting` neither
    directly in the Works directory nor in a directory that holds a marked file
    already, one left out or excluded included. The directory of the default
    place, empty or not, and the file of any place must not exist.

    There is one error for each call, the first that applies: no name, options
    that exclude each other, `--parent` under `flat`, a slug that is not valid
    or empty, a parent that has no Work, with the closest id, or is shared, a
    path that is not a Work's, and a directory or a file that exists.

    Args:
        root: The repository root.
        settings: The `[works]` table of the config.
        discovery: What one walk of the Works directory found: the Works and the
            marked files that were left out or excluded.
        files: The port that tells whether a path exists, is a directory or is a
            symbolic link. It is not written.
        arguments: The options that name the Work.

    Returns:
        The path of the new file, relative to the root, written with `/`.

    Raises:
        ContractsError: One of the errors above.
    """
    _check_options(arguments, settings.hierarchy)
    if arguments.path is None:
        slug = choose_slug(arguments)
        place = _default_place(settings, discovery, arguments, slug)
    else:
        place = _checked_path(root, settings, discovery, files, arguments.path)
    _refuse_existing(root, place, files, whole_directory=arguments.path is None)
    return place


def _check_options(arguments: NameArguments, mode: Literal["flat", "nesting"]) -> None:
    """Refuse a call that names nothing or whose options cannot be combined.

    Args:
        arguments: The options.
        mode: The hierarchy mode of the config.

    Raises:
        ContractsError: No name is given, `--path` comes with `--slug`, or with
            `--parent` under `nesting`, or `--parent` is given under `flat`; the
            first that applies.
    """
    raise NotImplementedError


def _default_place(
    settings: WorksSettings,
    discovery: WorkDiscovery,
    arguments: NameArguments,
    slug: str,
) -> Path:
    """Put a new Work in a directory of its own.

    Args:
        settings: The `[works]` table.
        discovery: The Works found, for the parent.
        arguments: The options, whose `--parent` picks the directory.
        slug: The name of the Work's directory.

    Returns:
        `<Works directory>/<slug>/README.md`, or with a parent the same below the
        directory of its file.
    """
    parent = arguments.parent
    base = (
        Path(settings.dir) if parent is None else _parent_directory(discovery, parent)
    )
    return base / slug / "README.md"


def _parent_directory(discovery: WorkDiscovery, parent: str) -> Path:
    """Find the directory of a parent's file.

    Args:
        discovery: The Works found.
        parent: The id given to `--parent`.

    Returns:
        The directory of the file of the Work with that id.

    Raises:
        ContractsError: No Work has the id, with the closest id when one is
            close, or two Works share it.
    """
    raise NotImplementedError


def _checked_path(
    root: Path,
    settings: WorksSettings,
    discovery: WorkDiscovery,
    files: FileSystem,
    path: str,
) -> Path:
    """Accept a `--path` that a Work could have.

    Args:
        root: The repository root.
        settings: The `[works]` table.
        discovery: The Works and the marked files found.
        files: The port that tells what exists and what is a symbolic link.
        path: The `--path` as typed.

    Returns:
        The path as a `Path`, relative to the root.

    Raises:
        ContractsError: The path is not one that a Work could have, with the
            reason and the path named.
    """
    raise NotImplementedError


def _refuse_existing(
    root: Path, place: Path, files: FileSystem, *, whole_directory: bool
) -> None:
    """Refuse a place that is taken.

    Args:
        root: The repository root.
        place: The file decided on.
        files: The port that tells what exists.
        whole_directory: Whether the directory of the place, empty or not, must
            not exist, as for the default place, and not only the file.

    Raises:
        ContractsError: The directory or the file exists, and the message names
            it.
    """
    raise NotImplementedError


def write_new(files: FileSystem, root: Path, path: Path, text: str) -> None:
    """Write a new contract and never overwrite a file.

    It is the only function here that writes. It creates the directories of the
    path, as the port does, and checks that the file does not exist first. Two
    creators racing for one path are not handled.

    Args:
        files: The port that writes.
        root: The repository root.
        path: The file, relative to the root, as `decide_place` returned it.
        text: The contract.

    Raises:
        ContractsError: The file exists. The message names it, and nothing is
            changed.
    """
    target = root / path
    if files.exists(target):
        message = f"`{path.as_posix()}` exists already, and wio never overwrites it"
        raise ContractsError(message)
    files.write_text(target, text)
