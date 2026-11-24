# SPDX-License-Identifier: Apache-2.0
"""Helpers that the scenarios of `wio rules list` share."""

import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from tests.acceptance.dsl.results import Output
    from tests.acceptance.dsl.wio import Wio

BASE = "rules/base"
RULES = ".agents/wio/rules"
WORK = "k3m9xq"
BARE = "n5p7qr"


def rule(code: str, name: str, body: str = "Body.\n", extra: str = "") -> bytes:
    """Build a rule file.

    Args:
        code: The rule's code.
        name: The rule's name.
        body: What follows the block and a blank line.
        extra: Lines for the block after the name.

    Returns:
        The bytes of the file.
    """
    block = f'<!-- wio\ncode = "{code}"\nname = "{name}"\n{extra}-->\n\n'
    return (block + body).encode()


def ruleset(wio: Wio, name: str, manifest: str, rules: dict[str, str]) -> None:
    """Write a ruleset.

    Args:
        wio: The facade.
        name: The ruleset's name.
        manifest: The text of its `ruleset.toml`.
        rules: Each rule's code and name.
    """
    wio.put(f"{RULES}/{name}/ruleset.toml", manifest.encode())
    for code, rule_name in rules.items():
        wio.put(f"{RULES}/{name}/{code}-{rule_name}.md", rule(code, rule_name))


def work(wio: Wio, work_id: str, roots: str) -> None:
    """Write a Work with the given roots.

    Args:
        wio: The facade.
        work_id: The Work's id.
        roots: The `roots` line of its metadata, or an empty string.
    """
    block = f'<!-- wio\nid = "{work_id}"\n{roots}-->\n\n# A Work\n'
    wio.put(f".agents/wio/works/{work_id}/README.md", block.encode())


def shown(output: Output) -> dict[str, str | None]:
    """Read the rules of the text and their `roots:` lines.

    Args:
        output: The result of `wio rules list`.

    Returns:
        Each qualified code with the value of its `roots:` line, or `None`.
    """
    found: dict[str, str | None] = {}
    for line in output.stdout.splitlines():
        if re.match(r"\w+\.[A-Z]+\d+ ", line):
            code = line.split()[0]
            found[code] = None
        elif (match := re.match(r"\s+roots: (.*)", line)) and found:
            found[list(found)[-1]] = match[1]
    return found


def header(output: Output) -> list[str]:
    """Read the header lines of the text.

    Args:
        output: The result of `wio rules list`.

    Returns:
        The lines before the first blank line.
    """
    return output.stdout.split("\n\n")[0].splitlines()
