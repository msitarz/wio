# SPDX-License-Identifier: Apache-2.0
"""A fixture command package that imports its implementation eagerly."""

from tests.integration.cli.fixtures.heavy import impl
from tests.integration.cli.fixtures.spec import describe

__all__ = ["describe", "impl"]
