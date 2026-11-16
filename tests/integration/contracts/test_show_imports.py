# SPDX-License-Identifier: Apache-2.0
"""Test stub of what `wio contracts show` imports, in a fresh interpreter.

The stub is the scenario of the Work's acceptance criteria. The implementation
stage replaces its body with the scenario and its fixture.
"""

import pytest

pytestmark = pytest.mark.skip(
    reason="architecture stub: the implementation stage fills it"
)


@pytest.mark.slow
def test_show_without_json_loads_neither_json_nor_tomlkit() -> None:
    """AC-6: a run without `--json` leaves both unloaded."""
    # Given a new Python process and a repository with the Works of AC-1
    # When `main(["contracts", "show", "k3m9xq"], stdio)` of `wio.cli` runs and
    # `sys.modules` is read
    # Then neither `json` nor `tomlkit` is there
    raise NotImplementedError
