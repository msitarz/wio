# SPDX-License-Identifier: Apache-2.0
"""The warning for a bundle body above the configured size threshold."""


def size_warning(size: int, threshold: int | None) -> str | None:
    """Judge the body size against the optional threshold.

    Args:
        size: The compiled bundle body's size in UTF-8 bytes.
        threshold: The configured threshold in bytes, or None when unset.

    Returns:
        No warning until the comparison is implemented.
    """
    del size, threshold
    return None
