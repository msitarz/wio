# SPDX-License-Identifier: Apache-2.0
"""Fakes that tests of more than one group share."""

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path


@dataclass
class FakeEnvironment:
    """A configurable environment that records variable and directory reads.

    Attributes:
        directory: The working directory.
        variables: The values of set variables.
        errors: Failures keyed by variable name, with None for the directory.
        reads: Variable names queried in order, with None for a directory query.
    """

    directory: Path
    variables: dict[str, str] = field(default_factory=dict)

    errors: dict[str | None, Exception] = field(default_factory=dict)
    reads: list[str | None] = field(default_factory=list)

    def get(self, name: str) -> str | None:
        """Read a variable of the fake.

        Args:
            name: The variable's name.

        Returns:
            Its value, or None when the fake has no such variable.

        Raises:
            Exception: The configured failure for this variable.
        """
        self._record_read(name)
        return self.variables.get(name)

    def working_directory(self) -> Path:
        """Find the fixed working directory.

        Returns:
            The directory the fake was given.

        Raises:
            Exception: The configured working-directory failure.
        """
        self._record_read(None)
        return self.directory

    def _record_read(self, name: str | None) -> None:
        """Record a query and raise any configured error.

        Args:
            name: The queried variable, or None for the working directory.

        Raises:
            Exception: The configured error for this query, if any.
        """
        self.reads.append(name)
        if name in self.errors:
            raise self.errors[name]


def value_or_raise[T](result: T | Exception) -> T:
    """Return a fake port's configured value or raise its configured error.

    Args:
        result: The value or exception prepared by the test.

    Returns:
        The value prepared by the test.

    Raises:
        Exception: The configured error when the result is an exception.
    """
    if isinstance(result, Exception):
        raise result
    return result


@dataclass
class EventSinkFake:
    """Record written events in memory without touching the log on disk.

    Attributes:
        recorded: Every event passed to `write`, in the order written.
    """

    recorded: list[object] = field(default_factory=list)

    def write(self, event: object) -> None:
        """Append the event to the in-memory list.

        Args:
            event: The event to record.
        """
        self.recorded.append(event)


@dataclass
class ReviewedCommitFake:
    """Supply a fixed reviewed commit or failure without running git.

    Attributes:
        result: The commit id, `None`, or exception to return/raise.
        calls: The `(action, stage)` pairs requested.
    """

    result: str | Exception | None = None
    calls: list[tuple[str, str]] = field(default_factory=list)

    def find(self, action: str, stage: str) -> str | None:
        """Record the call and return the configured commit id or raise.

        Args:
            action: The action of the gate.
            stage: The stage of the gate.

        Returns:
            The configured commit id or `None`.
        """
        self.calls.append((action, stage))
        return value_or_raise(self.result)
