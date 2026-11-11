# SPDX-License-Identifier: Apache-2.0
"""Read the imports of a source file from its syntax tree."""

import ast


def modules_imported(node: ast.AST) -> list[str]:
    """Name the modules that a syntax node imports.

    Args:
        node: Any node of a syntax tree.

    Returns:
        The modules, empty for a node that is not an import.
    """
    match node:
        case ast.Import(names=aliases):
            return [alias.name for alias in aliases]
        case ast.ImportFrom(module=module):
            return [module or ""]
        case _:
            return []
