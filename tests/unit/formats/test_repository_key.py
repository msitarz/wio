# SPDX-License-Identifier: Apache-2.0
"""The clone key shared by file delivery and the event log."""

from pathlib import Path

from wio.log.locate import log_directory


def test_repository_key_preserves_the_log_key() -> None:
    """A-2: the shared key keeps the existing name and identity digest."""
    # Given the identity from the contract and other clone identities
    from wio.formats.repository_key import repository_key

    identities = [Path("/home/u/src/wio/.git"), Path("/other/wio.git"), Path("/repo")]

    # When each clone's key is computed
    keys = [repository_key(identity) for identity in identities]

    # Then it matches the unchanged log directory's name
    assert keys[0] == "wio-c4555ef0c89d"
    assert keys == [
        log_directory(identity, Path("/home")).name for identity in identities
    ]
