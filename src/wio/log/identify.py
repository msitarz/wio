# SPDX-License-Identifier: Apache-2.0
"""Resolve the harness session represented by the configured environment variables.

The result supplies the session fields of an event envelope. The active
harness can be ambiguous in nested runs because both harnesses leave their
variables in the environment.
"""

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


@dataclass(frozen=True)
class SessionIdentity:
    """The harness and session fields available for an event envelope.

    Attributes:
        harness: The selected harness, if the matches resolve.
        session: The selected harness's first set session value, if selected.
        parent: The first set parent value if it differs from the session.
        matches: Matching harness names in config order.
        ids: Set values by variable name, in first occurrence order.
    """

    harness: str | None
    session: str | None
    parent: str | None
    matches: tuple[str, ...]
    ids: Mapping[str, str]


def identify(log: Log, environment: Environment, stdio: Stdio) -> SessionIdentity:
    """Identify the current harness session from the configured variables.

    Matching and field selection use presence, including empty strings.
    WIO_PREFER_HARNESS controls preference and also supplies its original
    value wherever it is configured as an id.

    Args:
        log: Effective harness mappings, preference and extra recorded variables.
        environment: Source for configured variables and WIO_PREFER_HARNESS.
        stdio: Streams whose standard error receives warnings about unknown
            names in the preference override.

    Returns:
        Session fields for the sole match or the first preferred match,
        with all matches and set ids retained even when no harness resolves.
    """
    override = environment.get(_PREFERENCE_VARIABLE)
    ids = freeze(_read_ids(log, environment, override))
    preference = _preference(log, override, stdio)
    matches = tuple(
        name
        for name, harness in log.harnesses.items()
        if any(variable in ids for variable in harness.session)
    )
    selected = _choose_harness(matches, preference)
    if selected is None:
        return SessionIdentity(None, None, None, matches, ids)
    session, parent = _session_fields(log.harnesses[selected], ids)
    return SessionIdentity(selected, session, parent, matches, ids)


def _read_ids(
    log: Log, environment: Environment, override: str | None
) -> dict[str, str]:
    """Read each configured id variable once, retaining set values in order."""
    mapped = chain.from_iterable(
        harness.session + harness.parent for harness in log.harnesses.values()
    )
    names = dict.fromkeys(chain(mapped, log.record_env_vars))
    ids: dict[str, str] = {}
    for name in names:
        value = override if name == _PREFERENCE_VARIABLE else environment.get(name)
        if value is not None:
            ids[name] = value
    return ids


def _preference(log: Log, override: str | None, stdio: Stdio) -> tuple[str, ...]:
    """Choose the preference used to resolve several matches."""
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
    """Resolve the selected harness from its matches and preference."""
    if len(matches) == 1:
        return matches[0]
    return next((name for name in preference if name in matches), None)


def _session_fields(
    harness: Harness, ids: Mapping[str, str]
) -> tuple[str | None, str | None]:
    """Derive the first set session and any distinct first set parent."""
    session = next(ids[name] for name in harness.session if name in ids)
    parent = next((ids[name] for name in harness.parent if name in ids), None)
    return session, parent if parent != session else None
