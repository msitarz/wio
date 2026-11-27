# SPDX-License-Identifier: Apache-2.0
"""System acceptance scenarios for top-level Work j85eh5 (`wio context`)."""

import json
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from tests.acceptance.channels import Channel
from tests.acceptance.context.test_stage_entry import read_events
from tests.acceptance.drivers.in_process import gate_port_states

if TYPE_CHECKING:
    from tests.acceptance.dsl.wio import Wio
    from tests.sandbox import Sandbox

_GOLDEN = Path(__file__).parents[2] / "golden" / "context" / "bundle.txt"

_CONFIG = """\
[works.defaults.actions]
deliver = ["goal", "skilled", "review"]

[actions.deliver]
description = "Deliver"

[roots.api]
paths = ["src"]
rule_presets = ["base"]

[rule_presets.base]
rules_include = ["demo.ARC", "demo.EXC"]
rules_exclude = ["demo.EXC001"]

[rulesets.demo]

[stages.goal]
goal = "Write the code."

[stages.skilled]
skill = "example"

[stages.review]
goal = "Review the code."
gate = true
"""

_CONFIG_REORDERED = """\
[stages.review]
gate = true
goal = "Review the code."

[stages.skilled]
skill = "example"

[stages.goal]
goal = "Write the code."

[rulesets.demo]

[rule_presets.base]
rules_exclude = ["demo.EXC001"]
rules_include = ["demo.ARC", "demo.EXC"]

[roots.api]
rule_presets = ["base"]
paths = ["src"]

[actions.deliver]
description = "Deliver"

[works.defaults.actions]
deliver = ["goal", "skilled", "review"]
"""

_WORK = """\
<!-- wio
id = "k3m9xq"
roots = ["api"]
-->

# Demo

Deliver the feature.
"""

_RULESET = """\
[families]
ARC = "Architecture"
EXC = "Excluded"
"""

_RULE_ARC = """\
<!-- wio
code = "ARC001"
name = "use-ports"
-->

Keep ports typed.
"""

_RULE_ARC2 = """\
<!-- wio
code = "ARC002"
name = "small-functions"
-->

Keep functions small.
"""

_RULE_EXC = """\
<!-- wio
code = "EXC001"
name = "skipped"
-->

This rule is excluded.
"""


def _setup_project(wio: Wio, sandbox: Sandbox, log_home: Path) -> None:
    """Populate a repository with a Work, skill, goal/gate stages, and rules.

    Args:
        wio: The scenario's facade.
        sandbox: The scenario's sandbox.
        log_home: Directory for `$WIO_HOME`.
    """
    wio.fixture("context/unreadable")
    wio.put(".agents/wio/config.toml", _CONFIG.encode("utf-8"))
    wio.put(".agents/wio/works/demo/README.md", _WORK.encode("utf-8"))
    wio.put(".agents/skills/example/SKILL.md", b"Secret skill instructions.\n")
    wio.put(".agents/wio/rules/demo/ruleset.toml", _RULESET.encode("utf-8"))
    wio.put(".agents/wio/rules/demo/ARC001-use-ports.md", _RULE_ARC.encode("utf-8"))
    wio.put(
        ".agents/wio/rules/demo/ARC002-small-functions.md",
        _RULE_ARC2.encode("utf-8"),
    )
    wio.put(".agents/wio/rules/demo/EXC001-skipped.md", _RULE_EXC.encode("utf-8"))
    sandbox.env["WIO_HOME"] = str(log_home)


@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
def test_one_command_gives_a_stage_its_context(
    wio: Wio, sandbox: Sandbox, tmp_path: Path
) -> None:
    """AC-1: goal and skill stages print all bundle sections in order and exit 0."""
    # Given a project with a goal stage, a skill stage, a Work, and rules
    _setup_project(wio, sandbox, tmp_path / "home")

    # When `wio context` runs for the goal stage and for the skill stage
    goal = wio.run(["context", "k3m9xq", "deliver", "goal"])
    skilled = wio.run(["context", "k3m9xq", "deliver", "skilled"])

    # Then both exit 0 and print metadata, header, stage, contract, rules, closing
    assert (goal.exit_code, goal.stderr) == (0, "")
    assert (skilled.exit_code, skilled.stderr) == (0, "")
    for out, marker in [
        (goal.stdout, "Write the code."),
        (skilled.stdout, "`.agents/skills/example/SKILL.md`"),
    ]:
        positions = [
            out.index("bundle: "),
            out.index("work: k3m9xq (Demo)"),
            out.index("--- stage ---"),
            out.index(marker),
            out.index("--- contract ---"),
            out.index("--- rules ---"),
            out.index("demo.ARC001 use-ports"),
            out.index("If your context was compacted"),
        ]
        assert positions == sorted(positions)
    assert "Secret skill instructions." not in skilled.stdout


