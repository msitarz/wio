# SPDX-License-Identifier: Apache-2.0
"""Warnings when a compiled bundle body exceeds the configured size."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable
    from contextlib import AbstractContextManager

    from tests.acceptance.dsl.wio import Wio

_ARGS = ["context", "k3m9xq", "deliver", "implementation"]
_CONFIG = ".agents/wio/config.toml"


def _config(wio: Wio, threshold: int | None) -> None:
    """Install the sample repository with an optional size threshold.

    Args:
        wio: The scenario's facade.
        threshold: The threshold, or None to leave it unset.
    """
    wio.fixture("context/unreadable")
    if threshold is not None:
        value = f"[bundle]\nsize_threshold = {threshold}\n".encode()
        wio.put(_CONFIG, value + wio.read(_CONFIG))


def _warning(size: int, threshold: int) -> str:
    """Describe the expected single size warning.

    Args:
        size: The body size.
        threshold: The configured threshold.

    Returns:
        The full warning line.
    """
    return (
        f"warning: Bundle body size (bytes): {size}; threshold (bytes): {threshold}.\n"
    )


def test_body_size_above_but_not_equal_to_threshold_warns(
    wio: Wio,
    prepared_compiler: Callable[[str, int], AbstractContextManager[None]],
) -> None:
    """AC-1: the compiler's body size, not the text length, is compared."""
    # Given a threshold of 1000 and 1400-byte bundle texts
    _config(wio, 1000)
    text = "x" * 1400

    # When bodies of 1001 and 1000 bytes are delivered
    with prepared_compiler(text, 1001):
        above = wio.run(_ARGS)
    with prepared_compiler(text, 1000):
        equal = wio.run(_ARGS)

    # Then both bundles print and only the larger body warns
    assert (above.exit_code, above.stdout, above.stderr) == (
        0,
        text,
        _warning(1001, 1000),
    )
    assert (equal.exit_code, equal.stdout, equal.stderr) == (0, text, "")


def test_no_threshold_never_warns_about_the_body_size(
    wio: Wio,
    prepared_compiler: Callable[[str, int], AbstractContextManager[None]],
) -> None:
    """AC-2: even a very large body has no size warning when unset."""
    # Given a config without a threshold and a very large body
    _config(wio, None)

    # When the bundle is delivered
    with prepared_compiler("fixed", 1_000_000):
        result = wio.run(_ARGS)

    # Then the bundle prints without a warning
    assert (result.exit_code, result.stdout, result.stderr) == (0, "fixed", "")


def test_zero_and_negative_thresholds_warn_for_one_byte(
    wio: Wio,
    prepared_compiler: Callable[[str, int], AbstractContextManager[None]],
) -> None:
    """AC-3: zero and negative thresholds remain valid and compare normally."""
    # Given valid configs with thresholds zero and minus one
    _config(wio, 0)
    base = wio.read(_CONFIG)
    results = []
    checked = []

    # When each config is checked and a one-byte body is delivered
    for threshold in (0, -1):
        wio.put(
            _CONFIG,
            base.replace(
                b"size_threshold = 0", f"size_threshold = {threshold}".encode()
            ),
        )
        checked.append(wio.run(["config", "check"]))
        with prepared_compiler("x", 1):
            results.append(wio.run(_ARGS))

    # Then both configs are valid and each body warns once
    assert all(result.exit_code == 0 for result in checked)
    assert [(r.exit_code, r.stdout, r.stderr) for r in results] == [
        (0, "x", _warning(1, 0)),
        (0, "x", _warning(1, -1)),
    ]


def test_size_warning_precedes_a_failed_delivery(
    wio: Wio,
    prepared_compiler: Callable[[str, int], AbstractContextManager[None]],
) -> None:
    """A failed file delivery still reports the size warning."""
    # Given an oversized body and an output path that is a directory
    _config(wio, 1000)

    # When the bundle is delivered to that path
    with prepared_compiler("x", 1001):
        result = wio.run([*_ARGS, "--output", "."])

    # Then the warning appears before the refusal and no bundle is printed
    assert (result.exit_code, result.stdout) == (2, "")
    assert result.stderr.startswith(_warning(1001, 1000))
    assert "error:" in result.stderr
