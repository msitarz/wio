# SPDX-License-Identifier: Apache-2.0
"""Tests for the port and shared-type stubs that make up the architecture."""

import ast
from pathlib import Path

import pytest

SRC = Path(__file__).resolve().parents[2] / "src" / "wio"
PORTS = sorted(SRC.glob("*/ports.pyi"))
MODELS = sorted((SRC / "models").glob("*.pyi"))
ALLOWED = ("wio.models", "wio.io")


def _tree(path: Path) -> ast.Module:
    """Parse a stub.

    Args:
        path: The `.pyi` file.

    Returns:
        Its syntax tree.
    """
    return ast.parse(path.read_text(encoding="utf-8"))


def _undocumented(path: Path) -> list[str]:
    """List the items of a stub that have no docstring.

    Args:
        path: The `.pyi` file.

    Returns:
        The names of the module, classes and functions without a docstring.
    """
    tree = _tree(path)
    nodes = [tree, *(n for n in ast.walk(tree) if isinstance(n, ast.ClassDef))]
    nodes += [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]
    return [
        getattr(node, "name", path.name)
        for node in nodes
        if not ast.get_docstring(node)
    ]


def _models_named_by(path: Path) -> set[str]:
    """List the `wio.models` names that a stub imports.

    Args:
        path: The `.pyi` file.

    Returns:
        The imported names.
    """
    imports = (n for n in ast.walk(_tree(path)) if isinstance(n, ast.ImportFrom))
    return {
        alias.name
        for node in imports
        if (node.module or "").startswith("wio.models")
        for alias in node.names
    }


def _declared_types(path: Path) -> set[str]:
    """List the types a models stub declares.

    Args:
        path: The `.pyi` file.

    Returns:
        The names of its classes and type aliases.
    """
    nodes = ast.walk(_tree(path))
    classes = {n.name for n in nodes if isinstance(n, ast.ClassDef)}
    aliases = {n.name.id for n in ast.walk(_tree(path)) if isinstance(n, ast.TypeAlias)}
    return classes | aliases


@pytest.mark.parametrize(
    "path", [*PORTS, *MODELS], ids=lambda p: str(p.relative_to(SRC))
)
def test_every_item_of_a_stub_has_a_docstring(path: Path) -> None:
    """Each module, class and method of a stub says what it guarantees."""
    # Given a port or shared-type stub

    # When the items without a docstring are listed
    missing = _undocumented(path)

    # Then there are none
    assert missing == []


@pytest.mark.parametrize("path", PORTS, ids=lambda p: str(p.relative_to(SRC)))
def test_a_port_stub_imports_nothing_from_a_neighbor(path: Path) -> None:
    """A stub imports only shared types, the io ports and the standard library."""
    # Given a ports stub
    tree = _tree(path)

    # When the `wio` modules it imports are listed
    imported = {
        node.module
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and (node.module or "").startswith("wio")
    }

    # Then each is a shared type module or the io ports
    assert [m for m in imported if not (m or "").startswith(ALLOWED)] == []


def _alias_parts(path: Path) -> dict[str, set[str]]:
    """Map each type alias of a models stub to the names in its definition.

    Args:
        path: The `.pyi` file.

    Returns:
        For each alias, the names its definition uses.
    """
    return {
        node.name.id: {n.id for n in ast.walk(node.value) if isinstance(n, ast.Name)}
        for node in ast.walk(_tree(path))
        if isinstance(node, ast.TypeAlias)
    }


def _named_types() -> set[str]:
    """List the shared types the ports name, including an alias's members.

    Returns:
        The names the ports import from `wio.models`, plus the names inside
        any type alias among them.
    """
    named = {name for path in PORTS for name in _models_named_by(path)}
    parts = {k: v for path in MODELS for k, v in _alias_parts(path).items()}
    return named | {member for alias in named for member in parts.get(alias, set())}


def test_the_shared_types_are_those_the_ports_name() -> None:
    """Every type a port names has one stub, and no stub goes unused."""
    # Given the types the ports name, and the types the stubs declare
    named = _named_types()
    declared = [name for path in MODELS for name in _declared_types(path)]

    # When the two are compared
    undeclared = named - set(declared)
    unused = set(declared) - named
    repeated = {name for name in declared if declared.count(name) > 1}

    # Then they match, and no type is declared twice
    assert (undeclared, unused, repeated) == (set(), set(), set())
