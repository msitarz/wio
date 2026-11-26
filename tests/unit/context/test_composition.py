# SPDX-License-Identifier: Apache-2.0
"""Check context composition against the Work contract.

The scenarios use the real bundle builders with in-memory ports.
"""

from pathlib import Path, PurePosixPath
from typing import TYPE_CHECKING

import pytest

from tests.unit.context.fakes import (
    ContractStub,
    RuleFiles,
    SelectionFake,
    SettingsStub,
    SkillsFake,
    TopicsStub,
)
from tests.unit.context.support import applies, left_out
from tests.unit.fakes import ROOT, FakeRepository
from wio.context.assembly import assemble
from wio.context.composition import Composition
from wio.context.heading import header
from wio.context.identity import bundle_id
from wio.errors import DiagnosticsError, WioError
from wio.formats.digest import rule_hash
from wio.models.config import Config, Root, Stage
from wio.models.frozen import freeze
from wio.models.resolved import ResolvedContract
from wio.models.rule import Rule
from wio.models.skill import FoundSkill
from wio.models.works import Work

if TYPE_CHECKING:
    from wio.context.ports import Composer
    from wio.models.rules import Selection

pytestmark = pytest.mark.xfail(strict=True, raises=NotImplementedError)

_WORK = Work("k3m9xq", "Demo", Path("work.md"), None, ("api",), (), freeze({}))
_CONTRACT = ResolvedContract(_WORK, "# Démo\n\nContract text.", ())
_VIEW = "# Inherited constraints\n\nRègles.\n\n" + _CONTRACT.own
_GOAL = Stage(goal="Review café.")
_PROCESS = Rule(
    "process",
    "FIX001",
    "fix-the-cause",
    None,
    "Fix it.",
    "Fix it.",
    1,
    PurePosixPath("process.md"),
)
_PYTHON = Rule(
    "python",
    "API001",
    "type-ports",
    None,
    "Type ports.",
    "Type ports.",
    1,
    PurePosixPath("python.md"),
)


def _wire(
    selection: SelectionFake,
    stage: Stage = _GOAL,
    *,
    skills: SkillsFake | None = None,
    files: RuleFiles | None = None,
) -> Composer:
    """Connect composition to in-memory services for a review stage.

    Args:
        selection: The rule selection or failure for the stage.
        stage: The requested stage's settings.
        skills: An optional prepared lookup.
        files: Optional file contents and failures.

    Returns:
        A composer for the prepared Work and stage.
    """
    settings = SettingsStub(
        Config(stages=freeze({"review": stage}), roots=freeze({"api": Root(paths=())}))
    )
    return Composition(
        ContractStub(_CONTRACT, _VIEW),
        selection,
        TopicsStub(),
        skills if skills is not None else SkillsFake(None),
        settings,
        FakeRepository(),
        files if files is not None else _rule_files(),
    )


def _rule_files() -> RuleFiles:
    """Prepare identifiable file bytes for the rules.

    Returns:
        The repository's two rule files with distinct contents.
    """
    return RuleFiles(
        data={
            ROOT / _PROCESS.path: b"Process\n",
            ROOT / _PYTHON.path: b"Python\xff\r\n",
        }
    )


def _both_rules() -> Selection:
    """Select both rules with the root-dependent rule first.

    Returns:
        A selection whose insertion and print orders differ.
    """
    return {_PYTHON: applies("api"), _PROCESS: applies()}


def test_bundle_has_the_rendered_parts_id_and_size() -> None:
    """Assemble the expected parts and report the identity of the printed text.

    The body includes multibyte text so the byte count differs from its length.
    """
    # Given a goal, a resolved view and two included rules
    composer = _wire(SelectionFake(_both_rules()))
    rules = (
        "Rules for every root:\n\nprocess: Process (FIX)\n\n"
        "process.FIX001 fix-the-cause\nFix it.\n\n"
        "Rules for root api:\n\npython: Python API (API)\n\n"
        "python.API001 type-ports\nType ports."
    )

    def header_for(size: int, lines: int) -> str:
        """Build the expected header from the assembly's body measurements.

        Args:
            size: The UTF-8 byte count.
            lines: The newline count.

        Returns:
            The expected stage header.
        """
        return header(
            "k3m9xq", "Demo", "deliver", "review", _GOAL, 2, size, lines, None
        )

    # When the bundle is composed
    bundle = composer.compose("k3m9xq", "deliver", "review")
    metadata, _, text = bundle.text.partition("\n\n")
    heading, _, body = text.partition("\n\n")
    lines = body.count("\n")

    # Then real assembly gives the same text and the counts match the body
    assert bundle.text == assemble("Review café.", _VIEW, rules, header_for)
    assert metadata == f"bundle: {bundle.id}"
    assert bundle.id == bundle_id(text)
    assert bundle.size == len(body.encode("utf-8"))
    assert "rules: 2" in heading.splitlines()
    assert f"size: {bundle.size} bytes, {lines} lines (body)" in heading


def test_rule_hashes_follow_the_print_order() -> None:
    """Keep the hashes in print order with the bytes of each rule file.

    The selection inserts the root-dependent rule before the independent rule.
    """
    # Given two selected rules in selection order and their file contents
    composer = _wire(SelectionFake(_both_rules()))

    # When the bundle is composed
    bundle = composer.compose("k3m9xq", "deliver", "review")

    # Then the recorded identities follow the print order
    assert list(bundle.rules.items()) == [
        ("process.FIX001", rule_hash(b"Process\n")),
        ("python.API001", rule_hash(b"Python\xff\r\n")),
    ]


