# SPDX-License-Identifier: Apache-2.0
"""Tests of the renderer of diagnostics that need a fresh interpreter."""

import subprocess
import sys

import pytest


@pytest.mark.slow
def test_rendering_text_does_not_import_json() -> None:
    """Importing the renderer stays light (AC-4)."""
    # Given a program that renders text in a new Python process
    program = (
        "import sys\n"
        "from wio.formats import render_text\n"
        "from wio.models.diagnostics import Diagnostic\n"
        "render_text([Diagnostic('note', 'a', 'm')])\n"
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
