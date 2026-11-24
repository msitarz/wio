# SPDX-License-Identifier: Apache-2.0
"""System tests of the rule files: the readers and the discovery together."""

from tests.unit.fakes import ROOT, MemoryFileSystem
from wio.models.config import RulePreset
from wio.rules import discover

RULES = ROOT / ".agents" / "wio" / "rules"
_REL = ".agents/wio/rules"


def test_the_rulesets_are_discovered_with_their_rules() -> None:
    """AC-1: both block forms, any depth, the order and the finders."""
    # Given `demo` with a described rule, a `+++` rule with no body, a rule in a
    # subdirectory, a README and a text file, and `other` with one rule
    demo = RULES / "demo"
    comment = (
        '<!-- wio\ncode = "ARC001"\nname = "keep-it-small"\n'
        'description = "Small things."\n-->\n\nKeep it small.\n'
    )
    front = '+++\nwio = 1\ncode = "PAY001"\nname = "pay-first"\n+++\n'
    nested = '<!-- wio\ncode = "ARC002"\nname = "name-things"\n-->\n\nNames.\n'
    other = '<!-- wio\ncode = "ARC001"\nname = "other-rule"\n-->\n\nOther.\n'
    files = {
        demo / "ruleset.toml": (
            'description = "Demo rules."\n[families]\nARC = "Architecture"\n'
            'PAY = "Payments"\n[rule_presets.small]\nrules_include = ["ARC"]\n'
        ),
        demo / "ARC001-keep-it-small.md": comment,
        demo / "PAY001-pay-first.md": front,
        demo / "arc" / "ARC002-name-things.md": nested,
        demo / "README.md": "# Demo\n\nNot a rule.\n",
        demo / "notes.txt": "not markdown",
        RULES / "other" / "ruleset.toml": '[families]\nARC = "Architecture"\n',
        RULES / "other" / "ARC001-other-rule.md": other,
    }

    # When the discovery runs
    found = discover(ROOT, MemoryFileSystem(files))

    # Then it returns `other` and `demo` by name, `demo`'s manifest and rules in
    # the order of family and code, and no diagnostic
    assert found.diagnostics == ()
    assert [r.name for r in found.rulesets] == ["demo", "other"]
    first = found.rulesets[0]
    assert first.manifest.description == "Demo rules."
    assert dict(first.manifest.families) == {"ARC": "Architecture", "PAY": "Payments"}
    assert first.manifest.rule_presets["small"] == RulePreset(("ARC",), ())
    assert [r.code for r in first.rules] == ["ARC001", "ARC002", "PAY001"]
    assert [r.code for r in first.rules_of("ARC")] == ["ARC001", "ARC002"]
    assert [r.code for r in first.rules_of("PAY")] == ["PAY001"]
    keep, _, pay = first.rules
    assert (keep.description, keep.summary, keep.body) == (
        "Small things.",
        "Keep it small.",
        "Keep it small.",
    )
    assert (pay.description, pay.summary, pay.body) == (None, "", "")
    assert [r.code for r in found.rulesets[1].rules] == ["ARC001"]


def test_the_faults_are_reported_together_and_the_rest_is_read() -> None:
    """AC-2: three errors, the faulty parts left out, the valid rest returned."""
    # Given a rule whose block does not close, a manifest that does not parse, a
    # stray rule file and a valid ruleset
    ok = '<!-- wio\ncode = "ARC001"\nname = "fine"\n-->\n\nFine.\n'
    files = {
        RULES / "demo" / "ruleset.toml": '[families]\nARC = "Topic"\n',
        RULES / "demo" / "ARC001-fine.md": ok,
        RULES / "demo" / "ARC002-open.md": '<!-- wio\ncode = "ARC002"\n',
        RULES / "broken" / "ruleset.toml": "[families\n",
        RULES / "stray.md": ok,
        RULES / "other" / "ruleset.toml": '[families]\nARC = "Topic"\n',
        RULES / "other" / "ARC001-fine.md": ok,
    }

    # When the discovery runs
    found = discover(ROOT, MemoryFileSystem(files))

    # Then it reports the three errors at their places, returns `demo` with
    # `ARC001` only and `other` whole, and not `broken`
    assert [(d.severity, d.where) for d in found.diagnostics] == [
        ("error", f"{_REL}/broken/ruleset.toml:1"),
        ("error", f"{_REL}/demo/ARC002-open.md:1"),
        ("error", f"{_REL}/stray.md"),
    ]
    assert [r.name for r in found.rulesets] == ["demo", "other"]
    assert [r.code for r in found.rulesets[0].rules] == ["ARC001"]
    assert [r.code for r in found.rulesets[1].rules] == ["ARC001"]
