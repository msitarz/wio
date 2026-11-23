# SPDX-License-Identifier: Apache-2.0
"""Tests of the hash of a rule file."""

from wio.formats import rule_hash


def test_the_hash_is_the_sha256_of_the_bytes() -> None:
    """AC-3: the digests of the empty input and of `abc`."""
    # Given the bytes of the empty input and of `abc`
    empty, abc = b"", b"abc"

    # When `rule_hash` runs on each
    results = (rule_hash(empty), rule_hash(abc))

    # Then the results are the known SHA-256 digests, as 64 lower-case digits
    assert results == (
        "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad",
    )
