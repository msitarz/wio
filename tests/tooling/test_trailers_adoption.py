# SPDX-License-Identifier: Apache-2.0
"""Tests that the hook and the workflows of the repository use `wio trailers`."""

from tests.tooling.hooks import ROOT

SCRIPT = "records.py"


def test_the_script_and_its_references_are_gone() -> None:
    """AC-7: no hook, workflow or script names `records.py`, and the file is gone."""
    # Given the repository
    files = [
        ROOT / "prek.toml",
        *(ROOT / ".github" / "workflows").glob("*.yml"),
        *(ROOT / "scripts").rglob("*"),
    ]

    # When `prek.toml`, the workflows and `scripts/` are searched for `records.py`
    named = [
        path.name
        for path in files
        if path.is_file() and SCRIPT in path.read_text(errors="ignore")
    ]
    present = sorted(path.name for path in (ROOT / "scripts").rglob(SCRIPT))

    # Then the script and every reference to it are absent
    assert (named, present) == ([], [])


def test_the_hook_and_the_records_workflow_call_wio_trailers() -> None:
    """AC-7: the commit-msg hook checks and the workflow checks and folds."""
    # Given `prek.toml` and the `records` workflow
    prek = (ROOT / "prek.toml").read_text()
    workflow = (ROOT / ".github" / "workflows" / "records.yml").read_text()

    # When the commands they run are read
    commands = [
        "uv run wio trailers check --require",
        "uv run wio trailers check --ref-range",
        "uv run wio trailers fold body",
        "uv run wio trailers fold block",
    ]

    # Then the hook runs the commit-time check and the workflow runs the rest
    assert commands[0] in prek
    assert all(command in workflow for command in commands[1:])