def test_selection_is_asked_once() -> None:
    """Request the stage's rules once for its resolved contract.

    One selection supplies the printed rules and the recorded identities.
    """
    # Given a selection port that records its requests
    selection = SelectionFake(_both_rules())
    composer = _wire(selection)

    # When the bundle is composed
    composer.compose("k3m9xq", "deliver", "review")

    # Then exactly one request names that resolved contract and stage
    assert selection.calls == [(_CONTRACT, "review")]


@pytest.mark.parametrize("included", [True, False], ids=["one-rule", "no-rules"])
def test_only_included_rules_are_printed_and_recorded(*, included: bool) -> None:
    """Keep excluded rules out of both the text and the recorded identities.

    Args:
        included: Whether the independent rule is included.
    """
    # Given one excluded rule and a decision for the other rule
    decision = applies() if included else left_out("not-selected")
    files = _rule_files()
    composer = _wire(
        SelectionFake({_PROCESS: decision, _PYTHON: left_out("excluded")}), files=files
    )

    # When the bundle is composed
    bundle = composer.compose("k3m9xq", "deliver", "review")

    # Then only the included rule appears and only its file is read
    assert "python.API001" not in bundle.text
    assert ("process.FIX001" in bundle.text) is included
    assert tuple(bundle.rules) == (("process.FIX001",) if included else ())
    assert f"rules: {int(included)}" in bundle.text.splitlines()
    assert files.calls == ([("read_bytes", ROOT / _PROCESS.path)] if included else [])


@pytest.mark.parametrize(
    ("name", "directory", "shown_name", "shown_directory"),
    [
        ("demo", "team/skills/demo", "demo", "team/skills/demo"),
        (
            "demo\nnow",
            "team\\skills/demo\rnow",
            r"demo\nnow",
            r"team\\skills/demo\rnow",
        ),
    ],
)
def test_skill_pointer_and_header_share_one_lookup(
    name: str, directory: str, shown_name: str, shown_directory: str
) -> None:
    """Use the same skill lookup for the displayed pointer and header.

    Args:
        name: The configured skill name.
        directory: The directory found by the lookup.
        shown_name: The skill name displayed in the header.
        shown_directory: The directory displayed in the header and guidance.
    """
    # Given a skill stage and a goal stage with observable lookup calls
    found = FoundSkill(directory, "a" * 64)
    skill_lookup = SkillsFake(found)
    goal_lookup = SkillsFake(found)
    skill = _wire(SelectionFake({}), Stage(skill=name), skills=skill_lookup)
    goal = _wire(SelectionFake({}), skills=goal_lookup)

    # When each bundle is composed
    skill_bundle = skill.compose("k3m9xq", "deliver", "review")
    goal_bundle = goal.compose("k3m9xq", "deliver", "review")

    # Then the skill is looked up once and its directory agrees in both places
    assert skill_lookup.calls == [name]
    assert goal_lookup.calls == []
    assert (
        f"skill: {shown_name} ({shown_directory}, files {found.files_hash})"
        in skill_bundle.text.splitlines()
    )
    assert f"`{shown_directory}/SKILL.md`" in skill_bundle.text
    assert not any(line.startswith("skill: ") for line in goal_bundle.text.splitlines())


def test_rule_discovery_failure_is_propagated_before_file_reads() -> None:
    """Preserve the rule discovery error without hashing any files.

    The error's diagnostics remain available to the caller.
    """
    # Given rule discovery has failed
    failure = DiagnosticsError("Rule discovery failed.")
    files = _rule_files()
    composer = _wire(SelectionFake(failure), files=files)

    # When the bundle is composed
    with pytest.raises(DiagnosticsError) as error:
        composer.compose("k3m9xq", "deliver", "review")

    # Then the same error reaches the caller and no rule file was read
    assert error.value is failure
    assert files.calls == []


def test_unreadable_rule_file_names_its_path() -> None:
    """Refuse composition if the bytes of a printed rule cannot be read.

    The refusal identifies the file the reader needs to fix.
    """
    # Given one included rule whose file cannot be read
    files = RuleFiles(data={ROOT / _PROCESS.path: PermissionError("denied")})
    composer = _wire(SelectionFake({_PROCESS: applies()}), files=files)

    # When the bundle is composed
    with pytest.raises(WioError) as error:
        composer.compose("k3m9xq", "deliver", "review")

    # Then the refusal names the unreadable rule file
    assert str(_PROCESS.path) in str(error.value)


def test_header_names_the_work_and_states_the_stage_settings() -> None:
    """Show the requested stage and the Work's title in the header.

    The review stage requests a fresh session and a human gate.
    """
    # Given a titled Work and a fresh stage with a human gate
    stage = Stage(goal="Review.", gate=True, judge="human", session="fresh")
    composer = _wire(SelectionFake({}), stage)

    # When the review bundle is composed
    bundle = composer.compose("k3m9xq", "deliver", "review")
    _, _, text = bundle.text.partition("\n\n")
    lines = text.splitlines()

    # Then the header contains the Work, request and stage settings
    assert lines[:3] == ["work: k3m9xq (Demo)", "action: deliver", "stage: review"]
    assert "gate: yes, judged by a person" in lines
    assert "session: fresh" in lines


def test_missing_skill_names_the_skill_in_the_refusal() -> None:
    """Refuse to compose a bundle when a configured skill cannot be found.

    The refusal identifies the skill the reader needs to restore.
    """
    # Given a stage configured for a skill that the lookup cannot find
    composer = _wire(SelectionFake({}), Stage(skill="missing-demo"))

    # When the bundle is composed
    with pytest.raises(WioError) as error:
        composer.compose("k3m9xq", "deliver", "review")

    # Then the refusal names the missing skill
    assert "missing-demo" in str(error.value)
