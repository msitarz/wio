# SPDX-License-Identifier: Apache-2.0
"""Tests that this repository's templates are named by their files."""

import subprocess
import sys
import tomllib
from pathlib import Path

import pytest

pytestmark = pytest.mark.slow

ROOT = Path(__file__).resolve().parents[2]
TEMPLATES = ROOT / ".agents" / "wio" / "templates"
SCRIPT = Path(sys.executable).parent / "wio"
NAMES = ("feature.draft", "feature.leaf", "feature.parent")


def test_the_repository_lists_its_templates_by_their_files() -> None:
    """AC-7: `wio templates list` names the three `feature` templates."""
    # Given the delivered tree

    # When `wio templates list` runs in it
    done = subprocess.run(
        [str(SCRIPT), "templates", "list"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    # Then it lists the three under `feature`, the draft marked as the entry
    lines = done.stdout.splitlines()
    names = [
        line.split()[0] for line in lines if line.startswith("  ") and line[2] != " "
    ]
    assert lines[0] == "feature"
    assert lines[1].split()[:2] == ["feature.draft", "[entry]"]
    assert names == list(NAMES)
    assert (done.returncode, done.stderr) == (0, "")


@pytest.mark.parametrize("name", NAMES)
def test_a_template_of_the_repository_has_no_name_key(name: str) -> None:
    """AC-7: the file names the template, so its block has no `name` key."""
    # Given the block of a template of this repository
    text = (TEMPLATES / f"{name}.md").read_text(encoding="utf-8")
    block = text.removeprefix("<!-- wio\n").split("\n-->\n", maxsplit=1)[0]

    # When the block is read as TOML
    data = tomllib.loads(block)

    # Then it has no `name` key
    assert "name" not in data
