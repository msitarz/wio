# SPDX-License-Identifier: Apache-2.0
"""Scenarios of `wio contracts show`, which shows one Work in full."""

import json
from typing import TYPE_CHECKING

import pytest

from tests.acceptance.channels import Channel

if TYPE_CHECKING:
    from tests.acceptance.dsl.results import Output
    from tests.acceptance.dsl.wio import Wio

WORKS = ".agents/wio/works"
HINT = "`wio contracts check` shows every problem."
CONFIG = """\
[works]
hierarchy = "{hierarchy}"

[templates.kinds]
feature = "feature.leaf"

[actions.define]
description = "Define it."

[actions.deliver]
description = "Deliver it."

[actions.amend]
on_demand = true
description = "Amend it."

[stages.define]
goal = "Define."

[stages.review-contract]
goal = "Review the contract."

[stages.build]
goal = "Build."

[stages.ship]
goal = "Ship."

[stages.amend]
goal = "Amend."

[stages.review-amendment]
goal = "Review the amendment."

[stage_presets]
define-feature = ["define", "review-contract"]
amend-contract = ["amend", "review-amendment"]
"""
LEAF = """\
<!-- wio
kind = "feature"

[actions]
define = "define-feature"
deliver = ["build"]
amend = "amend-contract"
-->

# Leaf
"""
CHILD_TEXT = f"""\
Work k3m9xq  Child
  Path         {WORKS}/p/c/README.md
  Template     feature.leaf
  Parent       p5n2hv  Parent
  Roots        wio
  After        a7b2c4  Sibling

Actions
  define   define-feature  (from the template)
             define, review-contract
  deliver  (from the contract)
             ship
  amend    removed (by the contract)

----

# Child

## Purpose

Own text.

## Inherited from: Parent (p5n2hv)

### Glossary

- **Term**: a word.
"""


def _begin(wio: Wio) -> None:
    """Start the repository of the scenario, which the CLI channel makes a git one.

    Args:
        wio: The facade.
    """
    wio.fixture("contracts/show-base")


def _put(wio: Wio, files: dict[str, str]) -> None:
    """Write text files into the repository of the scenario.

    Args:
        wio: The facade.
        files: The files, by path relative to the root of the repository.
    """
    for path, text in files.items():
        wio.put(path, text.encode())


def _work(work_id: str, title: str, block: str = "") -> str:
    """Write a Work that has a title and a block.

    Args:
        work_id: The id.
        title: The text of its first heading.
        block: More lines of the block, such as `roots`.

    Returns:
        The text of the file.
    """
    return f'<!-- wio\nid = "{work_id}"\n{block}-->\n\n# {title}\n'


def _project(
    wio: Wio,
    hierarchy: str = "nesting",
    parent_roots: str = "",
    child_roots: str = '"wio"',
    *,
    other: bool = False,
) -> None:
    """Build the project of AC-1: a parent, a sibling and a child.

    Args:
        wio: The facade.
        hierarchy: The hierarchy mode of the config.
        parent_roots: The `roots` of the parent as TOML, none when empty.
        child_roots: The `roots` of the child as TOML.
        other: Whether to add `Other`, which also lists the sibling.
    """
    roots = f"roots = [{parent_roots}]\n" if parent_roots else ""
    parent = f'id = "p5n2hv"\n{roots}'
    child = (
        'id = "k3m9xq"\ntemplate = "feature.leaf"\n'
        f'roots = [{child_roots}]\ndepends_on = ["a7b2c4"]\n\n'
        '[actions]\ndeliver = ["ship"]\namend = []\n'
    )
    _begin(wio)
    files = {
        ".agents/wio/config.toml": CONFIG.format(hierarchy=hierarchy),
        ".agents/wio/templates/feature.leaf.md": LEAF,
        f"{WORKS}/p/README.md": (
            f"<!-- wio\n{parent}-->\n\n# Parent\n\n"
            "## Glossary <!-- wio: inherit -->\n\n- **Term**: a word.\n"
        ),
        f"{WORKS}/p/s/README.md": _work("a7b2c4", "Sibling"),
        f"{WORKS}/p/c/README.md": (
            f"<!-- wio\n{child}-->\n\n# Child\n\n## Purpose\n\nOwn text.\n"
        ),
    }
    if other:
        files[f"{WORKS}/p/o/README.md"] = _work(
            "k5m8ps", "Other", 'depends_on = ["a7b2c4"]\n'
        )
    _put(wio, files)


