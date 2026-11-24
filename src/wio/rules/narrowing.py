# SPDX-License-Identifier: Apache-2.0
"""Narrowing a listing to the rules that references name or that nothing selects."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence

    from wio.models.config import Config
    from wio.models.listing import Listing
    from wio.models.rule import LoadedRuleset
    from wio.rules.anywhere import SelectedAnywhere


def narrow(
    listing: Listing,
    references: Sequence[str],
    *,
    not_selected: bool,
    config: Config,
    rulesets: Mapping[str, LoadedRuleset],
    anywhere: SelectedAnywhere,
) -> Listing:
    """Keep the rows of a listing that references name, or that nothing selects.

    With references, a row is kept when any reference delivers its rule, as
    `expand` returns it in the config's scope, and the row's `via` holds the
    routes by which the references delivered it. With `not_selected`, a row is
    kept when no include entry of the config delivers its rule, among the rules
    that the roots of the listing can reach and the root-independent ones, or
    among every rule when the listing applies no roots; together with references,
    it keeps the rules that they deliver and no entry does. The rows stay in the
    order of the listing, the header names the references as given and is marked
    `not selected` when asked, and a listing that keeps nothing is no error. It
    does no input or output.

    Args:
        listing: The listing of a view, with every rule it considers.
        references: The references as written, in the scope of the config.
        not_selected: Whether to keep only the rules that no entry delivers.
        config: The settings, whose rulesets and roots are read.
        rulesets: The rulesets by name, as `ruleset_map` gives them.
        anywhere: The rules that some include entry delivers, which the caller
            computes once for the repository.

    Returns:
        The narrowed listing.

    Raises:
        WioError: A reference names nothing, is not in the form of a reference,
            closes a cycle or reaches an entry that cannot be expanded. It names
            the reference and says why, and no listing is returned.
    """
    del listing, references, not_selected, config, rulesets, anywhere
    raise NotImplementedError
