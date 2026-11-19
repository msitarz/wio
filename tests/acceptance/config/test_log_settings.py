# SPDX-License-Identifier: Apache-2.0
"""Acceptance scenarios for the event-log settings of a config."""

from typing import TYPE_CHECKING

import pytest

from tests.acceptance.channels import Channel

if TYPE_CHECKING:
    from tests.acceptance.dsl.wio import Wio

pytestmark = pytest.mark.usefixtures("wio")
CONFIG = ".agents/wio/config.toml"


@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
def test_built_in_harnesses_need_no_configuration() -> None:
    """AC-1: The config exposes the built-in harnesses with default sources."""
    # Given a config that omits the log settings.
    # When the default settings are shown and the config is checked.
    # Then show reports Codex session ["CODEX_THREAD_ID", "CODEX_SESSION_ID"],
    # Codex parent ["CODEX_SESSION_ID"], Claude Code session
    # ["CLAUDE_CODE_SESSION_ID"] and record_env_vars ["AI_AGENT"], each with
    # source default, and config check exits 0.
    pytest.skip("Pending log settings wiring")


@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
def test_configured_harnesses_add_or_replace_entries() -> None:
    """AC-2: A configured harness replaces a built-in harness as a whole."""
    # Given a config that adds cursor with session ["CURSOR_TRACE_ID"] and
    # parent ["CURSOR_PARENT_ID"], and replaces codex with ["MY_CODEX_ID"].
    # When the settings are listed and shown.
    # Then list includes cursor, codex and claude-code. Show reports the two
    # cursor lists with source file, an empty codex parent list, and
    # ["CLAUDE_CODE_SESSION_ID"] with source default for claude-code.
    pytest.skip("Pending log settings wiring")


@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
def test_harness_preference_names_are_checked() -> None:
    """AC-3: The preference accepts known names and refuses invalid choices."""
    # Given configs that prefer ["codex", "claude-code"], ["cursor"] and
    # ["codex", "codex"], and one that declares a harness named none.
    # When the valid preference is shown and each config is checked.
    # Then show reports ["codex", "claude-code"] with source file and its
    # check exits 0. Each other check exits 1 with one error at
    # log.prefer_harness, log.prefer_harness and log.harnesses.none in turn.
    pytest.skip("Pending log settings wiring")


@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
@pytest.mark.parametrize("value", ['["MY_VAR"]', "[]"])
def test_additional_environment_variables_replace_the_default(
    wio: Wio, value: str
) -> None:
    """AC-4: A project can select extra variables or select none."""
    # Given configs that set record_env_vars to ["MY_VAR"] and [].
    wio.fixture("config/rich")
    wio.put(CONFIG, f"[log]\nrecord_env_vars = {value}\n".encode())

    # When each list is shown and its config is checked.
    shown = wio.run(["config", "show", "log.record_env_vars"])
    checked = wio.run(["config", "check"])

    # Then show reports ["MY_VAR"] and [] with source file, and both checks
    # exit 0.
    assert shown.lines[0] == f"log.record_env_vars = {value}  # file"
    assert shown.exit_code == checked.exit_code == 0


@pytest.mark.channels(Channel.CLI)
def test_invalid_log_settings_are_reported_and_refused() -> None:
    """AC-5: The config check reports bad settings and other commands refuse them."""
    # Given configs with a missing or empty session list, a bad or repeated
    # session, parent or record_env_vars name, or a bogus key in log or
    # log.harnesses.a. Each config contains one fault.
    # When each config is checked and a broken config runs contracts check.
    # Then each check exits 1 with one error at the corresponding key,
    # log.harnesses.a.session, log.harnesses.a.parent, log.record_env_vars,
    # log.bogus or log.harnesses.a.bogus. Contracts check exits 2, echoes the
    # config error to stderr and leaves stdout empty.
    pytest.skip("Pending log settings wiring")
