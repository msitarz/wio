# SPDX-License-Identifier: Apache-2.0
"""Planning a new rule: its code, its place and its file, before anything is written."""

from dataclasses import dataclass
from typing import TYPE_CHECKING

from wio.errors import WioError
lazy from wio.formats import declared, encode_comment_toml
lazy from wio.rules.reading import read_rule

if TYPE_CHECKING:
    from pathlib import PurePosixPath

    from wio.models.rule import LoadedRuleset, Rule
    from wio.rules.discovery import Discovery


@dataclass(frozen=True)
class NewRule:
    """What `wio rules new` is going to write.

    It is immutable and hashable.

    Attributes:
        path: Where the file goes, relative to the repository root and written
            with `/`.
        text: The whole file: a `<!-- wio -->` block with the code, the name and
            the description when there is one, and an empty body.
        rule: The rule that reading `text` at `path` gives.
    """

    path: PurePosixPath
    text: str
    rule: Rule


def plan_rule(
    ruleset: str,
    family: str,
    name: str,
    description: str | None,
    discovery: Discovery,
) -> NewRule:
    """Plan the next rule of a family in a ruleset.

    The code is the family's letters and the number after the highest number of
    the family, so a free number below it is not reused. The number has at least
    three digits and at least as many as the highest code of the family. The file
    is `<code>-<name>.md` in the directory of the rule with the highest code of
    the family, or in the ruleset's directory when the family has none, and its
    block is written in the comment form, whatever form the other rules have,
    with a quote, a backslash and `-->` of the description escaped. The text is
    read back with `read_rule`, so the plan is a valid rule. It does no input or
    output.

    Args:
        ruleset: The canonical name of a ruleset of the discovery.
        family: The upper-case letters of a family that the ruleset's manifest
            declares.
        name: The rule's name, in the form of a rule name.
        description: The one-line description, or `None` for none.
        discovery: What the walk of the rules found; its rulesets are those that
            were read whole.

    Returns:
        The path, the text and the rule.

    Raises:
        WioError: The ruleset is not one that was read, the family is not
            declared by its manifest, the name or the description is not of the
            right form, or the ruleset already has a rule with the name. It
            names the cause, and lists the rulesets, the families or the form
            that would do.
    """
    loaded = _ruleset(ruleset, discovery)
    _check_family(loaded, family)
    _check_unused(loaded, name)
    code, directory = _next(loaded, family)
    path = directory / f"{code}-{name}.md"
    data = {"code": code, "name": name}
    if description is not None:
        data["description"] = description
    text = f"<!-- wio\n{encode_comment_toml(data)}-->\n"
    reading = read_rule(loaded.name, path, text)
    faults = [d.message for d in reading.diagnostics if d.severity == "error"]
    if faults or reading.rule is None:
        raise WioError(faults[0] if faults else f"The rule `{code}` is not valid.")
    return NewRule(path, text, reading.rule)


def _check_unused(ruleset: LoadedRuleset, name: str) -> None:
    """Check that no rule of a ruleset has a name."""
    taken = next((rule for rule in ruleset.rules if rule.name == name), None)
    if taken is not None:
        message = (
            f"The ruleset `{ruleset.name}` has a rule named `{name}`: "
            f"`{taken.qualified}`."
        )
        raise WioError(message)


def _next(ruleset: LoadedRuleset, family: str) -> tuple[str, PurePosixPath]:
    """Find the next code of a family and the directory of its file."""
    existing = ruleset.rules_of(family)
    last = existing[-1] if existing else None
    digits = len(last.code) - len(family) if last else 0
    number = (last.number if last else 0) + 1
    directory = last.path.parent if last else ruleset.path
    return f"{family}{number:0{max(3, digits)}d}", directory


def _ruleset(name: str, discovery: Discovery) -> LoadedRuleset:
    """Find the ruleset that a request names."""
    found = {ruleset.name: ruleset for ruleset in discovery.rulesets}
    if name in found:
        return found[name]
    names = declared("Rulesets", "No ruleset was read.", sorted(found))
    message = f"`{name}` is not a ruleset that was read. {names}"
    raise WioError(message)


def _check_family(ruleset: LoadedRuleset, family: str) -> None:
    """Check that a ruleset's manifest declares a family."""
    if family in ruleset.manifest.families:
        return
    names = declared(
        "Declared families",
        "No families are declared.",
        list(ruleset.manifest.families),
    )
    message = (
        f"The ruleset `{ruleset.name}` does not declare the family `{family}`. {names}"
    )
    if family.upper() in ruleset.manifest.families:
        message += (
            f" A family is written in upper case; did you mean `{family.upper()}`?"
        )
    raise WioError(message)
