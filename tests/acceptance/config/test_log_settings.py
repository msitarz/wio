# SPDX-License-Identifier: Apache-2.0
"""Acceptance scenarios for the event-log settings of a config."""

from typing import TYPE_CHECKING

import pytest

from tests.acceptance.channels import Channel

if TYPE_CHECKING:
    from tests.acceptance.dsl.wio import Wio

CONFIG = ".agents/wio/config.toml"


@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
def test_built_in_harnesses_need_no_configuration(wio: Wio) -> None:
    """AC-1: The config exposes the built-in harnesses with default sources."""
    # Given a config that omits the log settings.
    wio.fixture("config/rich")
    wio.put(CONFIG, b"")

    # When the default settings are shown and the config is checked.
    shown = wio.run(["config", "show", "log"])
    checked = wio.run(["config", "check"])

    # Then all built-in settings show their defaults and the config passes.
    assert shown.exit_code == checked.exit_code == 0
    assert shown.lines == [
        "log.harnesses.claude-code.parent = []  # default",
        'log.harnesses.claude-code.session = ["CLAUDE_CODE_SESSION_ID"]  # default',
        'log.harnesses.codex.parent = ["CODEX_SESSION_ID"]  # default',
        (
            'log.harnesses.codex.session = ["CODEX_THREAD_ID", "CODEX_SESSION_ID"]'
            "  # default"
        ),
        "log.prefer_harness = []  # default",
        'log.record_env_vars = ["AI_AGENT"]  # default',
    ]


@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
def test_configured_harnesses_add_or_replace_entries(wio: Wio) -> None:
    """AC-2: A configured harness replaces a built-in harness as a whole."""
    # Given a config that adds cursor with session ["CURSOR_TRACE_ID"] and
    # parent ["CURSOR_PARENT_ID"], and replaces codex with ["MY_CODEX_ID"].
    wio.fixture("config/rich")
    wio.put(
        CONFIG,
        b'[log.harnesses.cursor]\nsession = ["CURSOR_TRACE_ID"]\n'
        b'parent = ["CURSOR_PARENT_ID"]\n[log.harnesses.codex]\n'
        b'session = ["MY_CODEX_ID"]\n',
    )

    # When the settings are listed and shown.
    listed = wio.run(["config", "list"])
    shown = wio.run(["config", "show", "log.harnesses"])

    # Then list includes cursor, codex and claude-code. Show reports the two
    # cursor lists with source file, an empty codex parent list, and
    # ["CLAUDE_CODE_SESSION_ID"] with source default for claude-code.
    assert listed.exit_code == shown.exit_code == 0
    assert all(
        f"log.harnesses.{name}.session" in listed.stdout
        for name in ("cursor", "codex", "claude-code")
    )
    assert shown.lines == [
        "log.harnesses.claude-code.parent = []  # default",
        'log.harnesses.claude-code.session = ["CLAUDE_CODE_SESSION_ID"]  # default',
        "log.harnesses.codex.parent = []  # default",
        'log.harnesses.codex.session = ["MY_CODEX_ID"]  # file',
        'log.harnesses.cursor.parent = ["CURSOR_PARENT_ID"]  # file',
        'log.harnesses.cursor.session = ["CURSOR_TRACE_ID"]  # file',
    ]


@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
def test_harness_preference_keeps_order(wio: Wio) -> None:
    """AC-3: A preference names known harnesses in order."""
    # Given a preference for Codex over Claude Code.
    wio.fixture("config/rich")
    wio.put(CONFIG, b'[log]\nprefer_harness = ["codex", "claude-code"]\n')

    # When the preference is shown and the config is checked.
    shown = wio.run(["config", "show", "log.prefer_harness"])
    checked = wio.run(["config", "check"])

    # Then the preference is from the file and the config passes.
    assert shown.exit_code == checked.exit_code == 0
    assert shown.lines[0] == 'log.prefer_harness = ["codex", "claude-code"]  # file'


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


@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
@pytest.mark.parametrize(
    ("text", "path"),
    [
        ('[log]\nprefer_harness = ["cursor"]', "log.prefer_harness"),
        ('[log]\nprefer_harness = ["codex", "codex"]', "log.prefer_harness"),
        ('[log.harnesses.none]\nsession = ["X"]', "log.harnesses.none"),
        ('[log.harnesses."bad name"]\nsession = ["X"]', 'log.harnesses."bad name"'),
        ("[log.harnesses.a]", "log.harnesses.a.session"),
        ("[log.harnesses.a]\nsession = []", "log.harnesses.a.session"),
        ('[log.harnesses.a]\nsession = ["bad name"]', "log.harnesses.a.session"),
        ('[log.harnesses.a]\nsession = ["S", "S"]', "log.harnesses.a.session"),
        (
            '[log.harnesses.a]\nsession = ["S"]\nparent = ["1X"]',
            "log.harnesses.a.parent",
        ),
        (
            '[log.harnesses.a]\nsession = ["S"]\nparent = ["X", "X"]',
            "log.harnesses.a.parent",
        ),
        ('[log]\nrecord_env_vars = ["bad name"]', "log.record_env_vars"),
        ('[log]\nrecord_env_vars = ["AI_AGENT", "AI_AGENT"]', "log.record_env_vars"),
        ("[log]\nbogus = 1", "log.bogus"),
        ('[log.harnesses.a]\nsession = ["S"]\nbogus = 1', "log.harnesses.a.bogus"),
    ],
)
def test_invalid_log_settings_name_the_affected_key(
    wio: Wio, text: str, path: str
) -> None:
    """AC-3, AC-5: One invalid setting gives one error at its key path."""
    # Given a config with one faulty log setting.
    wio.fixture("config/rich")
    wio.put(CONFIG, text.encode())

    # When the config is checked.
    checked = wio.run(["config", "check"])

    # Then it exits 1 and reports one error at the affected key.
    assert checked.exit_code == 1
    assert len(checked.lines) == 1
    assert checked.lines[0].startswith(f"error: {path}: ")


@pytest.mark.channels(Channel.CLI)
def test_other_commands_refuse_invalid_log_settings(wio: Wio) -> None:
    """AC-5: The config check reports bad settings and other commands refuse them."""
    # Given a config with an unknown key under log.
    wio.fixture("config/rich")
    wio.put(CONFIG, b"[log]\nbogus = 1")
    checked = wio.run(["config", "check"])

    # When another command needs the config.
    refused = wio.run(["contracts", "check"])

    # Then it exits 2, repeats the config error on stderr and leaves stdout empty.
    assert refused.exit_code == 2
    assert refused.stdout == ""
    assert refused.stderr.splitlines() == checked.lines
