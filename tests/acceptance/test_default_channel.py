# SPDX-License-Identifier: Apache-2.0
"""Test of the channel a test gets when it names none."""

from tests.acceptance.channels import Channel


def test_a_test_without_a_marker_uses_the_in_process_channel(
    channel: Channel,
) -> None:
    """The default channel fixture is the in-process one."""
    # Given a test with no channels marker

    # When it asks for the channel
    used = channel

    # Then it is the in-process channel
    assert used is Channel.IN_PROCESS
