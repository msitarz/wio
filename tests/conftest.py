# SPDX-License-Identifier: Apache-2.0
"""Fixtures that every test can ask for, and the group each test belongs to."""

from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from tests.sandbox import Sandbox

if TYPE_CHECKING:
    from collections.abc import Sequence

# One group per directory under `tests/`. The marker of a group is its name.
GROUPS = ("acceptance", "integration", "packaging", "scripts", "tooling", "unit")

_TESTS = Path(__file__).parent


def pytest_collection_modifyitems(items: Sequence[pytest.Item]) -> None:
    """Mark every test with the group of the directory it lives in.

    The group is the first directory under `tests/`, so `pytest -m integration`
    selects the tests of `tests/integration` and nothing else.

    Args:
        items: The collected tests; the marks are added in place.

    Raises:
        pytest.UsageError: If a test is in no group, or carries the marker of a
            group other than its own.
    """
    for item in items:
        if _TESTS not in item.path.parents:
            continue
        group = item.path.relative_to(_TESTS).parts[0]
        if group not in GROUPS:
            message = f"{item.nodeid} is in no group of tests; the groups are {GROUPS}"
            raise pytest.UsageError(message)
        item.add_marker(group)
        marked = {mark.name for mark in item.iter_markers()} & set(GROUPS)
        if marked != {group}:
            message = f"{item.nodeid} is in group {group} and marked {sorted(marked)}"
            raise pytest.UsageError(message)


@pytest.fixture
def sandbox(tmp_path: Path) -> Sandbox:
    """A sandbox under the test's own temporary directory.

    It only holds a directory and an environment. A test whose code runs git
    without being given the environment makes them the process's with
    `tests.support.enter`.

    Args:
        tmp_path: The test's own temporary directory.

    Returns:
        An empty repository directory and a private environment.
    """
    return Sandbox.under(tmp_path)
