# SPDX-License-Identifier: Apache-2.0
"""System-level scenarios of the `wio contracts` command as a whole."""

import json
import re
from typing import TYPE_CHECKING

import pytest

from tests.acceptance.channels import Channel

if TYPE_CHECKING:
    from tests.acceptance.dsl.results import Output
    from tests.acceptance.dsl.wio import Wio

WORKS = ".agents/wio/works"
TEMPLATES = ".agents/wio/templates"
CONFIG = """\
[works]
hierarchy = "nesting"

[templates.kinds]
feature = "feature.draft"

[roots.api]
paths = ["src"]

[actions.define]
description = "Define."

[actions.deliver]
description = "Deliver."

[stages.define]
goal = "Define."

[stages.ship]
goal = "Ship."

[stage_presets]
define-feature = ["define"]
"""
DRAFT = """\
<!-- wio
kind = "feature"
shape = "draft"

[actions]
define = "define-feature"
-->

# <Work name>

## Purpose <!-- wio: required -->

<!-- Why. -->
"""
LEAF = """\
<!-- wio
kind = "feature"
shape = "leaf"

[actions]
define = "define-feature"

[contract]
roots = []
depends_on = []
-->

# <Work name>

## Purpose <!-- wio: required -->
"""
PARENT = """\
<!-- wio
kind = "feature"
shape = "parent"

[actions]
define = "define-feature"

[contract]
roots = ["@descendants"]
depends_on = []
-->

# <Work name>

## Purpose <!-- wio: required -->

## Glossary <!-- wio: inherit -->

## Constraints <!-- wio: inherit -->

## Acceptance criteria <!-- wio: required -->
"""


def _project(wio: Wio, works: dict[str, str]) -> None:
    """Start a repository with the config, the three templates and some Works.

    Args:
        wio: The facade.
        works: The Works, by path below the Works directory.
    """
    wio.fixture("contracts/show-base")
    files = {
        ".agents/wio/config.toml": CONFIG,
        f"{TEMPLATES}/feature.draft.md": DRAFT,
        f"{TEMPLATES}/feature.leaf.md": LEAF,
        f"{TEMPLATES}/feature.parent.md": PARENT,
        **{f"{WORKS}/{path}": text for path, text in works.items()},
    }
    for path, text in files.items():
        wio.put(path, text.encode())


def _block(work_id: str, keys: str = "", template: str = "feature.leaf") -> str:
    """Write a Work with the sections of a valid leaf.

    Args:
        work_id: The Work's id.
        keys: More lines of the block.
        template: The template it follows.

    Returns:
        The text of the file.
    """
    head = f'<!-- wio\nid = "{work_id}"\ntemplate = "{template}"\n{keys}-->\n'
    return f"{head}\n# Work {work_id}\n\n## Purpose\n\nWhy.\n"


@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
def test_a_new_child_is_valid_and_inherits_what_its_parent_passes_on(wio: Wio) -> None:
    """Parent AC-2: a parent and a child."""
    # Given a repository with a Work `T` valid for `feature.parent`, with a
    # Glossary and a Constraints section
    parent = _block("t4n7vq", 'roots = ["api"]\n', "feature.parent").replace(
        "## Purpose\n\nWhy.\n",
        "## Purpose\n\nT-PURPOSE\n\n## Glossary\n\n- **Term**: T-GLOSSARY\n\n"
        "## Constraints\n\nT-CONSTRAINT\n\n## Acceptance criteria\n\nT-CRITERIA\n",
    )
    _project(wio, {"t/README.md": parent})

    # When `new feature --parent <T> --title "Child"` runs, and then `check`,
    # `list` and `show <child id>`
    made = wio.run(
        ["contracts", "new", "feature", "--parent", "t4n7vq", "--title", "Child"]
    )
    child = re.match(r"Created Work (\w{6})  Child\n", made.stdout)
    assert child
    checked = wio.run(["contracts", "check"])
    listed = wio.run(["contracts", "list"])
    shown = wio.run(["contracts", "show", child.group(1)])

    # Then `check` passes, `list` indents `Child` below `T`, and `show` prints the
    # Glossary and the Constraints of `T` as inherited sections and none of `T`'s
    # other sections
    assert (checked.stdout, checked.exit_code) == ("The contracts pass.\n", 0)
    assert f"\n  {child.group(1)}  Child" in listed.stdout
    assert "## Inherited from: Work t4n7vq (t4n7vq)" in shown.stdout
    assert "T-GLOSSARY" in shown.stdout
    assert "T-CONSTRAINT" in shown.stdout
    assert "T-PURPOSE" not in shown.stdout
    assert "T-CRITERIA" not in shown.stdout


