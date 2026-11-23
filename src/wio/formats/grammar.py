# SPDX-License-Identifier: Apache-2.0
"""The grammar of a reference and the forms of the names it is made of.

A reference is how the config and the rule files name a rule preset, a family or
a code: a bare name, or `<ruleset>.<item>`. This module is the one place that
says what a reference is, so `wio.config` and `wio.rules` never disagree about
it. It judges text alone: whether the ruleset or the item exists is for the
caller, which has the directories or the rule files.
"""

import re
from dataclasses import dataclass
from typing import Literal

NAME = re.compile(r"[a-z][a-z0-9_-]*")
"""The form of a ruleset name and of a rule preset name."""

FAMILY = re.compile(r"[A-Z]+")
"""The form of a family: upper-case letters."""

CODE = re.compile(r"[A-Z]+[0-9]+")
"""The form of a code: a family and digits."""

NAME_FORM = "a lowercase letter, then lowercase letters, digits, `-` and `_`"
"""The form of `NAME` in words, as a message states it."""

type ItemKind = Literal["family", "code", "rule preset"]
"""What the item of a reference is, told by its form."""


@dataclass(frozen=True)
class Bare:
    """A reference without a dot.

    Attributes:
        name: The name, which has the form of a rule preset name for
            `parse_reference`, and of a family, a code or a rule preset name for
            `parse_own_item`.
    """

    name: str


@dataclass(frozen=True)
class Qualified:
    """A reference with exactly one dot, which names an item of a ruleset.

    Attributes:
        ruleset: The ruleset's name or alias, in the form of a ruleset name.
        item: A family, a code or a rule preset, in the form of one of them.
    """

    ruleset: str
    item: str


@dataclass(frozen=True)
class Malformed:
    """A reference of the wrong form.

    Attributes:
        message: The sentence that says which part is wrong and the form that
            part should have.
    """

    message: str


type Reference = Bare | Qualified | Malformed
"""What a reference is, judged from its text alone."""


def parse_reference(text: str) -> Reference:
    """Judge the form of a reference of the config from its text.

    Args:
        text: The reference as the config writes it.

    Returns:
        `Bare` for a name without a dot in the form of a rule preset name, and
        `Qualified` for `<ruleset>.<item>` whose parts have their forms. Any
        other text is `Malformed`, a bare upper-case name included, with the
        sentence that says which part is wrong and the form it should have: the
        whole text of a bare name, more than one dot, the ruleset part, or the
        item.
    """
    if "." not in text:
        if NAME.fullmatch(text):
            return Bare(text)
        message = f"`{text}` is not a rule preset name; a bare name is a rule preset"
        return Malformed(f"{message} of the config, {NAME_FORM}.")
    if text.count(".") > 1:
        message = "has more than one dot; a reference is a bare name or"
        return Malformed(f"`{text}` {message} `<ruleset>.<item>`.")
    ruleset, item = text.split(".")
    if not NAME.fullmatch(ruleset):
        message = f"the ruleset part `{ruleset}` of `{text}` is not a ruleset name; "
        return Malformed(f"{message}a ruleset name is {NAME_FORM}.")
    if item_kind(item) is None:
        message = f"the item `{item}` of `{text}` is not a family (upper-case "
        return Malformed(
            f"{message}letters), a code (a family and digits) or a rule preset "
            f"({NAME_FORM})."
        )
    return Qualified(ruleset, item)


def parse_own_item(text: str) -> Reference:
    """Read an entry of a manifest, which names an item of its own ruleset.

    Args:
        text: The entry as the manifest writes it.

    Returns:
        `Bare` for a family, a code or a rule preset name without a dot, which
        is how a manifest names its own items; `Qualified` for a well-formed
        `<ruleset>.<item>`, which the caller reports because a manifest names
        only its own items; and `Malformed`, with its sentence, for any other
        text.
    """
    if "." in text:
        return parse_reference(text)
    if item_kind(text) is not None:
        return Bare(text)
    message = f"`{text}` is not a family (upper-case letters), a code (a family and "
    return Malformed(f"{message}digits) or a rule preset name ({NAME_FORM}).")


def item_kind(item: str) -> ItemKind | None:
    """Tell what kind of name an item is.

    Args:
        item: The part of a reference after the dot, or an entry of a manifest.

    Returns:
        `family`, `code` or `rule preset`, in that order of precedence, so a
        text that has the form of a code is a code; or `None` when it has no
        such form.
    """
    if FAMILY.fullmatch(item):
        return "family"
    if CODE.fullmatch(item):
        return "code"
    return "rule preset" if NAME.fullmatch(item) else None
