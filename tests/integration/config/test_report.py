# SPDX-License-Identifier: Apache-2.0
"""Tests of what a text report of `wio config check` loads in a fresh process."""

import subprocess
import sys

import pytest


@pytest.mark.slow
def test_a_text_report_never_imports_json() -> None:
    """AC-1: only `--json` loads `json`, as the rules of the command line ask."""
    # Given a program that reports a load as text in a new Python process
    program = (
        "import sys\n"
        "from wio.config.loader import Loaded\n"
        "from wio.config.report import report\n"
        "from wio.models.diagnostics import Diagnostic\n"
        "loaded = Loaded(None, (Diagnostic('note', 'a', 'm'),), frozendict())\n"
        "report(loaded, as_json=False)\n"
        "sys.stdout.write(str('json' in sys.modules))\n"
    )

    # When it runs
    done = subprocess.run(
        [sys.executable, "-c", program],
        capture_output=True,
        text=True,
        check=True,
    )

    # Then the json module is not among the modules it holds
    assert done.stdout == "False"
