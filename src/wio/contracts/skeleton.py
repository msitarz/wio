# SPDX-License-Identifier: Apache-2.0
"""The skeleton of an existing Work: what `wio contracts skeleton` prepares."""

from dataclasses import dataclass
from typing import TYPE_CHECKING

from wio.contracts.creation import find_template
from wio.contracts.discovery import discover_works
from wio.contracts.errors import ContractsError
from wio.contracts.refusal import refuse_tree
from wio.contracts.showing import find_by_id
from wio.formats import prepare_skeleton, read_metadata_block

if TYPE_CHECKING:
    from argparse import Namespace
    from collections.abc import Mapping, Sequence
    from pathlib import Path

    from wio.contracts import Services
    from wio.io.ports import FileSystem, Stdio
    from wio.models.template import Template
    from wio.models.works import Work

_NO_WORK = "`--work` is required; `wio templates show` prints a template alone"
CANNOT_KEEP = ("id", "template", "depends_on", "wio")
"""The keys that `--keep` refuses, because the skeleton handles them already."""


@dataclass(frozen=True)
class Skeleton:
    """A template's skeleton for one Work, prepared and not yet written.

    Provisional: the field names may change. It is immutable.

    Attributes:
        text: The whole skeleton: the template's form and body with the Work's
            `id` and `depends_on` and the kept keys in the block.
        dropped: The keys of the Work that `text` does not carry, in the order
            of the Work and without values, so that the note can name them. `id`,
            `depends_on`, `template` and `wio` are never among them, because the
            skeleton handles them already.
    """

    text: str
    dropped: tuple[str, ...]

    def note(self, path: Path) -> str:
        """Write the note about the keys of the Work that were not carried.

        The note is ``note: <path>: Not carried over: `roots`, `actions`. Use
        `--keep <key>` to carry one.`` on one line that ends in a newline, with
        the path written with `/` and the keys without values.

        Args:
            path: The Work's file, relative to the repository root.

        Returns:
            The note, or an empty string when nothing was dropped.
        """
        raise NotImplementedError


def run_skeleton(services: Services, args: Namespace, stdio: Stdio) -> int:
    """Run `wio contracts skeleton`.

    It reads through `services`, writes the skeleton to `stdio.stdout` and the
    note to `stdio.stderr`, and writes no file. A mistake is found before
    anything is written, so it prints nothing on standard output. When several
    apply the first of these is reported: a usage error, an incomplete tree, the
    Work, the template, then `--keep`. The usage error is a missing `--work`,
    which points to `wio templates show` and is refused before any file is read.
    The tree is walked with `discover_works` and judged with
    `refuse_tree(discovery, shared=False)`, so every error of finding the Works
    but a shared id refuses the command, with the pointer to
    `wio contracts check`, and a shared id refuses only its own lookup. The Work
    is found with `find_by_id` of `wio.contracts.showing`, which gives the
    messages of `show`: no Work has the id, with the closest one, or two share
    it.

    Args:
        services: What the command reads the project through.
        args: What the parser read: `template`, the name of the template, `work`,
            the id or `None` when it was not given, and `keep`, the keys to carry
            in the order given.
        stdio: Where the skeleton and the note go.

    Returns:
        0 after the skeleton is written. A note is written only when the Work
        has keys that the skeleton does not carry.

    Raises:
        ContractsError: A mistake of the user, as the functions it calls say.
            The command line writes it to standard error and exits 2.
        ConfigurationError: The config has an error.
        OSError: The Work's file or the template's cannot be read.
        UnicodeDecodeError: One of them is not UTF-8.
    """
    if args.work is None:
        raise ContractsError(_NO_WORK)
    config = services.settings.load()
    root = services.repository.root()
    discovery = discover_works(root, config.works, services.files)
    refuse_tree(discovery, shared=False)
    work = find_by_id(discovery, args.work)
    template = find_template(args.template, services.catalog, entry=False)
    skeleton = plan_skeleton(template, work, args.keep, root, services.files)
    stdio.stdout.write(skeleton.text)
    stdio.stderr.write(skeleton.note(work.path))
    return 0


def check_keep(keep: Sequence[str], keys: Sequence[str]) -> None:
    """Refuse a `--keep` that names a key that cannot be carried.

    Args:
        keep: The keys to carry, as typed.
        keys: The keys of the Work, in its order.

    Raises:
        ContractsError: A name in `CANNOT_KEEP` is refused first, and says that
            it cannot be kept; then a key that the Work does not have, which
            lists the keys that can be kept, those of the Work without
            `CANNOT_KEEP`, in the order of the Work.
    """
    raise NotImplementedError


def plan_skeleton(
    template: Template,
    work: Work,
    keep: Sequence[str],
    root: Path,
    files: FileSystem,
) -> Skeleton:
    """Prepare the template's skeleton for a Work without writing a file.

    The skeleton is the template's, with the Work's identity: the `id` first,
    after `wio = 1` in front matter, the requested `template`, and the Work's
    `depends_on` as its file has it, a wrong type included. A Work with no
    `depends_on` leaves the template's as the template has it, and one with
    `depends_on = []` gives `depends_on = []`. A kept key or table replaces the
    template's and is added when the template has none. The Work's keys are read
    again from its file, because the `Work` holds only the fields that the other
    commands use. The block is rewritten with the first line ending of the
    skeleton, and its body stays as the template has it. The skeleton comes from
    `prepare_skeleton` and the keys are set with `set_block_keys`.

    Args:
        template: The usable template.
        work: The Work, whose file is read for its keys.
        keep: The keys to carry besides the identity, as typed.
        root: The repository root, which the paths are relative to.
        files: Reads the template and the Work's file.

    Returns:
        The skeleton and the keys that it did not carry.

    Raises:
        ContractsError: `check_keep` refuses `keep`.
        OSError: A file cannot be read.
        UnicodeDecodeError: A file is not UTF-8.
    """
    prepared = prepare_skeleton(template.name, files.read_text(root / template.path))
    block = read_metadata_block(files.read_text(root / work.path))
    assert block is not None
    check_keep(keep, tuple(block.data))
    return carry_keys(prepared, block.data, keep)


def carry_keys(
    prepared: str, data: Mapping[str, object], keep: Sequence[str]
) -> Skeleton:
    """Put the identity and the kept keys of a Work into a prepared skeleton.

    `id` goes first and `depends_on` is the Work's when it has one. Each kept key
    replaces the skeleton's, or is added, and a key that is a table is carried as
    a value. The keys that the Work has and the skeleton did not take, besides
    `CANNOT_KEEP`, are `dropped`, in the order of the Work.

    Args:
        prepared: The skeleton that `prepare_skeleton` gives for the template.
        data: The keys of the Work as its block holds them, without `wio`.
        keep: The keys to carry, already checked by `check_keep`.

    Returns:
        The skeleton and the keys that were not carried.
    """
    raise NotImplementedError
