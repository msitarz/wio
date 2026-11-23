# SPDX-License-Identifier: Apache-2.0
"""The errors that only the rule files and the config show together.

The discovery judges each rule and manifest on its own, and `wio config check`
judges the references of the config as text. What is left is the faults that
need both: a reference that names nothing in its ruleset, a rule preset that
includes itself through others, a manifest that defines `all`, and a
root-independent ruleset that a root reaches. This module finds them without
reading a file, so that `wio rules check` can add them to the faults of the
discovery.
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from wio.models.config import Config
    from wio.models.diagnostics import Diagnostic
    from wio.rules.discovery import Discovery


def check_errors(config: Config, discovery: Discovery) -> tuple[Diagnostic, ...]:
    """Find the errors of the rule files, the manifests and the references.

    It returns the errors of the discovery as they are, and not its warnings,
    and then the errors of the references. The config is valid, so every
    reference in it is well-formed, and what needs the rule files is whether the
    item after the dot exists. Each entry is judged where it is written and by
    itself with `expand`: an entry of the config in the config scope, and each
    entry of each rule preset of a manifest, include or exclude, in the scope of
    its ruleset. A problem that belongs to a rule preset that the entry reached
    is not the entry's, so it is reported at that rule preset's own key and once,
    however many entries reach it, and a `cycle` problem is dropped because the
    cycles of a manifest are found by `find_cycles`. A reference is judged
    against what the discovery returned, so a rule or a ruleset that it left out
    is a reference to nothing. A family that the manifest declares and that holds
    no rule is valid.

    It also reports a rule preset called `all` in a manifest, which the ruleset
    reserves for all its rules, and a root whose rule presets reach a
    root-independent ruleset, directly or through a rule preset of the config,
    at the entry of the root that reaches it; a stage that includes such a
    ruleset is not an error.

    It does no input or output, and the result is in the order of
    `sort_diagnostics` whatever the order of the tables of the config, of the
    rulesets and of the entries.

    Args:
        config: The settings, whose roots, stages, rule presets and always
            fields are read.
        discovery: What `discover` returned: the rulesets that were read and the
            faults found while reading them.

    Returns:
        The errors, each at the key where it is written: a key path of the config
        for an entry of the config, and the manifest's path followed by `#` and a
        key path for an entry or a rule preset of a manifest.
    """
    del config, discovery
    raise NotImplementedError
