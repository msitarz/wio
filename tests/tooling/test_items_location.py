# SPDX-License-Identifier: Apache-2.0
"""Tests of where the items of a section are found."""

import ast
from pathlib import Path

SRC = Path(__file__).resolve().parents[2] / "src" / "wio"


def _modules_imported(node: ast.AST) -> list[str]:
    """Name the modules that a syntax node imports.

    Args:
        node: Any node of a syntax tree.

    Returns:
        The modules, empty for a node that is not an import.
    """
    match node:
        case ast.Import(names=names):
            return [alias.name for alias in names]
        case ast.ImportFrom(module=module):
            return [module or ""]
        case _:
            return []


def _imports_the_parser(path: Path) -> bool:
    """Tell whether a source file imports `markdown_it`, in any form.

    Args:
        path: A Python source file.

    Returns:
        Whether a syntax node of it imports `markdown_it` or one of its modules.
    """
    tree = ast.parse(path.read_text(encoding="utf-8"))
    return any(
        name.split(".")[0] == "markdown_it"
        for node in ast.walk(tree)
        for name in _modules_imported(node)
    )


def _exports(path: Path) -> set[str]:
    """Read the names that a module lists in `__all__`.

    Args:
        path: A Python source file with an `__all__` list.

    Returns:
        The names in the list.
    """
    for node in ast.parse(path.read_text(encoding="utf-8")).body:
        match node:
            case ast.Assign(
                targets=[ast.Name(id="__all__")], value=ast.List(elts=names)
            ):
                return {
                    str(name.value) for name in names if isinstance(name, ast.Constant)
                }
    return set()


def test_only_wio_formats_imports_the_parser_and_exports_the_items() -> None:
    """AC-6: `wio.formats` exports the finder and the judge of items."""
    # Given the sources of `src/wio`
    sources = sorted(SRC.rglob("*.py"))

    # When their syntax trees are searched for the imports of `markdown_it` and
    # for the exports of `wio.formats`
    importers = {
        path.relative_to(SRC).parts[0] for path in sources if _imports_the_parser(path)
    }
    exports = _exports(SRC / "formats" / "__init__.py")

    # Then only modules of `wio.formats` import `markdown_it`, and `wio.formats`
    # exports the finder and the judge
    assert importers == {"formats"}
    assert {"find_items", "judge_items"} <= exports
