# SPDX-License-Identifier: Apache-2.0
"""The reader of a ruleset's manifest, which turns one `ruleset.toml` into data.

It does no input or output and reads only the text it is given, so finding the
file and judging what it declares against the rule files are for the caller.
"""

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import PurePosixPath

    from wio.models.diagnostics import Diagnostic
    from wio.models.rule import Manifest


@dataclass(frozen=True)
class ManifestReading:
    """What reading one `ruleset.toml` gave.

    Attributes:
        manifest: The manifest, or `None` when the text has an error.
        diagnostics: Every error and warning of the text, in the order of
            `sort_diagnostics`.
    """

    manifest: Manifest | None
    diagnostics: tuple[Diagnostic, ...]


def read_manifest(path: PurePosixPath, text: str) -> ManifestReading:
    """Read the text of a `ruleset.toml` into a manifest.

    Reuses `decode_toml` and `closest_key` of `wio.formats`, the forms of a
    family and a rule preset name of `wio.formats.grammar`, and `join_path` and
    `item_path` of `wio.formats.wording` for the places of the faults.

    Args:
        path: The path of the file relative to the repository root.
        text: The text of the file, decoded as UTF-8; an empty text is an empty
            manifest.

    Returns:
        The manifest, with the families and the rule presets in the order
        written, and no error when the text has the shape of a manifest. Each
        fault is one error and leaves the manifest out: text that does not parse
        is at the path followed by `:<line>`, and any other fault is at the path
        followed by `#` and the key path of the fault, such as `#description`
        or `#rule_presets.x.rules_include[0]`. A key that the manifest or a rule
        preset does not know is a warning at the same kind of place that names
        the key and the closest known key, and the manifest is still returned.
    """
    del text
    msg = f"read_manifest of {path} is declared by the architecture stage"
    raise NotImplementedError(msg)
