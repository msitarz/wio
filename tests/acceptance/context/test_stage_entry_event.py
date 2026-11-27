# SPDX-License-Identifier: Apache-2.0
"""System acceptance scenario for parent Work 18m35a (Stage-entry event)."""

from typing import TYPE_CHECKING

import pytest

from tests.acceptance.channels import Channel
from tests.acceptance.context.test_stage_entry import read_events

if TYPE_CHECKING:
    from pathlib import Path

    from tests.acceptance.dsl.wio import Wio
    from tests.sandbox import Sandbox

_CONFIG = """\
rules_always_include = ["demo.ARC001"]

[works.defaults.actions]
deliver = ["review"]

[actions.deliver]
description = "Deliver"

[roots.api]
paths = []

[rulesets.demo]
root_independent = true

[stages.review]
goal = "Review"
gate = true
"""

_RULE = """\
<!-- wio
code = "ARC001"
name = "use-ports"
-->

Keep ports typed.
"""


@pytest.mark.channels(Channel.CLI)
def test_a_gate_run_writes_one_combined_context_event(
    wio: Wio, sandbox: Sandbox, tmp_path: Path
) -> None:
    """AC-1: a gate writes one event with stage-entry fields, start, and dirty."""
    # Given a committed repository with a rule and a stage with `gate = true`
    wio.fixture("context/unreadable")
    wio.put(".agents/wio/config.toml", _CONFIG.encode("utf-8"))
    wio.put(
        ".agents/wio/rules/demo/ruleset.toml",
        b'[families]\nARC = "Architecture"\n',
    )
    wio.put(".agents/wio/rules/demo/ARC001-use-ports.md", _RULE.encode("utf-8"))
    wio.commit("feat: initial work\n\nWio-Work: none")
    head_sha = wio.driver.git(["rev-parse", "HEAD"]).stdout.strip()
    log_home = tmp_path / "wio-home"
    sandbox.env["WIO_HOME"] = str(log_home)

    # When `wio context` runs for the gate stage
    result = wio.run(["context", "k3m9xq", "deliver", "review"])

    # Then the log holds exactly one context event carrying all stage-entry and
    # gate-start fields
    assert (result.exit_code, result.stderr) == (0, "")
    first_line, _, body = result.stdout.split("\n\n", 2)
    bundle_id = first_line.removeprefix("bundle: ")
    body_size = len(body.encode("utf-8"))
    (event,) = read_events(log_home)
    assert event["type"] == "context"
    assert event["work"] == "k3m9xq"
    assert event["action"] == "deliver"
    assert event["stage"] == "review"
    assert event["bundle"] == bundle_id
    assert event["size"] == body_size
    assert list(event["rules"]) == ["demo.ARC001"]
    assert isinstance(event["rules"]["demo.ARC001"], str)
    assert event["start"] == head_sha
    assert event["dirty"] is False