@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
def test_the_same_inputs_give_the_same_bytes(
    wio: Wio, sandbox: Sandbox, tmp_path: Path
) -> None:
    """AC-2: repeated runs and reordered config tables match the golden file."""
    # Given the project of AC-1 and its golden bundle
    _setup_project(wio, sandbox, tmp_path / "home")
    expected = _GOLDEN.read_text(encoding="utf-8")

    # When `wio context` runs, then runs again with config tables reordered
    first = wio.run(["context", "k3m9xq", "deliver", "goal"])
    wio.put(".agents/wio/config.toml", _CONFIG_REORDERED.encode("utf-8"))
    second = wio.run(["context", "k3m9xq", "deliver", "goal"])

    # Then both outputs equal the golden file byte for byte
    assert (first.exit_code, second.exit_code) == (0, 0)
    assert first.stdout == expected
    assert second.stdout == expected


@pytest.mark.channels(Channel.IN_PROCESS)
def test_a_change_to_any_input_shows_in_the_bundle_id(
    wio: Wio, sandbox: Sandbox, tmp_path: Path
) -> None:
    """AC-3: changing goal, contract, rule, or skill changes id; --output does not."""
    # Given the baseline goal and skill bundles
    _setup_project(wio, sandbox, tmp_path / "home")
    sandbox.env["TMPDIR"] = str(tmp_path / "tmp")
    base_goal = wio.run(["context", "k3m9xq", "deliver", "goal"]).stdout
    base_id = base_goal.splitlines()[0].removeprefix("bundle: ")
    base_skill_id = (
        wio.run(["context", "k3m9xq", "deliver", "skilled"])
        .stdout.splitlines()[0]
        .removeprefix("bundle: ")
    )

    # When --output runs unchanged, then each of the four inputs changes one at a time
    out_run = wio.run(["context", "k3m9xq", "deliver", "goal", "--output"])
    file_id = (
        Path(out_run.stdout.strip())
        .read_text(encoding="utf-8")
        .splitlines()[0]
        .removeprefix("bundle: ")
    )

    wio.put(
        ".agents/wio/config.toml",
        _CONFIG.replace("Write the code.", "Write better code.").encode("utf-8"),
    )
    goal_changed = (
        wio.run(["context", "k3m9xq", "deliver", "goal"])
        .stdout.splitlines()[0]
        .removeprefix("bundle: ")
    )
    wio.put(".agents/wio/config.toml", _CONFIG.encode("utf-8"))

    wio.put(
        ".agents/wio/works/demo/README.md",
        _WORK.replace("Deliver the feature.", "Deliver more.").encode("utf-8"),
    )
    contract_changed = (
        wio.run(["context", "k3m9xq", "deliver", "goal"])
        .stdout.splitlines()[0]
        .removeprefix("bundle: ")
    )
    wio.put(".agents/wio/works/demo/README.md", _WORK.encode("utf-8"))

    wio.put(
        ".agents/wio/rules/demo/ARC001-use-ports.md",
        _RULE_ARC.replace("Keep ports typed.", "Keep ports strict.").encode("utf-8"),
    )
    rule_changed = (
        wio.run(["context", "k3m9xq", "deliver", "goal"])
        .stdout.splitlines()[0]
        .removeprefix("bundle: ")
    )

    wio.put(".agents/skills/example/SKILL.md", b"Updated skill instructions.\n")
    skill_changed = (
        wio.run(["context", "k3m9xq", "deliver", "skilled"])
        .stdout.splitlines()[0]
        .removeprefix("bundle: ")
    )

    # Then --output keeps the same id and every input change produces a new id
    assert file_id == base_id
    assert base_id not in {goal_changed, contract_changed, rule_changed}
    assert skill_changed != base_skill_id