def _solo(wio: Wio, config: str) -> None:
    """Build a project with one Work that follows no template.

    Args:
        wio: The facade.
        config: The config, as TOML.
    """
    _begin(wio)
    _put(
        wio,
        {
            ".agents/wio/config.toml": config,
            f"{WORKS}/s/README.md": _work(
                "k3m9xq", "Solo", '\n[actions]\nratify = ["ship"]\n'
            ),
        },
    )


@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
def test_a_work_is_shown_with_its_facts_its_actions_and_its_resolved_contract(
    wio: Wio,
) -> None:
    """AC-1: a child with an override."""
    # Given a nesting project with a parent, a sibling and a child with an
    # override
    _project(wio)

    # When `wio contracts show k3m9xq` runs
    output = wio.run(["contracts", "show", "k3m9xq"])

    # Then it prints the text of AC-1 and exits 0
    assert output.stdout == CHILD_TEXT
    assert (output.stderr, output.exit_code) == ("", 0)


@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
def test_the_defaults_an_on_demand_action_and_an_undeclared_name_are_shown(
    wio: Wio,
) -> None:
    """AC-1: defaults, an on-demand action and an undeclared name."""
    # Given a config with defaults and a Work with no template and an undeclared
    # action
    config = """\
[actions.deliver]
description = "Deliver it."

[actions.amend]
on_demand = true
description = "Amend it."

[stages.build]
goal = "Build."

[stages.amend]
goal = "Amend."

[stages.review-amendment]
goal = "Review the amendment."

[stages.ship]
goal = "Ship."

[stage_presets]
amend-contract = ["amend", "review-amendment"]

[works.defaults.actions]
deliver = ["build"]
amend = "amend-contract"
"""
    _solo(wio, config)

    # When `wio contracts show k3m9xq` runs
    output = wio.run(["contracts", "show", "k3m9xq"])

    # Then the actions block is the text of AC-1
    assert (
        "Actions\n"
        "  deliver  (from the config defaults)\n"
        "             build\n"
        "  amend    amend-contract  (on demand, from the config defaults)\n"
        "             amend, review-amendment\n"
        "  ratify   (from the contract)\n"
        "             ship\n"
        "\n----\n"
    ) in output.stdout
    assert (output.stderr, output.exit_code) == ("", 0)


@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
def test_a_work_that_resolves_to_no_action_shows_none_and_exits_0(wio: Wio) -> None:
    """AC-1: a Work that resolves to no action."""
    # Given a config with no defaults and a Work with no template and no
    # `[actions]`
    _begin(wio)
    _put(
        wio,
        {
            ".agents/wio/config.toml": '[works]\nhierarchy = "flat"\n',
            f"{WORKS}/s/README.md": _work("k3m9xq", "Solo"),
        },
    )

    # When `wio contracts show k3m9xq` and the same with `--json` run
    text = wio.run(["contracts", "show", "k3m9xq"])
    data = wio.run(["contracts", "show", "k3m9xq", "--json"])

    # Then the first prints `Actions` and `  none`, the second has
    # `"actions": []`, and each exits 0
    assert "\n\nActions\n  none\n\n----\n" in text.stdout
    assert json.loads(data.stdout)["actions"] == []
    assert (text.exit_code, data.exit_code) == (0, 0)


@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
def test_roots_resolve_and_dependents_are_listed(wio: Wio) -> None:
    """AC-2: a parent and its dependents."""
    # Given the Works of AC-1 with a parent that lists `@descendants`, a child
    # with `api`, and an `Other` that also lists the sibling
    _project(wio, parent_roots='"e2e", "@descendants"', child_roots='"api"', other=True)

    # When `show` runs on the sibling and on the parent
    sibling = wio.run(["contracts", "show", "a7b2c4"])
    parent = wio.run(["contracts", "show", "p5n2hv"])

    # Then the sibling lists both dependents, the second in the same column, and
    # the parent shows its roots resolved
    assert (
        "\n  Needed by    k3m9xq  Child\n               k5m8ps  Other\n"
        in sibling.stdout
    )
    assert "\n  Roots        e2e, @descendants → api, e2e\n" in parent.stdout


