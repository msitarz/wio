# SPDX-License-Identifier: Apache-2.0
"""A fixture command package that imports its implementation lazily."""

from tests.unit.cli.fixtures.spec import describe
lazy from tests.unit.cli.fixtures.light import impl

__all__ = ["describe", "impl"]
