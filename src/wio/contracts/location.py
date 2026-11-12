# SPDX-License-Identifier: Apache-2.0
"""The id and the place of a new Work."""

import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import TYPE_CHECKING, Final, Literal, Protocol

from wio.contracts.discovery import find_work
from wio.contracts.errors import ContractsError
from wio.models.works import Work
lazy from wio.formats import closest_key

if TYPE_CHECKING:
    from collections.abc import Iterable

    from wio.contracts.discovery import WorkDiscovery
    from wio.env.ports import Entropy
    from wio.io.ports import FileSystem
    from wio.models.config import Works as WorksSettings

ID_ALPHABET: Final = "0123456789abcdefghjkmnpqrstvwxyz"
"""The characters of an id: no `i`, `l`, `o` or `u`, so it cannot be mistaken
for a digit."""
ID_LENGTH: Final = 6
"""How many characters an id has, and how many bytes one draw reads."""
MAX_DRAWS: Final = 100
"""How many ids are drawn before the command gives up."""
SLUG_LIMIT: Final = 48
"""The longest slug that a title gives."""
_SLUG: Final = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")
"""What a slug is: groups of lowercase letters and digits joined by one `-`."""
_UNUSABLE: Final = re.compile(r"[^a-z0-9]+")
"""A run of characters that a slug writes as one `-`."""
_WRITTEN_OUT: Final = str.maketrans(
    {
        "ł": "l",
        "ø": "o",
        "đ": "d",
        "ð": "d",
        "ħ": "h",
        "ı": "i",
        "æ": "ae",
        "œ": "oe",
        "ß": "ss",
        "þ": "th",
    }
)
"""The letters that do not fold to ASCII and are written out instead."""


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
        return "".join(ID_ALPHABET[byte & 0b11111] for byte in self._read(ID_LENGTH))


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
    if arguments.slug is not None:
        if _SLUG.fullmatch(arguments.slug) is None:
            message = (
                "A slug is lowercase letters and digits joined by single `-`, "
                f"not `{arguments.slug}`"
            )
            raise ContractsError(message)
        return arguments.slug
    slug = _slug_of_title(arguments.title or "")
    if not slug:
        message = "The title has no letter or digit to name the Work: use `--slug`"
        raise ContractsError(message)
    return slug


def _slug_of_title(title: str) -> str:
    """Apply the rule that turns a title into a slug.

    Args:
        title: The title as typed.

    Returns:
        The slug, empty when the title has no usable letter or digit.
    """
    written = title.lower().translate(_WRITTEN_OUT)
    folded = unicodedata.normalize("NFKD", written).encode("ascii", "ignore")
    dashed = _UNUSABLE.sub("-", folded.decode("ascii")).strip("-")
    return dashed[:SLUG_LIMIT].rstrip("-")


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
    path, parent = arguments.path is not None, arguments.parent is not None
    problems = (
        (
            arguments.slug is None and arguments.title is None and not path,
            "A name is required: give `--slug`, `--title` or `--path`",
        ),
        (
            path and arguments.slug is not None,
            "`--path` and `--slug` exclude each other",
        ),
        (
            path and parent and mode == "nesting",
            "`--path` and `--parent` exclude each other under `nesting`",
        ),
        (parent and mode == "flat", '`--parent` needs `hierarchy = "nesting"`'),
    )
    for applies, message in problems:
        if applies:
            raise ContractsError(message)


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
    found = find_work(discovery, parent)
    if isinstance(found, Work):
        return found.path.parent
    if found is None:
        close = closest_key(parent, (work.id for work in discovery.works))
        hint = f"; the closest is `{close}`" if close else ""
        message = f"No Work has the id `{parent}`{hint}"
    else:
        message = f"The id `{parent}` is shared by Works: {found.where}"
    raise ContractsError(message)


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
    place = PurePosixPath(path)
    works = PurePosixPath(settings.dir)
    reason = (
        _form_problem(place, works)
        or _link_problem(root, place, files)
        or (
            _nesting_problem(place, works, discovery)
            if settings.hierarchy == "nesting"
            else None
        )
    )
    if reason:
        message = f"`{path}` cannot be the path of a Work: {reason}"
        raise ContractsError(message)
    return Path(place)


def _form_problem(place: PurePosixPath, works: PurePosixPath) -> str | None:
    """Judge the written form of a path and where it lies.

    Args:
        place: The path as typed.
        works: The Works directory.

    Returns:
        The reason, or `None` for a relative path with no `..` that ends in
        `.md` and lies under the Works directory and below no hidden directory.
    """
    if place.is_absolute() or ".." in place.parts:
        return "it must be relative to the repository root, with no `..`"
    if not place.name.endswith(".md"):
        return "its name must end in `.md`"
    if works not in place.parents:
        return f"it is not under the Works directory `{works.as_posix()}`"
    hidden = [p for p in place.relative_to(works).parts[:-1] if p.startswith(".")]
    return f"it is under the hidden directory `{hidden[0]}`" if hidden else None


def _link_problem(root: Path, place: PurePosixPath, files: FileSystem) -> str | None:
    """Judge whether a path is or runs through a symbolic link.

    Args:
        root: The repository root, whose own path is not asked about.
        place: The path, relative to the root.
        files: The port.

    Returns:
        The reason naming the link, or `None`.
    """
    for part in (*reversed(place.parents), place):
        if part.parts and files.is_symlink(root / part):
            return f"it is or runs through the symbolic link `{part.as_posix()}`"
    return None


def _nesting_problem(
    place: PurePosixPath, works: PurePosixPath, discovery: WorkDiscovery
) -> str | None:
    """Judge a path by the rules of `nesting`.

    Args:
        place: The path, relative to the root.
        works: The Works directory.
        discovery: The Works and the marked files found.

    Returns:
        The reason when the path is directly in the Works directory, or its
        directory holds a Work, a file that was left out or a file that was
        excluded already, and `None` otherwise.
    """
    if place.parent == works:
        return "a Work cannot sit directly in the Works directory"
    found = (
        *(work.path for work in discovery.works),
        *discovery.left_out,
        *discovery.excluded,
    )
    held = next(
        (p for p in found if p.parent.as_posix() == place.parent.as_posix()), None
    )
    if held is None:
        return None
    return f"its directory holds a marked file already: `{held.as_posix()}`"


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
    if whole_directory and files.exists(root / place.parent):
        message = f"The directory `{place.parent.as_posix()}` exists already"
        raise ContractsError(message)
    if files.exists(root / place):
        message = f"`{place.as_posix()}` exists already"
        raise ContractsError(message)


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
