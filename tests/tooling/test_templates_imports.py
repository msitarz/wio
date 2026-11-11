# SPDX-License-Identifier: Apache-2.0
"""Tests of the import direction between `wio.templates` and `wio.contracts`."""

import ast
import subprocess
import sys
from pathlib import Path

import pytest

from tests.tooling.imports import modules_imported

ROOT = Path(__file__).resolve().parents[2]
TEMPLATES = ROOT / "src" / "wio" / "templates"


def _imports_contracts(path: Path) -> bool:
    """Tell whether a source file imports `wio.contracts`, in any form.

    Args:
        path: A Python source file.

    Returns:
        Whether a syntax node of it imports `wio.contracts` or one of its modules.
    """
    tree = ast.parse(path.read_text(encoding="utf-8"))
    return any(
        name == "wio.contracts" or name.startswith("wio.contracts.")
        for node in ast.walk(tree)
        for name in modules_imported(node)
    )


@pytest.mark.slow
def test_wio_templates_imports_nothing_of_wio_contracts() -> None:
    """AC-7: `src/wio/templates` imports nothing of `wio.contracts`."""
    # Given the sources of `src/wio/templates`
    sources = sorted(TEMPLATES.rglob("*.py"))

    # When the imports of its modules are read from their syntax trees, and
    # `tach check` runs
    importers = [path.name for path in sources if _imports_contracts(path)]
    tach = subprocess.run(
        [sys.executable, "-m", "tach", "check"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    # Then the trees show no import of `wio.contracts`, and `tach check` reports
    # none
    assert importers == []
    assert tach.returncode == 0
