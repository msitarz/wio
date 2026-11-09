# SPDX-License-Identifier: Apache-2.0
"""Tests of what a text report of `wio config check` loads in a fresh process."""

import pytest

pytestmark = pytest.mark.slow


def test_a_text_report_never_imports_json() -> None:
    """AC-1: only `--json` loads `json`, as the rules of the command line ask."""
    # Given a fresh interpreter that reports a load as text
    # When `sys.modules` is read
    # Then `json` is not in it
    pytest.skip("stub: the implementation stage writes this test")
