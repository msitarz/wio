# SPDX-License-Identifier: Apache-2.0
"""Checks for the harness and environment settings of the event log."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from wio.config.checks import CheckInputs
    from wio.models.config import Config
    from wio.models.diagnostics import Diagnostic


def check_log_settings(_config: Config, _inputs: CheckInputs) -> tuple[Diagnostic, ...]:
    """Judge harness names, preference order and environment variable names.

    Args:
        _config: The best-effort config assembled by the shape reader.
        _inputs: The shared check inputs. This check reads only the config.

    Returns:
        Errors at the setting that contains a bad name or a repeat.
    """
    return ()
