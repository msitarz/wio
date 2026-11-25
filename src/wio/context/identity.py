# SPDX-License-Identifier: Apache-2.0
"""The bundle id: the one value that names what a session was given."""


def bundle_id(text: str) -> str:
    """Name a text by its content.

    The caller chooses the text that is hashed; this function reads nothing else,
    so two equal texts have one id and a change to any character gives another.

    Args:
        text: The text to name.

    Returns:
        The first 12 lower-case hexadecimal digits of the SHA-256 of the UTF-8
        bytes of `text`.
    """
    del text
    raise NotImplementedError
