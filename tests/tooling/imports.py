# SPDX-License-Identifier: Apache-2.0
"""Read the imports of a source file from its syntax tree."""

import ast


def modules_imported(
    node: ast.AST, package: str = "", *, members: bool = False
) -> list[str]:
    """Name the modules that a syntax node imports.

    A `from` import names its module. With `members`, it also names, for each name
    it takes, the module with that name below it, because
    `from wio import templates` imports the module `wio.templates` when
    `templates` is one, so a scan for a component sees it.

    Args:
        node: Any node of a syntax tree.
        package: The package of the file that the node is in, such as
            `wio.contracts`, which a relative import is resolved against, or empty
            to leave a relative import as it is written.
        members: Whether a `from` import also names each name it takes below its
            module.

    Returns:
        The modules, empty for a node that is not an import.
    """
    match node:
        case ast.Import(names=aliases):
            return [alias.name for alias in aliases]
        case ast.ImportFrom():
            return _from_modules(node, package, members=members)
        case _:
            return []


def _from_modules(node: ast.ImportFrom, package: str, *, members: bool) -> list[str]:
    """Name the modules that a `from` import names.

    Args:
        node: The import.
        package: The package of the file, as `modules_imported` takes it.
        members: Whether to name each name it takes below its module.

    Returns:
        The module, and with `members` each name below it.
    """
    base = _absolute(node.module or "", node.level, package)
    below = [f"{base}.{alias.name}" for alias in node.names if base]
    return [base, *(below if members else [])]


def _absolute(module: str, level: int, package: str) -> str:
    """Resolve the module of a `from` import against the file's package.

    Args:
        module: The module as written, empty for `from . import x`.
        level: The number of leading dots.
        package: The package of the file, or empty when it is not known.

    Returns:
        The absolute module, or the module with its dots when `package` is empty.
    """
    if not level:
        return module
    if not package:
        return "." * level + module
    parts = package.split(".")
    base = ".".join(parts[: len(parts) - (level - 1)])
    return f"{base}.{module}" if module else base
