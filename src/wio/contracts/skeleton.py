# SPDX-License-Identifier: Apache-2.0
"""The skeleton of an existing Work: what `wio contracts skeleton` prepares."""

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from argparse import Namespace
    from collections.abc import Sequence
    from pathlib import Path

    from wio.contracts import Services
    from wio.contracts.discovery import WorkDiscovery
    from wio.contracts.ports import TemplateCatalog
    from wio.io.ports import FileSystem, Stdio
    from wio.models.template import Template
    from wio.models.works import Work

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
            of the Work and without values, so that the note can name them.
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
    Work, the template, then `--keep`.

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
    raise NotImplementedError


def find_work_by_id(discovery: WorkDiscovery, work_id: str | None) -> Work:
    """Find the Work that `--work` names, or refuse.

    The tree is judged before, so only the lookup of a shared id is refused here,
    with the error of discovery.

    Args:
        discovery: What discovery found, with its tree judged complete.
        work_id: The `--work` as typed, or `None` when it was not given.

    Returns:
        The Work.

    Raises:
        ContractsError: `--work` is missing, which points to
            `wio templates show`; no Work has the id, which names it and the
            closest id of the Works; or two Works share it.
    """
    raise NotImplementedError


def usable_template(name: str, catalog: TemplateCatalog) -> Template:
    """Find the template to prepare the skeleton from, or refuse.

    Args:
        name: The template's name as typed.
        catalog: Finds templates and says which are rejected.

    Returns:
        The template.

    Raises:
        ContractsError: The template is rejected, which points to
            `wio templates check`, or no file has it, which points to
            `wio templates list`. A rejected template is reported first.
    """
    raise NotImplementedError


def check_keep(keep: Sequence[str], keys: Sequence[str]) -> None:
    """Refuse a `--keep` that names a key that cannot be carried.

    Args:
        keep: The keys to carry, as typed.
        keys: The keys of the Work, in its order.

    Raises:
        ContractsError: A name in `CANNOT_KEEP` is refused first, and says that
            it cannot be kept; then a key that the Work does not have, which
            lists the keys that can be kept in the order of the Work.
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
    skeleton, and its body stays as the template has it.

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
    raise NotImplementedError
