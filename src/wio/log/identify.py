# SPDX-License-Identifier: Apache-2.0
"""Resolve the harness session represented by the configured environment variables.

The result supplies the session fields of an event envelope. The active
harness can be ambiguous in nested runs because both harnesses leave their
variables in the environment.
"""

import re
from dataclasses import dataclass
from itertools import chain
from typing import TYPE_CHECKING

from wio.models.frozen import freeze

if TYPE_CHECKING:
    from collections.abc import Mapping

    from wio.env.ports import Environment
    from wio.io.ports import Stdio
    from wio.models.config import Harness, Log


_PREFERENCE_VARIABLE = "WIO_PREFER_HARNESS"
_ID = re.compile(r"[A-Za-z0-9._:-]{1,128}")


@dataclass(frozen=True)
class SessionIdentity:
    """The harness and session fields available for an event envelope.

    Attributes:
        harness: The selected harness, including when its session is unknown.
        session: The selected harness's valid session id, if available.
        parent: The first valid parent id when the session is known and differs.
        matches: Matching harness names in config order.
        ids: Valid values by variable name, in first occurrence order.
    """

    harness: str | None
    session: str | None
    parent: str | None
    matches: tuple[str, ...]
    ids: Mapping[str, str]


def identify(log: Log, environment: Environment, stdio: Stdio) -> SessionIdentity:
    """Identify the current harness session from the configured variables.

    WIO_PREFER_HARNESS supplies preference alone, even if a harness or
    the extra recorded variables name it. It cannot supply a match,
    session, parent or recorded id.

    Args:
        log: Effective harness mappings, preference and extra recorded variables.
        environment: Source for configured variables and WIO_PREFER_HARNESS.
        stdio: Streams whose standard error receives warnings about malformed
            ids and unknown names in the preference override.

    Returns:
        Session fields for the sole match or the first preferred match,
        with all matches and valid ids retained even when no harness resolves.
    """
    values = _read_ids(log, environment)
    ids = freeze(_valid_ids(values, stdio))
    preference = _preference(log, environment.get(_PREFERENCE_VARIABLE), stdio)
    matches = tuple(
        name
        for name, harness in log.harnesses.items()
        if any(variable in values for variable in harness.session)
    )
    selected = _choose_harness(matches, preference)
    if selected is None:
        return SessionIdentity(None, None, None, matches, ids)
    session, parent = _session_fields(log.harnesses[selected], values, ids)
    return SessionIdentity(selected, session, parent, matches, ids)


def _read_ids(log: Log, environment: Environment) -> dict[str, str]:
    """Read each configured id variable once, retaining set values in order.

    Args:
        log: The mappings and extra variable names in config order.
        environment: The source of variable values.

    Returns:
        The nonempty values in first occurrence order, including malformed
        values for matching. The reserved preference variable is excluded.
    """
    mapped = chain.from_iterable(
        harness.session + harness.parent for harness in log.harnesses.values()
    )
    names = dict.fromkeys(chain(mapped, log.record_env_vars))
    return {
        name: value
        for name in names
        if name != _PREFERENCE_VARIABLE and (value := environment.get(name))
    }


def _valid_ids(values: Mapping[str, str], stdio: Stdio) -> dict[str, str]:
    """Keep well-shaped ids in first occurrence order.

    Args:
        values: Set values by distinct variable name.
        stdio: The streams used to warn once per malformed value.

    Returns:
        Only values of one to 128 ASCII letters, digits or characters in
        `._:-`. Warnings name malformed variables and omit their values.
    """
    ids: dict[str, str] = {}
    for name, value in values.items():
        if _ID.fullmatch(value):
            ids[name] = value
        else:
            stdio.stderr.write(f"warning: {name} has an invalid id\n")
    return ids


def _preference(log: Log, override: str | None, stdio: Stdio) -> tuple[str, ...]:
    """Choose the preference used to resolve several matches.

    Args:
        log: Config preference and known harness names.
        override: The raw value of the preference variable.
        stdio: The streams used to warn about unknown names.

    Returns:
        The config preference for an absent or empty override, an empty
        preference for `none`, or the override names in listed order.
    """
    value = (override or "").strip()
    if value == "none":
        return ()
    names = tuple(filter(None, map(str.strip, value.split(","))))
    if not names:
        return log.prefer_harness
    known: list[str] = []
    for name in names:
        if name in log.harnesses:
            known.append(name)
        else:
            stdio.stderr.write(
                f"warning: {_PREFERENCE_VARIABLE} names unknown harness {name!r}\n"
            )
    return tuple(known)


def _choose_harness(
    matches: tuple[str, ...], preference: tuple[str, ...]
) -> str | None:
    """Resolve the selected harness from its matches and preference.

    Args:
        matches: The matching harness names in config order.
        preference: Harness names in preference order.

    Returns:
        The sole match, the first preferred match, or None if unresolved.
    """
    if len(matches) == 1:
        return matches[0]
    return next((name for name in preference if name in matches), None)


def _session_fields(
    harness: Harness, values: Mapping[str, str], ids: Mapping[str, str]
) -> tuple[str | None, str | None]:
    """Derive the session and any distinct parent of the selected harness.

    Args:
        harness: Ordered session and parent variable names.
        values: All set id values by variable name.
        ids: The validated subset of those values.

    Returns:
        The valid id of the first set session variable, or two absent fields
        when it is malformed. The first valid parent id is returned when it
        differs from the session.
    """
    session = next((ids.get(name) for name in harness.session if name in values), None)
    if session is None:
        return None, None
    parent = next((ids[name] for name in harness.parent if name in ids), None)
    return session, parent if parent != session else None
