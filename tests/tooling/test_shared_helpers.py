# SPDX-License-Identifier: Apache-2.0
"""Tests that each shared helper is defined once and used by the components."""

import ast
import sys
from pathlib import Path

SRC = Path(__file__).resolve().parents[2] / "src" / "wio"

HOMES = {
    "walk_markdown": "io/walk.py",
    "refuse_directory": "io/walk.py",
    "closest_key": "formats/closest.py",
    "render_check": "formats/diagnostics.py",
    "order_diagnostics": "models/diagnostics.py",
    "has_error": "models/diagnostics.py",
}
OLD_COPIES = {
    "_walk",
    "_walk_visible",
    "_refuse_directory",
    "_has_error",
    "_order_key",
    "render_check",
}
OUTSIDE_THE_STANDARD_LIBRARY = {
    "io/walk.py": {"wio.models.diagnostics", "wio.io.ports"},
    "formats/closest.py": set(),
    "formats/diagnostics.py": {"wio.models.diagnostics"},
    "models/diagnostics.py": set(),
}


def _tree(path: Path) -> ast.Module:
    """Parse a source file.

    Args:
        path: A Python file.

    Returns:
        Its syntax tree.
    """
    return ast.parse(path.read_text(encoding="utf-8"))


def _defined(path: Path) -> set[str]:
    """Name the functions that a file defines, at any depth.

    Args:
        path: A Python file.

    Returns:
        The names of its function definitions.
    """
    return {
        node.name for node in ast.walk(_tree(path)) if isinstance(node, ast.FunctionDef)
    }


def _imported(path: Path) -> set[str]:
    """Name the modules that a file imports, in any form.

    Args:
        path: A Python file.

    Returns:
        The modules.
    """
    names: set[str] = set()
    for node in ast.walk(_tree(path)):
        match node:
            case ast.Import(names=aliases):
                names.update(alias.name for alias in aliases)
            case ast.ImportFrom(module=module):
                names.add(module or "")
    return names


def _is_error_test(node: ast.AST) -> bool:
    """Tell whether a node compares a `severity` attribute with `error`.

    Args:
        node: Any node of a syntax tree.

    Returns:
        Whether it is such a comparison.
    """
    return (
        isinstance(node, ast.Compare)
        and isinstance(node.left, ast.Attribute)
        and node.left.attr == "severity"
        and any(
            isinstance(other, ast.Constant) and other.value == "error"
            for other in node.comparators
        )
    )


def _asks_for_errors(path: Path) -> bool:
    """Tell whether a file calls `any` on a test of `severity == "error"`.

    Args:
        path: A Python file.

    Returns:
        Whether a call of `any` holds a comparison of a `severity` attribute with
        the text `error`.
    """
    return any(
        _is_error_test(node)
        for call in ast.walk(_tree(path))
        if isinstance(call, ast.Call) and getattr(call.func, "id", "") == "any"
        for node in ast.walk(call)
    )


def _homes_of_helpers(sources: list[Path]) -> dict[str, list[str]]:
    """Find where each helper is defined.

    Args:
        sources: The Python files of `src/wio`.

    Returns:
        For each helper, the files that define it, relative to `src/wio`.
    """
    return {
        name: sorted(
            path.relative_to(SRC).as_posix()
            for path in sources
            if name in _defined(path)
        )
        for name in HOMES
    }


def _old_copies_in_templates() -> set[str]:
    """Find the private copies that `wio.templates` still defines.

    Returns:
        The names among `OLD_COPIES` that a module of it defines.
    """
    return {
        name
        for path in (SRC / "templates").rglob("*.py")
        for name in _defined(path) & OLD_COPIES
    }


def _third_party_imports() -> dict[str, set[str]]:
    """Find what each helper module imports beyond the standard library.

    Returns:
        For each module of `OUTSIDE_THE_STANDARD_LIBRARY`, its imported modules
        that are not the standard library's.
    """
    return {
        home: {
            name
            for name in _imported(SRC / home)
            if name.split(".")[0] not in sys.stdlib_module_names
        }
        for home in OUTSIDE_THE_STANDARD_LIBRARY
    }


def _uses(name: str, module: str) -> bool:
    """Tell whether a module of `wio.config` mentions a helper.

    Args:
        name: The helper.
        module: The file of `wio.config`.

    Returns:
        Whether the file's text holds the name.
    """
    return name in (SRC / "config" / module).read_text(encoding="utf-8")


def test_each_helper_is_defined_once_in_its_package() -> None:
    """AC-10: each helper lives in the package named for it."""
    # Given the sources of `src/wio` after the change
    sources = sorted(SRC.rglob("*.py"))

    # When their syntax trees are searched for the definitions of the helpers, for
    # the use of `severity == "error"` and for the imports of the helper modules
    defined = _homes_of_helpers(sources)
    asking = [p for p in (SRC / "config").rglob("*.py") if _asks_for_errors(p)]
    importers = {
        path.relative_to(SRC).parts[0]
        for path in sources
        if "difflib" in _imported(path)
    }

    # Then each helper is defined only in its package, the components define none
    # of the old private copies, `wio.config` asks `has_error` and `closest_key`,
    # `difflib` is imported only in `wio.formats`, and each helper module imports
    # only what the contract lists
    assert defined == {name: [home] for name, home in HOMES.items()}
    assert _old_copies_in_templates() == set()
    assert asking == []
    assert _uses("has_error", "loader.py")
    assert _uses("has_error", "report.py")
    assert _uses("closest_key", "messages.py")
    assert _uses("closest_key", "keypath.py")
    assert importers == {"formats"}
    assert _third_party_imports() == OUTSIDE_THE_STANDARD_LIBRARY
    assert "difflib" in _imported(SRC / "formats" / "closest.py")
