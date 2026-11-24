# SPDX-License-Identifier: Apache-2.0
"""What `wio rules new` does and says: it writes one rule and tells what selects it."""

from typing import TYPE_CHECKING

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
    del new, origins, as_json
    raise NotImplementedError


def run_new(services: Services, args: Namespace, stdio: Stdio) -> int:
    """Run `wio rules new`: plan, check, write, read back and report one rule.

    It runs the discovery and refuses an error of it anywhere in the repository,
    resolves an alias to the canonical name of the ruleset, plans the rule with
    `plan_rule`, and refuses when the file exists, because writing would
    overwrite it, whether or not that file is a rule. Only then does it write the
    file, run the discovery again to read it back, and ask `selected_anywhere`
    whether any entry of the config delivers the rule, whatever the roots. A
    warning of the discovery refuses nothing. Nothing is written for a request
    that is refused, and exactly one file is written otherwise.

    Args:
        services: What the command reads and writes the project through.
        args: The parsed arguments: `ruleset`, `family`, `name`, `description`
            and `json`.
        stdio: Where the result goes.

    Returns:
        0 after the rule was created.

    Raises:
        WioError: The request cannot be met, or the file exists. It names the
            cause, so the command exits 2.
        DiagnosticsError: The discovery reported an error anywhere.
        ConfigurationError: The config has an error.
    """
    del services, args, stdio
    raise NotImplementedError
