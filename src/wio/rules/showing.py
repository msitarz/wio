# SPDX-License-Identifier: Apache-2.0
"""What `wio rules show` does and says: it prints one rule by its code."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from argparse import Namespace

    from wio.io.ports import Stdio
    from wio.models.rule import Rule
    from wio.rules import Services
    from wio.rules.discovery import Discovery


def show_rule(reference: str, discovery: Discovery) -> Rule:
    """Find the one rule that a reference names.

    The reference must be `<ruleset>.<code>` with the canonical name of a ruleset
    that the discovery read; resolving an alias is the caller's. It is judged
    from its text with `parse_reference` and `item_kind`, and a bare code is told
    from other malformed text with `parse_own_item`. It does no input or output.

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
    raise NotImplementedError


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
    raise NotImplementedError


def run_show(services: Services, args: Namespace, stdio: Stdio) -> int:
    """Run `wio rules show`: discover, resolve the alias, find and print a rule.

    It runs the discovery and refuses an error of it anywhere in the repository
    before it looks at the reference, resolves the ruleset part of the reference,
    which may be an alias, to the canonical name, finds the rule with
    `show_rule` and writes it with `render_rule`. A warning of the discovery
    refuses nothing. It writes nothing to the repository, and nothing to standard
    output for a request that is refused.

    Args:
        services: What the command reads the project through.
        args: The parsed arguments: `reference` and `json`.
        stdio: Where the rule goes.

    Returns:
        0 after the rule was printed.

    Raises:
        WioError: The reference does not name one rule. It names the cause, so
            the command exits 2.
        DiagnosticsError: The discovery reported an error anywhere.
        ConfigurationError: The config has an error.
    """
    raise NotImplementedError
