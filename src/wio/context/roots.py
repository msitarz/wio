# SPDX-License-Identifier: Apache-2.0
"""The Work roots selected by a context stage."""


def selects_work_roots(roots: tuple[str, ...] | None) -> bool:
    """Tell whether a stage selects the Work's roots.

    Args:
        roots: The stage's roots, or None when the setting is absent.

    Returns:
        True when roots are absent or explicitly include `@work`.
    """
    return roots is None or "@work" in roots
