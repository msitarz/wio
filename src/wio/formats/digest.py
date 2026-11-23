# SPDX-License-Identifier: Apache-2.0
"""The hash that identifies the bytes of a rule file."""


def rule_hash(data: bytes) -> str:
    """Hash the bytes of a rule file.

    The `context` event records this string for every rule of a bundle, and
    `wio trailers` compares it with the one it receives from the selector, so one
    function gives both. It hashes the bytes as stored and no decoded text, so a
    change to any part of the file, a line ending included, changes the result.

    Args:
        data: The bytes of the file.

    Returns:
        The SHA-256 of `data` as 64 lower-case hexadecimal digits.
    """
    del data
    raise NotImplementedError
