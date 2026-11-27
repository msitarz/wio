# SPDX-License-Identifier: Apache-2.0
"""What `wio rules show` does and says: it prints one rule by its code."""

from typing import TYPE_CHECKING

from wio.errors import WioError
lazy from wio.formats import (
    Bare,
    Block,
    Malformed,
    Qualified,
    and_list,
    encode_json,
    item_kind,
    parse_own_item,
    parse_reference,
    quoted,
    render_blocks,
)
lazy from wio.rules.discovery import discover, refuse_on_errors
lazy from wio.rules.inputs import build_rule_catalog, resolve_ruleset, ruleset_map

if TYPE_CHECKING:
    from argparse import Namespace

    from wio.io.ports import Stdio
    from wio.models.rule import LoadedRuleset, Rule
    from wio.rules import Services
    from wio.rules.discovery import Discovery
    from wio.rules.inputs import RuleCatalog


def show_rule(reference: str, discovery: Discovery) -> Rule:
    """Find the one rule that a reference names.

    The reference must be `<ruleset>.<code>` with the canonical name of a ruleset
    that the discovery read; resolving an alias is the caller's, so an alias is
    an unknown ruleset here. It is judged from its text with `parse_reference`
    and `item_kind`, and a bare code is told from other malformed text with
    `parse_own_item`. It does no input or output. The refusal of an unknown
    ruleset is its own: it says that no ruleset is the name and lists the
    rulesets that were read.

    Args:
        reference: The reference as the command resolved it.
        discovery: What the walk of the rules found.

    Returns:
        The rule with that ruleset and code.

    Raises:
        WioError: The reference is a family, a rule preset, `all`, a bare code,
            malformed, an unknown ruleset, an unknown rule or in the form of a
            rule preset name and not of a code. It says which, and names the
            rulesets or the codes that would do.
    """
    match parse_reference(reference):
        case Qualified(ruleset, item):
            return _find(ruleset, item, discovery)
        case _:
            raise WioError(_unqualified(reference))


def render_rule(rule: Rule, *, as_json: bool) -> str:
    """Write what `wio rules show` prints for a rule.

    The text is the block of the qualified code and the name with the
    description when there is one and the line `file: <path>`, rendered with
    `render_blocks`; then, when the body is not empty, a blank line and the body
    as the rule holds it, its line endings untouched; then one line feed. The
    JSON is one object on one line with `code`, which is qualified, `name`,
    `description`, which is `null` for none, `summary`, `body` and `path`, in that
    order, and one line feed. It reads and writes nothing.

    Args:
        rule: The rule to show.
        as_json: Whether to write the object instead of the text.

    Returns:
        The text for standard output.
    """
    if as_json:
        return encode_json(_as_object(rule)) + "\n"
    details = [f"file: {rule.path.as_posix()}"]
    if rule.description:
        details.insert(0, rule.description)
    text = render_blocks([Block(0, rule.qualified, rule.name, None, tuple(details))])
    return f"{text}\n{rule.body}\n" if rule.body else text


def run_show(services: Services, args: Namespace, stdio: Stdio) -> int:
    """Run `wio rules show`: discover, resolve the alias, find and print a rule.

    Raises:
        WioError: The reference does not name one rule. It names the cause, so
            the command exits 2.
        DiagnosticsError: The discovery reported an error anywhere.
        ConfigurationError: The config has an error.
    """
    config = services.settings.load()
    discovery = discover(services.repository.root(), services.files)
    refuse_on_errors(discovery)
    catalog = build_rule_catalog(config, ruleset_map(discovery))
    rule = show_rule(_canonical(args.reference, catalog), discovery)
    stdio.stdout.write(render_rule(rule, as_json=args.json))
    return 0


def _canonical(reference: str, catalog: RuleCatalog) -> str:
    """Replace an alias in a reference with the ruleset's canonical name."""
    match parse_reference(reference):
        case Qualified(ruleset, item) if found := resolve_ruleset(ruleset, catalog):
            return f"{found}.{item}"
        case _:
            return reference


def _as_object(rule: Rule) -> dict[str, object]:
    """Describe a rule as plain data for JSON."""
    return {
        "code": rule.qualified,
        "name": rule.name,
        "description": rule.description,
        "summary": rule.summary,
        "body": rule.body,
        "path": rule.path.as_posix(),
    }


def _unqualified(reference: str) -> str:
    """Say why a reference without a usable ruleset and item is refused."""
    match parse_own_item(reference):
        case Bare(name):
            return f"`{name}` has no ruleset; `show` takes `<ruleset>.<code>`."
        case Malformed(message):
            return f"`{reference}` is not a reference. {message}"
        case _:
            return f"`{reference}` is not a reference."


def _find(ruleset: str, item: str, discovery: Discovery) -> Rule:
    """Find a rule once the form of the reference is known to be qualified."""
    loaded = next((r for r in discovery.rulesets if r.name == ruleset), None)
    _require_code(ruleset, item, loaded)
    found = _ruleset(ruleset, discovery, loaded)
    return found.get(item) or _missing(found, item)


def _missing(ruleset: LoadedRuleset, item: str) -> Rule:
    """Refuse a code that a ruleset does not hold."""
    codes = [f"`{r.code}`" for r in ruleset.rules]
    held = and_list(codes) if codes else "no rule"
    message = f"`{ruleset.name}` holds {held} and not `{item}`."
    raise WioError(message)


def _ruleset(
    name: str, discovery: Discovery, loaded: LoadedRuleset | None
) -> LoadedRuleset:
    """Require the ruleset that a reference names."""
    if loaded is not None:
        return loaded
    names = quoted([r.name for r in discovery.rulesets])
    message = f"No ruleset is `{name}`."
    if names:
        message = f"{message} Rulesets: {names}."
    raise WioError(message)


def _require_code(ruleset: str, item: str, loaded: LoadedRuleset | None) -> None:
    """Refuse an item that does not have the form of a code."""
    text = f"`{ruleset}.{item}`"
    match item_kind(item):
        case "family":
            message = f"{text} is a family and `show` takes a rule's code."
            raise WioError(message)
        case "rule preset" if item == "all" or _is_preset(loaded, item):
            message = f"{text} is a rule preset and `show` takes a rule's code."
            raise WioError(message)
        case "rule preset":
            message = "has the form of a rule preset name and not of a code"
            message = f"{text} {message}, so `show` does not take it."
            raise WioError(message)


def _is_preset(loaded: LoadedRuleset | None, item: str) -> bool:
    """Tell whether a ruleset declares a rule preset."""
    return loaded is not None and item in loaded.manifest.rule_presets
