# SPDX-License-Identifier: Apache-2.0
"""System scenarios for the order of context input checks."""

from types import SimpleNamespace
from typing import TYPE_CHECKING

import pytest

from tests.acceptance.channels import Channel

if TYPE_CHECKING:
    from tests.acceptance.dsl.wio import Wio


@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
def test_refusals_are_judged_in_order(wio: Wio) -> None:
    """AC-1: removing each fault exposes the next refusal."""
    # Given a nested repository with all seven faults
    wio.fixture("context/unreadable")
    config_path = ".agents/wio/config.toml"
    config = wio.read(config_path) + b'[works]\nhierarchy = "nesting"\n'
    wio.put(config_path, b"mistyped = 1\n" + config)
    pair = ".agents/wio/works/pair/"
    wio.put(pair + "README.md", b'<!-- wio\nid = "a1b2c3"\n-->\n')
    wio.put(pair + "other.md", b'<!-- wio\nid = "d4e5f6"\n-->\n')
    work = ".agents/wio/works/demo/README.md"
    wio.put(work, b'<!-- wio\nid = "k3m9xq"\nroots = ["ghost"]\n-->\n\n# Demo\n')
    rules = ".agents/wio/rules/demo/"
    wio.put(rules + "ruleset.toml", b'[families]\nARC = "Architecture"\n')
    wio.put(
        rules + "ERR001-undeclared.md",
        b'<!-- wio\ncode = "ERR001"\nname = "undeclared"\n-->\n\nText.\n',
    )
    args = ["context", "nope11", "delivr", "missing-stage"]

    # When each reported fault is removed before the next run
    results = [wio.run(args)]
    wio.put(config_path, config)
    results.append(wio.run(args))
    wio.put(pair + "other.md", b"Unmarked.\n")
    results.append(wio.run(args))
    args[1] = "k3m9xq"
    results.append(wio.run(args))
    args[2] = "deliver"
    results.append(wio.run(args))
    args[3] = "implementation"
    results.append(wio.run(args))
    wio.put(work, b'<!-- wio\nid = "k3m9xq"\nroots = ["api"]\n-->\n\n# Demo\n')
    results.append(wio.run(args))

    # Then every refusal names the first remaining fault and prints no bundle
    expected = [
        ("mistyped",),
        ("pair/README.md", "pair/other.md"),
        ("nope11",),
        ("delivr",),
        ("missing-stage",),
        ("ghost",),
        ("demo/ERR001-undeclared.md",),
    ]
    for result, names in zip(results, expected, strict=True):
        assert (result.exit_code, result.stdout) == (2, "")
        assert all(name in result.stderr for name in names)


def test_both_warnings_are_reported_with_a_fixed_bundle(
    wio: Wio, monkeypatch: pytest.MonkeyPatch
) -> None:
    """AC-2: real checks report both warnings before a fixed bundle."""
    # Given a fixed composition and a Work with no roots outside its pipeline
    wio.fixture("context/pipeline")
    path = ".agents/wio/works/list/README.md"
    wio.put(path, wio.read(path).replace(b'roots = ["api"]', b"roots = []"))
    bundle = SimpleNamespace(text="fixed bundle\n", id="fixed", size=0, rules={})

    def compose(*_args: object) -> SimpleNamespace:
        """Return the fixed bundle for any request."""
        return bundle

    monkeypatch.setattr("wio.context.Composition.compose", compose)

    # When the stage runs through the real checks
    result = wio.run(["context", "a1b2c3", "deliver", "define"])

    # Then the fixed bundle and both warnings appear once, in order
    assert (result.exit_code, result.stdout) == (0, "fixed bundle\n")
    lines = result.stderr.splitlines()
    assert len(lines) == 2
    assert "`define`" in lines[0]
    assert "pipeline" in lines[0]
    assert "no roots" in lines[1]
