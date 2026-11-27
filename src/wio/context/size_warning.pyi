# SPDX-License-Identifier: Apache-2.0
"""The warning for a bundle body above the configured size threshold."""

def size_warning(size: int, threshold: int | None) -> str | None:
    """Judge the bundle body size against an optional byte threshold.

    Args:
        size: The compiled bundle body's size in UTF-8 bytes.
        threshold: The configured threshold in bytes, or None when unset.

    Returns:
        A warning naming both numbers if size exceeds threshold, otherwise None.
        The warning has no prefix or newline.
    """
    ...
