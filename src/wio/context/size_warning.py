# SPDX-License-Identifier: Apache-2.0
"""The warning for a bundle body above the configured size threshold."""


def size_warning(size: int, threshold: int | None) -> str | None:
    """Judge the body size against the optional threshold.

    Args:
        size: The compiled bundle body's size in UTF-8 bytes.
        threshold: The configured threshold in bytes, or None when unset.

    Returns:
        A warning naming both values when size exceeds the threshold,
        or None when the threshold is unset or not exceeded.
    """
    if threshold is None or size <= threshold:
        return None
    return f"Bundle body is {size} bytes; threshold is {threshold} bytes."