@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
def test_under_flat_there_is_no_parent_and_nothing_is_inherited(wio: Wio) -> None:
    """AC-2: under flat."""
    # Given `hierarchy = "flat"` and the Works of AC-1
    _project(wio, hierarchy="flat")

    # When `wio contracts show k3m9xq` runs
    output = wio.run(["contracts", "show", "k3m9xq"])

    # Then there is no `Parent` line and the view is the Work's own contract
    assert "  Parent " not in output.stdout
    assert output.stdout.endswith("\n----\n\n# Child\n\n## Purpose\n\nOwn text.\n")
    assert output.exit_code == 0


@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
def test_a_path_from_a_subdirectory_shows_the_same_work(wio: Wio) -> None:
    """AC-3: a path from a subdirectory."""
    # Given the Works of AC-1 and the working directory `.agents/wio/works/p`
    _project(wio)

    # When `wio contracts show c/README.md` runs there
    by_path = wio.run(["contracts", "show", "c/README.md"], f"{WORKS}/p")
    by_id = wio.run(["contracts", "show", "k3m9xq"])

    # Then it prints the same as `wio contracts show k3m9xq`
    assert by_path.stdout == by_id.stdout == CHILD_TEXT
    assert (by_path.stderr, by_path.exit_code) == ("", 0)


@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
def test_an_id_that_no_work_has_is_told_with_the_closest_one(wio: Wio) -> None:
    """AC-3: an id that no Work has."""
    # Given the Works of AC-1
    _project(wio)

    # When `show k3m9xr` and `show zzzzzz` run
    close = wio.run(["contracts", "show", "k3m9xr"])
    far = wio.run(["contracts", "show", "zzzzzz"])

    # Then the first names the closest id, the second does not, and each exits 2
    assert (
        close.stderr == "error: No Work has the id `k3m9xr`. Did you mean `k3m9xq`?\n"
    )
    assert far.stderr == "error: No Work has the id `zzzzzz`.\n"
    assert (close.stdout, close.exit_code, far.stdout, far.exit_code) == ("", 2, "", 2)


@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
def test_a_file_that_is_not_a_work_gives_its_reason_and_exits_2(wio: Wio) -> None:
    """AC-3: a file that is not a Work."""
    # Given an unmarked file, a path that does not exist and a file outside the
    # Works directory
    _project(wio)
    _put(wio, {f"{WORKS}/p/notes.md": "# Notes\n", "README.md": "# Repository\n"})
    arguments = [f"{WORKS}/p/notes.md", f"{WORKS}/p/missing.md", "README.md"]

    # When `show` runs on each
    outputs = [wio.run(["contracts", "show", argument]) for argument in arguments]

    # Then each prints an error with a different reason and exits 2
    errors = [output.stderr for output in outputs]
    assert all(a in e for a, e in zip(arguments, errors, strict=True))
    assert len(set(errors)) == 3
    assert [(o.stdout, o.exit_code) for o in outputs] == [("", 2)] * 3


@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
def test_a_shared_id_refuses_its_own_lookup_and_is_listed_twice_elsewhere(
    wio: Wio,
) -> None:
    """AC-3: a shared id."""
    # Given two Works that share an id and a Work that lists it
    _begin(wio)
    _put(
        wio,
        {
            ".agents/wio/config.toml": CONFIG.format(hierarchy="flat"),
            f"{WORKS}/a/README.md": _work("a7b2c4", "Twin"),
            f"{WORKS}/b/README.md": _work("a7b2c4", "Twin two"),
            f"{WORKS}/c/README.md": _work(
                "k3m9xq", "Lister", 'depends_on = ["a7b2c4"]\n'
            ),
        },
    )

    # When `show` runs on the id and on the Work that lists it
    shared = wio.run(["contracts", "show", "a7b2c4"])
    lister = wio.run(["contracts", "show", "k3m9xq"])

    # Then the first is refused with the error of discovery and the hint, and
    # the second lists both
    assert shared.stdout == ""
    assert shared.exit_code == 2
    assert f"{WORKS}/a/README.md" in shared.stderr
    assert f"{WORKS}/b/README.md" in shared.stderr
    assert shared.stderr.endswith(HINT + "\n")
    assert (
        "\n  After        a7b2c4  Twin\n               a7b2c4  Twin two\n"
        in lister.stdout
    )
    assert lister.exit_code == 0


