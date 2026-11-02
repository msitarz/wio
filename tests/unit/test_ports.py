# SPDX-License-Identifier: Apache-2.0
"""Tests for the port and shared-type stubs that make up the architecture."""

import ast
import re
import sys
from dataclasses import dataclass
from pathlib import Path

import pytest

SRC = Path(__file__).resolve().parents[2] / "src" / "wio"
PORTS = sorted(SRC.glob("*/ports.pyi"))
MODELS = sorted((SRC / "models").glob("*.pyi"))
OWNERS = {"cli", "context", "contract", "env", "io", "rule", "trailers"}


def _tree(path: Path) -> ast.Module:
    """Parse a stub.

    Args:
        path: The `.pyi` file.

    Returns:
        Its syntax tree.
    """
    return ast.parse(path.read_text(encoding="utf-8"))


def _name(path: Path) -> str:
    """Name a stub for a test id.

    Args:
        path: A stub under `src/wio`.

    Returns:
        Its path relative to `src/wio`.
    """
    return str(path.relative_to(SRC))


def _undocumented(path: Path) -> list[str]:
    """List the items of a stub that have no docstring.

    Args:
        path: The `.pyi` file.

    Returns:
        The names of the module, classes and functions without a docstring.
    """
    tree = _tree(path)
    nodes = [tree, *(n for n in ast.walk(tree) if isinstance(n, ast.ClassDef))]
    functions = (ast.FunctionDef, ast.AsyncFunctionDef)
    nodes += [n for n in ast.walk(tree) if isinstance(n, functions)]
    return [
        getattr(node, "name", path.name)
        for node in nodes
        if not ast.get_docstring(node)
    ]


def _modules_of(node: ast.AST) -> list[str]:
    """List the module names an import statement refers to.

    Args:
        node: Any syntax node.

    Returns:
        The names, with a leading dot for each level of a relative import, or
        none when the node is not an import.
    """
    if isinstance(node, ast.ImportFrom):
        return [("." * node.level) + (node.module or "")]
    if isinstance(node, ast.Import):
        return [alias.name for alias in node.names]
    return []


@dataclass(frozen=True)
class ImportPolicy:
    """The imports a stub may have besides the standard library."""

    ports: tuple[str, ...] = ()
    models_allowed: bool = True


def _import_problems(path: Path, policy: ImportPolicy) -> list[str]:
    """List the imports of a stub that break the dependency direction.

    A stub may import the standard library and, by absolute name, the shared
    types, and a ports stub also the ports of `wio.io`.

    Args:
        path: The `.pyi` file.
        policy: Which modules besides the standard library may be imported.

    Returns:
        One entry per import that is relative or from anywhere else.
    """
    modules = [m for node in ast.walk(_tree(path)) for m in _modules_of(node)]
    return [m for m in modules if not _allowed(m, policy)]


def _allowed(module: str, policy: ImportPolicy) -> bool:
    """Tell whether a stub may import a module.

    Args:
        module: An absolute or relative module name.
        policy: Which modules besides the standard library may be imported.

    Returns:
        True for the standard library, the policy's ports modules, and
        `wio.models` when the policy allows it.
    """
    top = module.split(".", maxsplit=1)[0]
    is_models = module == "wio.models" or module.startswith("wio.models.")
    return (
        top in sys.stdlib_module_names
        or module in policy.ports
        or (policy.models_allowed and is_models)
    )


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
    nodes = list(ast.walk(_tree(path)))
    classes = {n.name for n in nodes if isinstance(n, ast.ClassDef)}
    aliases = {n.name.id for n in nodes if isinstance(n, ast.TypeAlias)}
    return classes | aliases


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


def _named_types(declared: set[str]) -> set[str]:
    """List the shared types the ports name, including an alias's members.

    Args:
        declared: The types the models stubs declare.

    Returns:
        The names the ports import from `wio.models`, plus the declared types
        inside any type alias among them.
    """
    named = {name for path in PORTS for name in _models_named_by(path)}
    parts = {k: v for path in MODELS for k, v in _alias_parts(path).items()}
    return named | {m for a in named for m in parts.get(a, set()) if m in declared}


def test_only_the_consuming_packages_have_a_ports_stub() -> None:
    """Seven packages declare ports, and `config` and `log` declare none."""
    # Given the packages that hold a `ports.pyi`
    owners = {path.parent.name for path in PORTS}

    # When they are compared with the packages that consume something
    # Then they are the same seven
    assert owners == OWNERS


