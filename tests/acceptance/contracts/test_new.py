# SPDX-License-Identifier: Apache-2.0
"""Scenarios of `wio contracts new`."""

import json
from typing import TYPE_CHECKING

import pytest

from tests.acceptance.channels import Channel

if TYPE_CHECKING:
    from tests.acceptance.dsl.wio import Wio

WORKS = ".agents/wio/works"


def _project(wio: Wio) -> None:
    """Prepare a nesting project with two kinds and templates.

    Args:
        wio: The scenario facade.
    """
    wio.fixture("contracts/list-empty")
    wio.put(
        ".agents/wio/config.toml",
        b"""[works]
hierarchy = "nesting"
[templates.kinds]
feature = "feature.draft"
other = "other.note"
[roots.wio]
paths = ["src"]
""",
    )
    for name, kind in (
        ("feature.draft", "feature"),
        ("feature.leaf", "feature"),
        ("other.note", "other"),
    ):
        template = (
            f'<!-- wio\nkind = "{kind}"\ndescription = "A template."\n'
            "[contract]\nroots = []\ndepends_on = []\n-->\n\n# Old\n\n## Purpose\n"
        )
        wio.put(f".agents/wio/templates/{name}.md", template.encode())


@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
def test_a_work_is_created_from_the_entry_template_of_a_kind(wio: Wio) -> None:
    """AC-1: a kind creates the template skeleton with requested changes."""
    # Given a project with an entry template and a declared root
    _project(wio)

    # When the command creates a Work with a title and root
    result = wio.run(
        [
            "contracts",
            "new",
            "feature",
            "--title",
            "Read config",
            "--root",
            "wio",
            "--json",
        ]
    )

    # Then the file and report carry the requested facts
    assert (result.exit_code, result.stderr) == (0, "")
    report = json.loads(result.stdout)
    content = wio.read(report["path"]).decode()
    listing = wio.run(["contracts", "list", "--json"])
    work = json.loads(listing.stdout)[0]
    assert work["id"] == report["id"]
    assert work["template"] == "feature.draft"
    assert work["roots"] == ["wio"]
    assert work["depends_on"] == []
    assert content.endswith("\n# Read config\n\n## Purpose\n")


@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
def test_any_template_can_be_used_and_kind_and_template_must_agree(wio: Wio) -> None:
    """AC-2: an explicit template is accepted and a mismatched kind is refused."""
    # Given two kinds and their templates
    _project(wio)

    # When an explicit leaf and a mismatched template are requested
    first = wio.run(
        ["contracts", "new", "--template", "feature.leaf", "--slug", "a", "--json"]
    )
    second = wio.run(
        ["contracts", "new", "feature", "--template", "other.note", "--slug", "b"]
    )

    # Then the first is created and the second is refused
    assert first.exit_code == 0
    assert json.loads(first.stdout)["template"] == "feature.leaf"
    assert second.exit_code == 2
    assert "other" in second.stderr
    assert "feature" in second.stderr


@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
def test_a_bare_contract_holds_the_id_and_a_heading(wio: Wio) -> None:
    """AC-3: a bare Work has a generated identity and heading."""
    # Given a nesting project without kinds
    wio.fixture("contracts/list-empty")

    # When a bare Work is created
    result = wio.run(["contracts", "new", "--slug", "note", "--json"])

    # Then its file contains only the metadata block and heading
    assert result.exit_code == 0
    report = json.loads(result.stdout)
    assert (
        wio.read(report["path"]).decode()
        == f'<!-- wio\nid = "{report["id"]}"\n-->\n\n# Title\n'
    )


@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
def test_a_mistake_creates_nothing(wio: Wio) -> None:
    """AC-5: an invalid root reports an error without creating a file."""
    # Given a project with an entry template
    _project(wio)
    before = wio.fingerprint(WORKS)

    # When a Work is requested with an undeclared root
    result = wio.run(
        ["contracts", "new", "feature", "--slug", "a", "--root", "missing"]
    )

    # Then the error is reported and the Works are unchanged
    assert result.exit_code == 2
    assert "missing" in result.stderr
    assert result.stdout == ""
    assert wio.fingerprint(WORKS) == before


@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
def test_json_is_one_object_with_the_same_facts(wio: Wio) -> None:
    """AC-6: JSON reports the parent inferred from a path."""
    # Given a nesting project with a parent Work
    _project(wio)
    wio.put(f"{WORKS}/p/README.md", b'<!-- wio\nid = "p5n2hv"\n-->\n\n# Parent\n')

    # When a new Work is created by path beneath that parent
    result = wio.run(["contracts", "new", "--path", f"{WORKS}/p/c/spec.md", "--json"])

    # Then the object gives the fields in order and names the parent
    assert result.exit_code == 0
    report = json.loads(result.stdout)
    assert list(report) == ["id", "title", "path", "template", "parent"]
    assert report["parent"] == "p5n2hv"
    assert report["template"] is None
