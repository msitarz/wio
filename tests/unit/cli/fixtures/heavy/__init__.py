# SPDX-License-Identifier: Apache-2.0
"""A fixture command package that imports its implementation eagerly."""

from tests.unit.cli.fixtures.heavy import impl
from tests.unit.cli.fixtures.spec import describe

__all__ = ["describe", "impl"]
