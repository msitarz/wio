# SPDX-License-Identifier: Apache-2.0
"""The decision of every rule: included with its roots, or out with its reason.

The layers say which rules are selected, and this module says where each applies:
a selected rule applies when its ruleset is root-independent or reached by a
selected root. One `select` serves every view of a listing and every consumer of
a selection. It reads no file.
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Mapping

    from wio.models.config import Config
    from wio.models.rule import LoadedRuleset
    from wio.models.rules import Selection


def select(
    roots: tuple[str, ...] | None,
    stage: str | None,
    config: Config,
    rulesets: Mapping[str, LoadedRuleset],
) -> Selection:
    """Decide every rule of every ruleset for the roots and the stage.

    It applies the layers with `apply_layers` and then decides each rule. The
    roots are applied when `roots` is not `None`, an empty tuple included; then
    a selected rule is included when its ruleset is root-independent or reached
    by a selected root, with those roots in the order of their names, and is out
    as `cut-by-roots` otherwise. When the roots are not applied, no rule is cut,
    and a rule that is not root-independent lists the roots of the config that
    reach its ruleset, in the order of their names. A rule of a root-independent
    ruleset applies to every root, so it has no roots and `root_independent`
    true, whether or not a root also reaches its ruleset. A rule that the layers
    did not select is out with the reason of the last layer that removed it:
    `excluded` for a root or the stage, including the exclude of a rule preset
    that an entry of that layer names, `vetoed` for the always excludes, and
    `not-selected` when no layer touched it. The exclude of a rule preset inside
    an entry of the always includes took nothing out of the set, so it gives no
    reason: a rule that only it removed is `not-selected`. A rule that a layer
    removed is never reported as cut by the roots.

    It does no input or output, and the result does not depend on the order of
    the tables of the config, of the entries of its lists or of `roots`.

    Args:
        roots: The roots to apply, which `None` leaves unapplied.
        stage: The stage to apply, or `None` for no stage.
        config: The settings: the roots, the stages, the always fields and what
            each ruleset is set to.
        rulesets: Every ruleset of the repository by its canonical name, in the
            form that `ruleset_map` gives.

    Returns:
        One decision for each rule of every ruleset, in the order of C-2 of
        `wio rules`.

    Raises:
        KeyError: A name of `roots` or `stage` is not in the config, as
            `apply_layers` raises it.
    """
    del config
    msg = f"select for {roots} and {stage} over {len(rulesets)} is declared"
    raise NotImplementedError(msg)
