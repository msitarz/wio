# SPDX-License-Identifier: Apache-2.0
"""What `wio rules new` does and says: it writes one rule and tells what selects it."""

from typing import TYPE_CHECKING

from wio.errors import WioError
lazy from wio.formats import encode_json
lazy from wio.rules.anywhere import selected_anywhere
lazy from wio.rules.discovery import discover, refuse_on_errors
lazy from wio.rules.inputs import (
    build_rule_catalog,
    chain_labels,
    chain_text,
    layer_label,
    resolve_ruleset,
    ruleset_map,
)
lazy from wio.rules.planning import plan_rule

if TYPE_CHECKING:
    from argparse import Namespace

    from wio.io.ports import Stdio
    from wio.rules import Services
    from wio.rules.anywhere import Origin
    from wio.rules.planning import NewRule


def render_created(new: NewRule, origins: tuple[Origin, ...], *, as_json: bool) -> str:
    """Write what `wio rules new` says about the rule it created.

    The text is `created <ruleset>.<code> <name>`, the line `file: <path>`, and
    then one `selected: <chain>` line for each route of each origin, in the
    chain form that `chain_text` writes and the `wio rules list --explain` of
    the same rule shows, or `selected: no, nothing selects it yet` when there is
    no origin. The JSON is one object on one line with `code`, which is the
    qualified code, `name`, `path`, `selected` and `origins`, the chains as arrays
    of labels without the code. It reads and writes nothing.

    Args:
        new: The rule that was written.
        origins: The include entries of the config that deliver it, in the order
            of `SelectedAnywhere.selected`.
        as_json: Whether to write the object instead of the text.

    Returns:
        The text for standard output, ending in a newline.
    """
    chains = [
        chain_labels(layer_label(origin.layer, origin.name), route)
        for origin in origins
        for route in origin.routes
    ]
    if as_json:
        return encode_json(_as_object(new, chains)) + "\n"
    code = new.rule.qualified
    lines = [f"created {code} {new.rule.name}", f"file: {new.path.as_posix()}"]
    lines += [f"selected: {chain_text(code, chain)}" for chain in chains]
    if not chains:
        lines.append("selected: no, nothing selects it yet")
    return "".join(f"{line}\n" for line in lines)


def _as_object(new: NewRule, chains: list[tuple[str, ...]]) -> dict[str, object]:
    """Describe the new rule as plain data for JSON."""
    return {
        "code": new.rule.qualified,
        "name": new.rule.name,
        "path": new.path.as_posix(),
        "selected": bool(chains),
        "origins": [list(chain) for chain in chains],
    }


def run_new(services: Services, args: Namespace, stdio: Stdio) -> int:
    """Run `wio rules new`: plan, check, write, read back and report one rule.

    Raises:
        WioError: The request cannot be met, or the file exists. It names the
            cause, so the command exits 2.
        DiagnosticsError: The discovery reported an error anywhere.
        ConfigurationError: The config has an error.
    """
    config = services.settings.load()
    root = services.repository.root()
    discovery = discover(root, services.files)
    refuse_on_errors(discovery)
    catalog = build_rule_catalog(config, ruleset_map(discovery))
    canonical = resolve_ruleset(args.ruleset, catalog) or args.ruleset
    new = plan_rule(canonical, args.family, args.name, args.description, discovery)
    target = root.joinpath(*new.path.parts)
    if services.files.exists(target) or services.files.is_symlink(target):
        message = f"The file `{new.path.as_posix()}` exists and is not overwritten."
        raise WioError(message)
    services.files.write_text(target, new.text)
    again = ruleset_map(discover(root, services.files))
    written = again[canonical].get(new.rule.code)
    if written is None:
        message = f"The new rule `{new.rule.qualified}` was written but not read back."
        raise WioError(message)
    anywhere = selected_anywhere(config, again)
    origins = anywhere.selected.get(written, ())
    stdio.stdout.write(render_created(new, origins, as_json=args.json))
    return 0
