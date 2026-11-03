# SPDX-License-Identifier: Apache-2.0
"""Fixtures that every test can ask for."""

from typing import TYPE_CHECKING

import pytest

from tests.sandbox import Sandbox

if TYPE_CHECKING:
    from pathlib import Path


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
