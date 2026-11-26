# SPDX-License-Identifier: Apache-2.0
"""Join the rendered parts of a context bundle and name the resulting text.

Assembly defines the boundaries used to measure the body and identify the
bundle.
"""

from typing import Final
lazy from collections.abc import Callable

from wio.context.identity import bundle_id

_CLOSING: Final = "If your context was compacted, run the command in the header again."


def assemble(
    stage: str, contract: str, rules: str, header_for: Callable[[int, int], str]
) -> str:
    """Assemble the metadata, header and body of a bundle.

    The body labels the nonempty parts in stage, contract and rules order and
    ends with the compaction instruction and one newline. Parts keep their
    whitespace except for trailing newlines. A blank line separates each part
    and each section. The id covers the header and body with their separator.

    Args:
        stage: The rendered stage guidance.
        contract: The rendered contract.
        rules: The rendered rules.
        header_for: Builds the header from the UTF-8 byte count and newline
            count of the body, in that order, and returns it without trailing
            newlines.

    Returns:
        The complete bundle with its id in the first line.
    """
    parts: list[str] = []
    for label, part in (("stage", stage), ("contract", contract), ("rules", rules)):
        trimmed = part.rstrip("\n")
        if trimmed:
            parts.append(f"--- {label} ---\n\n{trimmed}")
    parts.append(_CLOSING)

    body = "\n\n".join(parts) + "\n"
    header = header_for(len(body.encode("utf-8")), body.count("\n"))
    text = f"{header}\n\n{body}"
    return f"bundle: {bundle_id(text)}\n\n{text}"
