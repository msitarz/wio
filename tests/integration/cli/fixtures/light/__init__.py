# SPDX-License-Identifier: Apache-2.0
"""A fixture command package that imports its implementation lazily."""

from tests.integration.cli.fixtures.spec import describe
lazy from tests.integration.cli.fixtures.light import impl

__all__ = ["describe", "impl"]
