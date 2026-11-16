# SPDX-License-Identifier: Apache-2.0
"""The skeleton of an existing Work: what `wio contracts skeleton` prepares."""

from dataclasses import dataclass
from typing import TYPE_CHECKING

from wio.contracts.creation import find_template
from wio.contracts.discovery import discover_works
from wio.contracts.errors import ContractsError
from wio.contracts.refusal import refuse_tree
from wio.contracts.showing import find_by_id
from wio.formats import (
    prepare_skeleton,
    read_metadata_block,
    render_text,
    set_block_keys,
)
from wio.models.diagnostics import Diagnostic

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
        if not self.dropped:
            return ""
        names = ", ".join(f"`{name}`" for name in self.dropped)
        message = f"Not carried over: {names}. Use `--keep <key>` to carry one."
        return render_text([Diagnostic("note", path.as_posix(), message)]) + "\n"


def run_skeleton(services: Services, args: Namespace, stdio: Stdio) -> int:
    """Run `wio contracts skeleton`.

    It writes the skeleton to `stdio.stdout` and the note to `stdio.stderr`, and
    writes no file. A mistake is found before anything is written, so it prints
    nothing on standard output. When several apply the first of these is
    reported: a usage error, an incomplete tree, the Work, the template, then
    `--keep`. The usage error is a missing `--work`, which points to
    `wio templates show` and is refused before any file is read. Every error of
    finding the Works but a shared id refuses the command, with the pointer to
    `wio contracts check`, and a shared id refuses only its own lookup. The Work
    and the template are found as `show` and `new` find theirs, so the messages
    are the same.

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
    for name in keep:
        if name in CANNOT_KEEP:
            msg = f"The key `{name}` cannot be kept: the skeleton carries it already"
            raise ContractsError(msg)
    for name in keep:
        if name not in keys:
            raise ContractsError(_no_such_key(name, keys))


def _no_such_key(name: str, keys: Sequence[str]) -> str:
    """Word the refusal of a key that the Work does not have.

    Args:
        name: The key that was asked for.
        keys: The keys of the Work, in its order.

    Returns:
        The message, which lists the keys that can be kept, or says there are
        none.
    """
    keepable = [key for key in keys if key not in CANNOT_KEEP]
    listed = ", ".join(f"`{key}`" for key in keepable)
    hint = f"; it can keep {listed}" if keepable else "; it has no key to keep"
    return f"The Work has no key `{name}`{hint}"


def plan_skeleton(
    template: Template,
    work: Work,
    keep: Sequence[str],
    root: Path,
    files: FileSystem,
) -> Skeleton:
    """Prepare the template's skeleton for a Work without writing a file.

    The template's skeleton is the one `prepare_skeleton` gives, and
    `carry_keys` says what the Work adds to it. The Work's keys are read again
    from its file, because the `Work` holds only the fields that the other
    commands use, and `--keep` is checked against them before anything is
    carried.

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

    `id` goes first and `depends_on` is the Work's when it has one, as its file
    has it, a wrong type included; a Work with none leaves the template's, and
    `depends_on = []` gives `[]`. Each kept key replaces the skeleton's, or is
    added, and a table is carried as a value. The form, the first line ending,
    the `template` and the body stay as the skeleton has them, and TOML comments
    of the block are not carried. What the skeleton did not take is `dropped`.

    Args:
        prepared: The skeleton that `prepare_skeleton` gives for the template.
        data: The keys of the Work as its block holds them, without `wio`.
        keep: The keys to carry, already checked by `check_keep`.

    Returns:
        The skeleton and the keys that were not carried.
    """
    identity = {"id": data["id"]}
    if "depends_on" in data:
        identity["depends_on"] = data["depends_on"]
    kept = {name: data[name] for name in dict.fromkeys(keep)}
    dropped = tuple(
        name for name in data if name not in CANNOT_KEEP and name not in kept
    )
    return Skeleton(set_block_keys(prepared, {**identity, **kept}), dropped)
