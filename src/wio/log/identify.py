# SPDX-License-Identifier: Apache-2.0
"""Resolve the harness session represented by the configured environment variables.

The result supplies the session fields of an event envelope. The active
harness can be ambiguous in nested runs because both harnesses leave their
variables in the environment.
"""

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Mapping

    from wio.env.ports import Environment
    from wio.io.ports import Stdio
    from wio.models.config import Log


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

    Args:
        log: Effective harness mappings, preference and extra recorded variables.
        environment: Source for configured variables and WIO_PREFER_HARNESS.
        stdio: Streams whose standard error receives warnings about malformed
            ids and unknown names in the preference override.

    Returns:
        Session fields for the sole match or the first preferred match,
        with all matches and valid ids retained even when no harness resolves.
    """
    raise NotImplementedError