@pytest.mark.parametrize("path", PORTS, ids=_name)
def test_every_class_of_a_ports_stub_is_a_protocol(path: Path) -> None:
    """A port is a `typing.Protocol`, so a provider satisfies it structurally."""
    # Given a ports stub
    classes = [n for n in ast.walk(_tree(path)) if isinstance(n, ast.ClassDef)]

    # When the classes that do not derive from `Protocol` are listed
    others = [
        c.name
        for c in classes
        if not any(isinstance(b, ast.Name) and b.id == "Protocol" for b in c.bases)
    ]

    # Then there are none, and the stub declares at least one port
    assert others == []
    assert classes


@pytest.mark.parametrize("path", [*PORTS, *MODELS], ids=_name)
def test_every_item_of_a_stub_has_a_docstring(path: Path) -> None:
    """Each module, class and method of a stub says what it guarantees."""
    # Given a port or shared-type stub

    # When the items without a docstring are listed
    missing = _undocumented(path)

    # Then there are none
    assert missing == []


def _import_policy(path: Path) -> ImportPolicy:
    """Say which imports a ports stub may have.

    Args:
        path: A `ports.pyi` file.

    Returns:
        `wio.env` imports nothing from wio, `wio.io` only the shared types, and
        a consumer also the ports of `wio.io` and `wio.env`.
    """
    owner = path.parent.name
    if owner == "env":
        return ImportPolicy(models_allowed=False)
    if owner == "io":
        return ImportPolicy()
    return ImportPolicy(ports=("wio.io.ports", "wio.env.ports"))


@pytest.mark.parametrize("path", PORTS, ids=_name)
def test_a_port_stub_imports_only_what_its_owner_may(path: Path) -> None:
    """A stub never imports a neighbor, an adapter or a third-party package."""
    # Given a ports stub and the imports its owner may have
    policy = _import_policy(path)

    # When its imports that break the dependency direction are listed
    problems = _import_problems(path, policy)

    # Then there are none
    assert problems == []


def test_the_temporary_directory_rule_is_in_the_docstring() -> None:
    """The port states how the temporary directory is found."""
    # Given the docstring of the member that returns the temporary directory
    classes = [
        n
        for n in ast.walk(_tree(SRC / "env" / "ports.pyi"))
        if isinstance(n, ast.ClassDef) and n.name == "Directories"
    ]
    methods = [n for n in classes[0].body if isinstance(n, ast.FunctionDef)]
    doc = " ".join((ast.get_docstring(methods[0]) or "").split())

    # When the rule is matched as one ordered statement, and the empty case and
    # the error are looked for
    branches = re.search(
        r"\$TMPDIR` names, as it is.*non-empty value, without testing it\. "
        r"Otherwise.*(?<!private)/tmp` on Linux.*/private/tmp` on macOS.*"
        r"test file can be written there",
        doc,
    )
    empty = re.search(r"empty `\$TMPDIR` (counts as|is treated as) unset", doc)
    error = re.search(r"Raises:\s+OSError", doc)
    missing = [
        name
        for name, found in (("branches", branches), ("empty", empty), ("error", error))
        if not found
    ]

    # Then each is there, with the `$TMPDIR` case before the fallback
    assert missing == []


@pytest.mark.parametrize("path", MODELS, ids=_name)
def test_a_shared_type_stub_imports_only_the_stdlib_and_shared_types(
    path: Path,
) -> None:
    """The shared types depend on nothing else in wio."""
    # Given a shared-type stub

    # When its imports that break the dependency direction are listed
    problems = _import_problems(path, ImportPolicy())

    # Then there are none
    assert problems == []


def test_the_shared_types_are_those_the_ports_name() -> None:
    """Every type a port names has one stub, and no stub goes unused."""
    # Given the types the stubs declare, and the types the ports name
    declared = [name for path in MODELS for name in _declared_types(path)]
    named = _named_types(set(declared))

    # When the two are compared
    undeclared = named - set(declared)
    unused = set(declared) - named
    repeated = {name for name in declared if declared.count(name) > 1}

    # Then they match, and no type is declared twice
    assert (undeclared, unused, repeated) == (set(), set(), set())