@pytest.mark.channels(Channel.IN_PROCESS)
def test_a_questionable_choice_never_blocks(
    wio: Wio, sandbox: Sandbox, tmp_path: Path
) -> None:
    """AC-4: outside-pipeline, no-roots, and oversized-bundle warn and exit 0."""
    # Given a project with an extra off-pipeline stage and a no-roots Work
    _setup_project(wio, sandbox, tmp_path / "home")
    extra = _CONFIG + '\n[stages.extra]\ngoal = "Extra."\n'
    wio.put(".agents/wio/config.toml", extra.encode("utf-8"))
    wio.put(
        ".agents/wio/works/noroot/README.md",
        b'<!-- wio\nid = "n0r00t"\n-->\n\n# No Roots\n',
    )

    # When each questionable case runs, and the sized case runs without threshold
    off_pipe = wio.run(["context", "k3m9xq", "deliver", "extra"])
    no_roots = wio.run(["context", "n0r00t", "deliver", "goal"])
    plain = wio.run(["context", "k3m9xq", "deliver", "goal"])
    wio.put(
        ".agents/wio/config.toml",
        ("[bundle]\nsize_threshold = 1\n" + extra).encode("utf-8"),
    )
    oversized = wio.run(["context", "k3m9xq", "deliver", "goal"])

    # Then all exit 0 with warnings on stderr, and the threshold leaves bundle intact
    assert (
        off_pipe.exit_code,
        no_roots.exit_code,
        oversized.exit_code,
    ) == (0, 0, 0)
    assert off_pipe.stderr.startswith("warning: ")
    assert no_roots.stderr.startswith("warning: ")
    assert oversized.stderr.startswith("warning: ")
    assert oversized.stdout == plain.stdout


@pytest.mark.channels(Channel.IN_PROCESS)
def test_an_unknown_input_produces_no_bundle_and_no_event(
    wio: Wio, sandbox: Sandbox, tmp_path: Path
) -> None:
    """AC-5: unknown work, action, stage, or Work root exits 2 with no event."""
    # Given a project and a Work naming an undeclared root
    log_home = tmp_path / "home"
    _setup_project(wio, sandbox, log_home)
    wio.put(
        ".agents/wio/works/bad/README.md",
        b'<!-- wio\nid = "bad001"\nroots = ["ghost"]\n-->\n\n# Bad\n',
    )

    # When `wio context` runs for each of the four unknown inputs
    results = [
        wio.run(["context", "nosuch", "deliver", "goal"]),
        wio.run(["context", "k3m9xq", "nosuch", "goal"]),
        wio.run(["context", "k3m9xq", "deliver", "nosuch"]),
        wio.run(["context", "bad001", "deliver", "goal"]),
    ]

    # Then every run exits 2, prints no bundle, and writes no event
    for result in results:
        assert (result.exit_code, result.stdout) == (2, "")
    assert read_events(log_home) == []


@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
def test_a_file_holds_the_same_bundle(
    wio: Wio, sandbox: Sandbox, tmp_path: Path
) -> None:
    """AC-6: `--output` and `--output <path>` write the golden bytes and print path."""
    # Given the project of AC-1 and an external temporary directory
    _setup_project(wio, sandbox, tmp_path / "home")
    sandbox.env["TMPDIR"] = str(tmp_path / "tmp")
    expected = _GOLDEN.read_text(encoding="utf-8")
    named = tmp_path / "chosen.md"

    # When `wio context` runs with `--output` and `--output <path>`
    default_run = wio.run(["context", "k3m9xq", "deliver", "goal", "--output"])
    named_run = wio.run(
        ["context", "k3m9xq", "deliver", "goal", "--output", str(named)]
    )

    # Then both exit 0, print their path, and write the exact golden bytes
    assert (default_run.exit_code, named_run.exit_code) == (0, 0)
    default_path = Path(default_run.stdout.strip())
    assert default_path.read_text(encoding="utf-8") == expected
    assert named_run.stdout == f"{named}\n"
    assert named.read_text(encoding="utf-8") == expected


@pytest.mark.channels(Channel.CLI)
def test_a_stage_entry_is_recorded_for_plain_and_gate_stages(
    wio: Wio, sandbox: Sandbox, tmp_path: Path
) -> None:
    """AC-7: plain and gate runs record matching ids, ordered rules, and gate fields."""
    # Given a committed repository with two real rules, a plain stage, and a gate stage
    log_home = tmp_path / "home"
    _setup_project(wio, sandbox, log_home)
    wio.commit("feat: baseline\n\nWio-Work: none")
    head_sha = wio.driver.git(["rev-parse", "HEAD"]).stdout.strip()

    # When `wio context` runs for the plain stage and for the gate stage
    plain = wio.run(["context", "k3m9xq", "deliver", "goal"])
    gate = wio.run(["context", "k3m9xq", "deliver", "review"])

    # Then two events exist with matching ids, ordered rule hashes, and gate fields
    assert (plain.exit_code, gate.exit_code) == (0, 0)
    plain_id = plain.stdout.splitlines()[0].removeprefix("bundle: ")
    gate_id = gate.stdout.splitlines()[0].removeprefix("bundle: ")
    ev_plain, ev_gate = read_events(log_home)
    assert ev_plain["bundle"] == plain_id
    assert list(ev_plain["rules"]) == ["demo.ARC001", "demo.ARC002"]
    assert "start" not in ev_plain
    assert "dirty" not in ev_plain
    assert ev_gate["bundle"] == gate_id
    assert list(ev_gate["rules"]) == ["demo.ARC001", "demo.ARC002"]
    assert ev_gate["start"] == head_sha
    assert ev_gate["dirty"] is False


