# SPDX-License-Identifier: Apache-2.0
"""Tests of what the modules of `wio.contracts` import."""

import ast
import subprocess
import sys
from pathlib import Path

import pytest

from tests.tooling.imports import modules_imported

ROOT = Path(__file__).resolve().parents[2]
CONTRACTS = ROOT / "src" / "wio" / "contracts"
FORBIDDEN = (
    "wio.cli",
    "wio.config",
    "wio.templates",
    "wio.rules",
    "wio.trailers",
    "wio.log",
    "wio.context",
    "wio.io.adapters",
    "wio.env.adapters",
    "tomllib",
    "tomlkit",
    "markdown_it",
)
"""The components and the libraries that `wio.contracts` never imports."""


def _forbidden_imports(path: Path) -> list[str]:
    """List the forbidden modules that a source file imports, in any form.

    Args:
        path: A Python source file.

    Returns:
        The imported modules that are `FORBIDDEN` or below one of them, one for
        each import, with the file's name.
    """
    tree = ast.parse(path.read_text(encoding="utf-8"))
    return [
        f"{path.name}: {name}"
        for node in ast.walk(tree)
        for name in modules_imported(node)
        for bad in FORBIDDEN
        if name == bad or name.startswith(f"{bad}.")
    ]


@pytest.mark.slow
def test_wio_contracts_imports_no_component_and_no_codec_library() -> None:
    """Parent AC-7: the sources show none, and `tach` and `ruff` report none."""
    # Given the sources of `src/wio/contracts`
    sources = sorted(CONTRACTS.rglob("*.py"))

    # When the imports of its modules are read from their syntax trees, and
    # `tach check` and `ruff check` run on `src/wio`
    found = [bad for path in sources for bad in _forbidden_imports(path)]
    tach = subprocess.run(
        [sys.executable, "-m", "tach", "check"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    ruff = subprocess.run(
        [sys.executable, "-m", "ruff", "check", "src/wio"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    # Then the trees show no such import, and both tools report none
    assert sources
    assert found == []
    assert tach.returncode == 0
    assert ruff.returncode == 0
