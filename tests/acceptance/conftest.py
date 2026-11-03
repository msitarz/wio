# SPDX-License-Identifier: Apache-2.0
"""Fixtures and channel parametrization for the acceptance scenarios."""

from typing import TYPE_CHECKING

import pytest

from tests.acceptance.channels import Channel
from tests.acceptance.drivers.cli import CliDriver
from tests.acceptance.drivers.in_process import InProcessDriver
from tests.acceptance.dsl.wio import Wio
from tests.acceptance.sandbox import Sandbox

if TYPE_CHECKING:
    from pathlib import Path

    from tests.acceptance.drivers.base import WioDriver


def pytest_generate_tests(metafunc: pytest.Metafunc) -> None:
    """Run a test once per channel of its `channels` marker.

    The CLI case is marked `slow`, because it spawns the real command.

    Args:
        metafunc: The test being collected.
    """
    marker = metafunc.definition.get_closest_marker("channels")
    if marker is None:
        return
    params = [
        pytest.param(
            channel,
            id=channel.value,
            marks=[pytest.mark.slow] if channel is Channel.CLI else [],
        )
        for channel in marker.args
    ]
    metafunc.parametrize("channel", params)


@pytest.fixture
def channel() -> Channel:
    """The channel of a test with no `channels` marker.

    Returns:
        The in-process channel.
    """
    return Channel.IN_PROCESS


def driver_for(channel: Channel, sandbox: Sandbox) -> WioDriver:
    """Build the test driver of a channel.

    Args:
        channel: The channel to reach `wio` on.
        sandbox: The directory and environment to give `wio`.

    Returns:
        The in-process or the CLI test driver, built from the sandbox.
    """
    match channel:
        case Channel.IN_PROCESS:
            return InProcessDriver(sandbox)
        case Channel.CLI:
            return CliDriver(sandbox)


@pytest.fixture
def wio(channel: Channel, tmp_path: Path) -> Wio:
    """The facade, over the test driver of the test's channel.

    Args:
        channel: The channel the test runs on.
        tmp_path: The test's own temporary directory.

    Returns:
        A facade over a sandbox under `tmp_path`.
    """
    return Wio(driver_for(channel, Sandbox.under(tmp_path)))
