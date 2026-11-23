# SPDX-License-Identifier: Apache-2.0
"""The reader of a rule file, which turns the text of one file into a `Rule`.

It does no input or output and reads only the text it is given, so the walking
of a directory and the judging of a rule against its ruleset are for the caller.
"""

import re
from dataclasses import dataclass
from typing import TYPE_CHECKING

from wio.formats.errors import MetadataBlockError
from wio.formats.wording import quoted
from wio.models.diagnostics import Diagnostic, order_diagnostics
from wio.models.rule import Rule
lazy from wio.formats import CODE, closest_key, read_metadata_block

if TYPE_CHECKING:
    from pathlib import PurePosixPath

    from wio.models.block import MetadataBlock

RULE_NAME_FORM = "lower-case words of letters and digits joined by single hyphens"
"""The form of a rule's name in words, as a message states it."""

RULE_NAME = re.compile(r"[a-z][a-z0-9]*(?:-[a-z0-9]+)*")
"""The form of a rule's name: words of letters and digits, hyphens between."""

_KEYS = ("code", "name", "description")
"""The keys a rule file's metadata block knows."""


@dataclass(frozen=True)
class RuleReading:
    """What reading one rule file gave.

    Attributes:
        rule: The rule, or `None` when the file is not a rule or has an error.
        diagnostics: Every error and warning of the file, each with its place,
            in the order a check of files prints them; empty for a file that is
            not marked.
    """

    rule: Rule | None
    diagnostics: tuple[Diagnostic, ...]


def read_rule(ruleset: str, path: PurePosixPath, text: str) -> RuleReading:
    """Read the text of a rule file into a rule.

    Reuses the code form `CODE` of `wio.formats.grammar`, the block reader
    `read_metadata_block` and `closest_key` of `wio.formats`.

    Args:
        ruleset: The name of the ruleset whose directory holds the file.
        path: The path of the file relative to the repository root, which is the
            place of every diagnostic, followed by `:<line>` when a fault has a
            line.
        text: The text of the file, decoded as UTF-8.

    Returns:
        The rule and no error for a marked file whose `code` and `name` have
        their forms, in either block form, with a warning for each key that the
        block does not know and the known key it is close to. Every fault of the
        file is reported together as an error and leaves the rule out. A text
        with no metadata block on its first line, or with `+++` front matter
        that has no `wio` key, is not a rule and gives no diagnostic.
    """
    where = str(path)
    try:
        block = read_metadata_block(text)
    except MetadataBlockError as error:
        fault = Diagnostic("error", f"{where}:{error.line}", error.message)
        return RuleReading(None, (fault,))
    if block is None:
        return RuleReading(None, ())
    found = [*_key_faults(block.data, where), *_unknown_keys(block.data, where)]
    diagnostics = order_diagnostics(found)
    if any(d.severity == "error" for d in diagnostics):
        return RuleReading(None, diagnostics)
    return RuleReading(_rule(ruleset, path, block), diagnostics)


def _rule(ruleset: str, path: PurePosixPath, block: MetadataBlock) -> Rule:
    """Build the rule of a block whose keys have no fault.

    Args:
        ruleset: The name of the ruleset.
        path: The path of the file.
        block: The block, whose `code` and `name` are valid strings and whose
            `description`, when present, is a valid string.

    Returns:
        The rule, with its body cut from the text after the block.
    """
    body, line = _cut_body(block.body, block.body_start_line)
    description = block.data.get("description")
    return Rule(
        ruleset=ruleset,
        code=str(block.data["code"]),
        name=str(block.data["name"]),
        description=None if description is None else str(description),
        summary=_summary(body),
        body=body,
        body_line=line,
        path=path,
    )


def _cut_body(text: str, start: int) -> tuple[str, int]:
    """Cut the body from the text after the block.

    Args:
        text: The text after the block, from its start line on.
        start: The line of the file on which `text` starts.

    Returns:
        The text without its leading and trailing blank lines and without a
        final line ending, and the line on which it starts; `start` for an empty
        body. A blank line is empty or holds only whitespace.
    """
    lines = text.split("\n")
    first = next((i for i, line in enumerate(lines) if line.strip()), None)
    if first is None:
        return "", start
    last = max(i for i, line in enumerate(lines) if line.strip())
    kept = lines[first : last + 1]
    kept[-1] = kept[-1].removesuffix("\r")
    return "\n".join(kept), start + first


def _summary(body: str) -> str:
    """Join the lines of the first paragraph of a body.

    Args:
        body: The body, which starts with a line that is not blank.

    Returns:
        The lines before the first blank line, each stripped, joined with single
        spaces; empty for an empty body.
    """
    lines: list[str] = []
    for line in body.split("\n"):
        if not line.strip():
            break
        lines.append(line.strip())
    return " ".join(lines)


def _key_faults(data: dict[str, object], where: str) -> list[Diagnostic]:
    """Judge the `code`, the `name` and the `description` of a block.

    Args:
        data: The decoded block.
        where: The place of the file.

    Returns:
        An error for each key that is missing or of the wrong form or type,
        at the file's path.
    """
    faults = [
        _code_fault(data.get("code"), "code" in data),
        _name_fault(data.get("name"), "name" in data),
        _description_fault(data.get("description")),
    ]
    return [Diagnostic("error", where, text) for text in faults if text]


def _code_fault(value: object, present: bool) -> str | None:  # noqa: FBT001
    """Judge the `code` key.

    Args:
        value: Its value.
        present: Whether the block has the key.

    Returns:
        The problem, or `None`.
    """
    if not present:
        return "missing key `code`; a code is upper-case letters and digits."
    if not isinstance(value, str):
        return f"`code` must be a string, received {value!r}."
    if CODE.fullmatch(value):
        return None
    message = f"the `code` `{value}` is not a code; "
    return f"{message}a code is upper-case letters, then digits."


def _name_fault(value: object, present: bool) -> str | None:  # noqa: FBT001
    """Judge the `name` key.

    Args:
        value: Its value.
        present: Whether the block has the key.

    Returns:
        The problem, or `None`.
    """
    if not present:
        return f"missing key `name`; a name is {RULE_NAME_FORM}."
    if not isinstance(value, str):
        return f"`name` must be a string, received {value!r}."
    if RULE_NAME.fullmatch(value):
        return None
    return f"the `name` `{value}` is not a rule name; a name is {RULE_NAME_FORM}."


def _description_fault(value: object) -> str | None:
    """Judge the optional `description` key.

    Args:
        value: Its value, or `None` when the block has no such key.

    Returns:
        The problem, or `None`.
    """
    if value is None:
        return None
    if not isinstance(value, str):
        return f"`description` must be a string, received {value!r}."
    if value.strip() and "\n" not in value and "\r" not in value:
        return None
    return "`description` must be one line that is not blank."


def _unknown_keys(data: dict[str, object], where: str) -> list[Diagnostic]:
    """Warn of each key that the block does not know.

    Args:
        data: The decoded block.
        where: The place of the file.

    Returns:
        A warning at the file's path for each unknown key, naming the known key
        it is close to when there is one.
    """
    warnings = []
    for key in data:
        if key in _KEYS:
            continue
        message = f"unknown key `{key}`. Valid keys: {quoted(_KEYS)}."
        close = closest_key(key, _KEYS)
        if close:
            message += f" Did you mean `{close}`?"
        warnings.append(Diagnostic("warning", where, message))
    return warnings