def _refused(output: Output) -> bool:
    """Tell whether a run was refused for an incomplete tree.

    Args:
        output: What the run produced.

    Returns:
        Whether nothing is on standard output, the hint ends standard error and
        the exit code is 2.
    """
    return (
        output.stdout == ""
        and output.stderr.endswith(HINT + "\n")
        and output.exit_code == 2
    )


@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
def test_an_incomplete_tree_refuses_the_command_and_other_errors_do_not(
    wio: Wio,
) -> None:
    """AC-4: each case."""
    # Given a tree with an unreadable Work file, one with two marked files in a
    # directory and one with an undeclared root and a cycle
    config = {".agents/wio/config.toml": CONFIG.format(hierarchy="nesting")}
    _begin(wio)
    _put(wio, config | {f"{WORKS}/g/README.md": _work("k3m9xq", "Good")})
    wio.put(f"{WORKS}/u/README.md", b"\xff\xfe")
    unreadable = wio.run(["contracts", "show", "k3m9xq"])
    _put(wio, {f"{WORKS}/g/other.md": _work("a7b2c4", "Second")})
    wio.put(f"{WORKS}/u/README.md", _work("n5p7qr", "Fine").encode())
    collision = wio.run(["contracts", "show", "n5p7qr"])
    _put(
        wio,
        {
            f"{WORKS}/g/other.md": "# Not a Work\n",
            f"{WORKS}/u/README.md": _work(
                "n5p7qr", "Fine", 'roots = ["nosuch"]\ndepends_on = ["y4k2mq"]\n'
            ),
            f"{WORKS}/v/README.md": _work(
                "y4k2mq", "Cycle", 'depends_on = ["n5p7qr"]\n'
            ),
        },
    )

    # When `show` runs on a good Work of each
    soft = wio.run(["contracts", "show", "k3m9xq"])

    # Then the first two write nothing to standard output and exit 2, and the
    # third prints the Work and exits 0
    assert _refused(unreadable)
    assert _refused(collision)
    assert soft.stdout.startswith("Work k3m9xq  Good\n")
    assert (soft.stderr, soft.exit_code) == ("", 0)


@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
def test_json_is_one_object_with_the_same_facts_and_the_view(wio: Wio) -> None:
    """AC-5: the child as JSON."""
    # Given the Works of AC-1
    _project(wio)

    # When `wio contracts show k3m9xq --json` runs
    output = wio.run(["contracts", "show", "k3m9xq", "--json"])

    # Then it prints one object with the fields of AC-5 in order
    data = json.loads(output.stdout)
    assert output.stdout == json.dumps(data) + "\n"
    assert list(data) == [
        "id",
        "title",
        "path",
        "template",
        "parent",
        "roots",
        "resolved_roots",
        "depends_on",
        "dependents",
        "actions",
        "view",
    ]
    assert (data["parent"], data["depends_on"], data["resolved_roots"]) == (
        "p5n2hv",
        ["a7b2c4"],
        ["wio"],
    )
    assert data["dependents"] == []
    define, deliver, amend = data["actions"]
    assert (define["source"], define["preset"]) == ("template", "define-feature")
    assert (deliver["source"], deliver["on_demand"], deliver["preset"]) == (
        "contract",
        False,
        None,
    )
    assert (deliver["stages"], amend["on_demand"], amend["stages"]) == (
        ["ship"],
        True,
        [],
    )
    assert amend["source"] == "contract"
    assert "## Inherited from: Parent (p5n2hv)" in data["view"]
    assert (output.stderr, output.exit_code) == ("", 0)


@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
def test_showing_writes_nothing_and_prints_the_same_bytes_twice(wio: Wio) -> None:
    """AC-6: nothing is written and the output is the same."""
    # Given the Works of AC-1 and a hash of each contract
    _project(wio)
    before = wio.fingerprint(".agents")

    # When `show` and `show --json` each run twice
    texts = [wio.run(["contracts", "show", "k3m9xq"]) for _ in range(2)]
    objects = [wio.run(["contracts", "show", "k3m9xq", "--json"]) for _ in range(2)]

    # Then the outputs of each are identical and no contract changed
    assert texts[0] == texts[1]
    assert objects[0] == objects[1]
    assert wio.fingerprint(".agents") == before