@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
def test_a_work_moves_to_another_template_and_keeps_its_identity(wio: Wio) -> None:
    """Parent AC-3: a leaf moved to the parent template, with and without `--keep`."""
    # Given a Work `W` from `feature.leaf` with `roots = ["api"]`, an action
    # override and a `depends_on` that no Work has, and the template
    # `feature.parent`
    work = _block(
        "w6k2xm",
        'roots = ["api"]\ndepends_on = ["a7b2c4"]\n\n[actions]\ndeliver = ["ship"]\n',
    )
    _project(wio, {"w/README.md": work})
    before = wio.fingerprint(".agents")

    # When `skeleton feature.parent --work <W>` runs, with and without
    # `--keep roots`, and with an id and a template that do not exist
    plain = wio.run(["contracts", "skeleton", "feature.parent", "--work", "w6k2xm"])
    kept = wio.run(
        ["contracts", "skeleton", "feature.parent", "--work", "w6k2xm"]
        + ["--keep", "roots"]
    )
    no_work = wio.run(["contracts", "skeleton", "feature.parent", "--work", "zzzzzz"])
    no_template = wio.run(["contracts", "skeleton", "nosuch", "--work", "w6k2xm"])

    # Then the skeleton has the Work's id and `depends_on`, the template's roots and
    # no directive list, standard error names `roots` and `actions`, then only
    # `actions`, nothing is written, and each mistake names what is missing
    block = plain.stdout.split("-->\n", maxsplit=1)[0]
    assert 'id = "w6k2xm"' in block
    assert 'depends_on = ["a7b2c4"]' in block
    assert 'roots = ["@descendants"]' in block
    assert "<!-- wio:" not in plain.stdout
    assert "`roots`, `actions`" in plain.stderr
    assert 'roots = ["api"]' in kept.stdout
    assert "`actions`" in kept.stderr
    assert "`roots`" not in kept.stderr
    assert (plain.exit_code, kept.exit_code) == (0, 0)
    assert wio.fingerprint(".agents") == before
    assert "`zzzzzz`" in no_work.stderr
    assert "`nosuch`" in no_template.stderr
    assert (no_work.exit_code, no_template.exit_code) == (2, 2)


def _problems(output: Output) -> list[tuple[str, str, str]]:
    """Read the lines of a text report as severity, place and message.

    Args:
        output: What `wio contracts check` wrote.

    Returns:
        One tuple for each line.
    """
    parts = (line.split(": ", maxsplit=2) for line in output.stdout.splitlines())
    return [(severity, place, message) for severity, place, message in parts]


@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
def test_check_reports_every_problem_of_the_tree_in_one_run_and_in_one_order(
    wio: Wio,
) -> None:
    """Parent AC-4: four problems, as text and as JSON."""
    # Given Works that include two with one id, two that depend on each other, one
    # that lacks a section its template requires, and a directory under `nesting`
    # that holds two marked files
    _project(
        wio,
        {
            "s1/README.md": _block("s1s1s1"),
            "s2/README.md": _block("s1s1s1"),
            "x/README.md": _block("x2x2x2", 'depends_on = ["y3y3y3"]\n'),
            "y/README.md": _block("y3y3y3", 'depends_on = ["x2x2x2"]\n'),
            "r/README.md": _block("r4r4r4").replace("## Purpose\n\nWhy.\n", ""),
            "c/README.md": _block("c5c5c5"),
            "c/other.md": _block("c6c6c6"),
        },
    )

    # When `wio contracts check` runs, and then `wio contracts check --json`
    text = wio.run(["contracts", "check"])
    data = wio.run(["contracts", "check", "--json"])

    # Then both report all four problems, each with the paths it concerns, in the
    # same order, the second as one JSON array that parses, and each exits 1
    report = json.loads(data.stdout)
    assert [(p["severity"], p["where"], p["message"]) for p in report] == _problems(
        text
    )
    places = " ".join(place for _, place, _ in _problems(text))
    assert f"{WORKS}/s1/README.md" in text.stdout
    assert f"{WORKS}/s2/README.md" in text.stdout
    assert f"{WORKS}/x/README.md" in text.stdout
    assert "x2x2x2" in text.stdout
    assert "y3y3y3" in text.stdout
    assert f"{WORKS}/r/README.md" in places
    assert f"{WORKS}/c/" in text.stdout
    assert (text.exit_code, data.exit_code) == (1, 1)


@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
def test_check_warns_of_an_unknown_key_and_still_passes(wio: Wio) -> None:
    """Parent AC-4: a clean tree and a warning."""
    # Given a tree with no error, and a Work whose metadata has an unknown key
    _project(wio, {"w/README.md": _block("w6k2xm", "rots = []\n")})

    # When `wio contracts check` runs
    output = wio.run(["contracts", "check"])

    # Then it prints the warning that names the key and the key it is close to, and
    # exits 0
    assert output.stdout.startswith(f"warning: {WORKS}/w/README.md")
    assert "`rots`" in output.stdout
    assert "`roots`" in output.stdout
    assert output.exit_code == 0