@pytest.mark.channels(Channel.IN_PROCESS)
def test_a_run_leaves_the_worktree_as_it_found_it(
    wio: Wio, sandbox: Sandbox, tmp_path: Path
) -> None:
    """AC-8: stdout and external `--output` runs leave the worktree unchanged."""
    # Given a project, external WIO_HOME, and a fingerprint of the worktree
    _setup_project(wio, sandbox, tmp_path / "home")
    before = wio.fingerprint(".")
    external = tmp_path / "outside.md"

    # When `wio context` runs without `--output`, then with an external `--output`
    first = wio.run(["context", "k3m9xq", "deliver", "goal"])
    second = wio.run(
        ["context", "k3m9xq", "deliver", "goal", "--output", str(external)]
    )

    # Then the worktree is unchanged after both runs and the external file exists
    assert (first.exit_code, second.exit_code) == (0, 0)
    assert wio.fingerprint(".") == before
    assert external.read_text(encoding="utf-8") == first.stdout


@pytest.mark.channels(Channel.IN_PROCESS)
def test_the_rules_are_those_that_wio_rules_list_shows(
    wio: Wio, sandbox: Sandbox, tmp_path: Path
) -> None:
    """AC-9: the bundle's rules match the included rules of `wio rules list`."""
    # Given a project with included and excluded rules
    _setup_project(wio, sandbox, tmp_path / "home")

    # When `wio rules list --json` and `wio context` run for the same Work and stage
    listed = wio.run(["rules", "list", "--work", "k3m9xq", "--stage", "goal", "--json"])
    bundle = wio.run(["context", "k3m9xq", "deliver", "goal"])

    # Then the bundle's rules section holds exactly the included rule codes
    assert (listed.exit_code, bundle.exit_code) == (0, 0)
    payload = json.loads(listed.stdout)
    included = [item["code"] for item in payload["rules"] if item["included"]]
    rules_section = bundle.stdout.split("--- rules ---", 1)[1]
    assert included == ["demo.ARC001", "demo.ARC002"]
    for code in included:
        assert rules_section.count(code) == 1
    assert "demo.EXC001" not in rules_section


@pytest.mark.channels(Channel.IN_PROCESS)
def test_all_seven_warnings_come_in_exact_order(
    wio: Wio, sandbox: Sandbox, tmp_path: Path
) -> None:
    """AC-10: pipeline, roots, size, worktree, start, dirty, and event log in order."""
    # Given a Work with no roots, an off-pipeline gate, tiny threshold, inside output,
    # failing history/repository ports, and an unwritable event log
    log_home = tmp_path / "home"
    _setup_project(wio, sandbox, log_home)
    wio.put(
        ".agents/wio/config.toml",
        (
            "[bundle]\nsize_threshold = 1\n"
            + _CONFIG
            + '\n[stages.offgate]\ngoal = "Off gate."\ngate = true\n'
        ).encode("utf-8"),
    )
    wio.put(
        ".agents/wio/works/noroot/README.md",
        b'<!-- wio\nid = "n0r00t"\n-->\n\n# No Roots\n',
    )
    # Seed the clone log directory and replace events.jsonl with a directory.
    seed = wio.run(["context", "k3m9xq", "deliver", "goal"])
    assert seed.exit_code == 0
    (events_file,) = list(log_home.rglob("events.jsonl"))
    events_file.unlink()
    events_file.mkdir()

    # When `wio context` runs for the off-pipeline gate with `--output inside.md`
    with gate_port_states(
        commits=ValueError("bad history"), dirty=RuntimeError("bad repo")
    ):
        result = wio.run(
            ["context", "n0r00t", "deliver", "offgate", "--output", "inside.md"]
        )

    # Then stderr holds all seven warnings in exact order and exit code is 0
    assert result.exit_code == 0
    lines = result.stderr.splitlines()
    assert len(lines) == 7
    assert all(line.startswith("warning: ") for line in lines)
    assert "pipeline" in lines[0]
    assert "roots" in lines[1]
    assert "Bundle body size" in lines[2]
    assert "committed by mistake" in lines[3]
    assert "start" in lines[4]
    assert "dirty" in lines[5]
    assert "the event log could not be written" in lines[6]
