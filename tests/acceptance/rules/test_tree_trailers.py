# SPDX-License-Identifier: Apache-2.0
"""System scenarios of `wio trailers` citing the rules that a stage selects.

They use the project of `tests/acceptance/trailers/test_command.py`, with a root
`api`, a ruleset `demo` and a gate that selects `demo.ARC001`, and run on the CLI
channel only, because the write form finds the reviewed commit in a git repository.
"""

import json
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from tests.acceptance.channels import Channel
from tests.acceptance.rules.support import RULES, rule

if TYPE_CHECKING:
    from tests.acceptance.dsl.wio import Wio
    from tests.sandbox import Sandbox

WORK = "Wio-Work: k3m9xq\nWio-Action: deliver\nWio-Stage: architecture"
GATE = (
    "Wio-Work: k3m9xq\nWio-Action: deliver\nWio-Stage: architecture-review\n"
    "Wio-Result: pass\nWio-Judge: human"
)
GATE_ARGS = ["trailers", "k3m9xq", "deliver", "architecture-review"]
PASS = ["--result", "pass", "--judge", "human"]
CONFIG = """\
[actions.deliver]
description = "Build what the Work says."

[roots.api]
paths = ["src"]
rule_presets = ["demo.all"]

[stages.architecture]
goal = "Write the boundaries."

[stages.architecture-review]
gate = true
judge = "human"
goal = "Judge the boundaries."
rules_include = ["demo.ARC001"]

[templates.kinds]
feature = "t.leaf"
"""


def _work(roots: str) -> bytes:
    """Write the contract of the Work.

    Args:
        roots: The `roots` line of its metadata block, or an empty string.

    Returns:
        The bytes of the contract.
    """
    block = f'<!-- wio\nid = "k3m9xq"\ntemplate = "t.leaf"\n{roots}-->\n'
    return (
        block + "\n# A Work\n\n## Acceptance criteria\n\n### **AC-1** One\n"
    ).encode()


def _project(wio: Wio, *, roots: str) -> None:
    """Commit the project with its rules, a work commit and a pure gate commit.

    Args:
        wio: The facade.
        roots: The `roots` line of the Work.
    """
    wio.fixture("trailers/command")
    wio.put(".agents/wio/config.toml", CONFIG.encode())
    wio.put(".agents/wio/works/k3m9xq/README.md", _work(roots))
    wio.put(f"{RULES}/demo/ruleset.toml", b'[families]\nARC = "A"\n')
    wio.put(f"{RULES}/demo/ARC001-keep.md", rule("ARC001", "keep", "Keep it.\n"))
    wio.commit("feat: add the Work")
    wio.put("note.txt", b"x\n")
    wio.commit(f"feat: add x\n\n{WORK}")
    wio.commit(f"chore: judge\n\n{GATE}", empty=True)


def _hashes(sandbox: Sandbox) -> list[dict[str, str]]:
    """Read the hashes of the rules that the recorded events hold.

    Args:
        sandbox: Supplies the Wio home.

    Returns:
        The hash of each rule of each event that holds some, in file order.
    """
    found: list[dict[str, str]] = []
    for path in sorted((Path(sandbox.env["WIO_HOME"]) / "log").rglob("*.jsonl")):
        for line in path.read_text().splitlines():
            event = json.loads(line)
            if event.get("hashes"):
                found.append(event["hashes"])
    return found


@pytest.mark.channels(Channel.CLI)
def test_a_cited_rule_is_hashed_and_one_the_stage_does_not_select_is_refused(
    wio: Wio, sandbox: Sandbox
) -> None:
    """AC-10: the hash of `demo.ARC001`, a new hash after an edit, then a refusal."""
    # Given a commit that holds the rule files and a Work whose roots list `api`,
    # and a gate that selects `demo.ARC001`
    _project(wio, roots='roots = ["api"]\n')

    # When the citation runs, the file of the rule is edited and committed and the
    # citation runs again, and then `demo.ARC999` is cited
    first = wio.run([*GATE_ARGS, *PASS, "--cite", "demo.ARC001=pass"])
    wio.put(f"{RULES}/demo/ARC001-keep.md", rule("ARC001", "keep", "Keep it more.\n"))
    wio.commit(f"feat: edit the rule\n\n{WORK}")
    wio.commit(f"chore: judge\n\n{GATE}", empty=True)
    second = wio.run([*GATE_ARGS, *PASS, "--cite", "demo.ARC001=pass"])
    third = wio.run([*GATE_ARGS, *PASS, "--cite", "demo.ARC999=pass"])

    # Then the first is accepted and its event holds a hash for `demo.ARC001`, the
    # second holds a different hash, and the third prints nothing on standard output,
    # writes no event and exits 1
    assert (first.exit_code, second.exit_code) == (0, 0)
    hashes = _hashes(sandbox)
    assert [list(h) for h in hashes] == [["demo.ARC001"], ["demo.ARC001"]]
    assert hashes[0] != hashes[1]
    assert (third.exit_code, third.stdout) == (1, "")
    assert "demo.ARC999" in third.stderr
    assert len(_hashes(sandbox)) == 2


@pytest.mark.channels(Channel.CLI)
def test_a_work_without_roots_cites_no_rule(wio: Wio) -> None:
    """AC-10: the review is accepted, and a cite is refused for a Work without roots."""
    # Given a Work that lists no roots, and a gate with no `roots`
    _project(wio, roots="")

    # When the review runs, and then it runs with `--cite demo.ARC001=pass`
    plain = wio.run([*GATE_ARGS, *PASS])
    cited = wio.run([*GATE_ARGS, *PASS, "--cite", "demo.ARC001=pass"])

    # Then the first is accepted and cites no rule, and the second prints nothing on
    # standard output, writes no event and exits 1
    assert (plain.exit_code, plain.stdout) == (0, f"{GATE}\n")
    assert (cited.exit_code, cited.stdout) == (1, "")
