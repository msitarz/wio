# SPDX-License-Identifier: Apache-2.0
"""Tests of the text and the JSON of `show`."""

import json
from pathlib import Path
from typing import TYPE_CHECKING

from wio.contracts.show_render import render_show
from wio.contracts.showing import Related, ShownAction, ShownWork
from wio.models.frozen import freeze
from wio.models.works import Work

if TYPE_CHECKING:
    from collections.abc import Mapping

    from wio.contracts.showing import ShownSource

VIEW = (
    "# Child\n\n## Purpose\n\nOwn text.\n\n## Inherited from: Parent (p5n2hv)\n\n"
    "### Glossary\n\n- **Term**: a word.\n"
)
"""The resolved view of the child of AC-1."""
PATH = ".agents/wio/works/p/c/README.md"


def _work(**keys: object) -> Work:
    """Build the child of AC-1, with some of its fields replaced.

    Args:
        keys: The fields to replace.

    Returns:
        The Work.
    """
    fields: dict[str, object] = {
        "id": "k3m9xq",
        "title": "Child",
        "path": Path(PATH),
        "template": "feature.leaf",
        "roots": ("wio",),
        "depends_on": ("a7b2c4",),
        "actions": freeze({}),
    }
    return Work(**(fields | keys))  # type: ignore[arg-type]


def _action(
    name: str,
    source: ShownSource,
    *,
    on_demand: bool = False,
    preset: str | None = None,
    stages: tuple[str, ...] = (),
    removed: bool = False,
) -> ShownAction:
    """Build an action that `show` prints.

    Args:
        name: The action's name.
        source: Where it comes from.
        on_demand: Whether the config marks it on demand.
        preset: The stage preset it names.
        stages: Its stages.
        removed: Whether the Work removed it.

    Returns:
        The action.
    """
    return ShownAction(name, source, on_demand, preset, stages, removed=removed)


def _shown(work: Work | None = None, **parts: object) -> ShownWork:
    """Build the Work that AC-1 shows, with some of its parts replaced.

    Args:
        work: The Work, the child of AC-1 when none is given.
        parts: The parts of `ShownWork` to replace.

    Returns:
        What `show` prints.
    """
    fields: Mapping[str, object] = {
        "parent": Related("p5n2hv", "Parent", found=True),
        "resolved_roots": ("wio",),
        "depends_on": (Related("a7b2c4", "Sibling", found=True),),
        "dependents": (),
        "actions": (
            _action(
                "define",
                "template",
                preset="define-feature",
                stages=("define", "review-contract"),
            ),
            _action("deliver", "contract", stages=("ship",)),
            _action("amend", "contract", on_demand=True, removed=True),
        ),
        "view": VIEW,
    } | parts
    return ShownWork(work or _work(), **fields)  # type: ignore[arg-type]


TEXT = f"""\
Work k3m9xq  Child
  Path         {PATH}
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

{VIEW}"""


def test_the_text_is_the_facts_the_actions_a_rule_and_the_view() -> None:
    """AC-1: a child with an override."""
    # Given the shown Work of AC-1
    shown = _shown()

    # When `render_show` runs
    text = render_show(shown, as_json=False)

    # Then it is exactly the text of AC-1, ending in one line ending
    assert text == TEXT
    assert text.endswith("\n")
    assert not text.endswith("\n\n")


def test_the_labels_are_padded_to_column_15_and_a_second_value_is_in_that_column() -> (
    None
):
    """AC-2: labels and a second value."""
    # Given a Work with two dependents
    dependents = (
        Related("k3m9xq", "Child", found=True),
        Related("k5m8ps", "Other", found=True),
    )

    # When `render_show` runs
    text = render_show(_shown(dependents=dependents), as_json=False)

    # Then `Needed by` has the first dependent and the second is on the next
    # line at column 15
    assert "\n  Needed by    k3m9xq  Child\n               k5m8ps  Other\n" in text
    assert "\n               k5m8ps  Other\n".index("k5m8ps") == 16


def test_a_line_is_written_only_when_it_has_something_to_say() -> None:
    """AC-1: empty facts."""
    # Given a Work with no title, no template, no parent, no roots,
    # dependencies and dependents
    work = _work(title=None, template=None, roots=(), depends_on=())
    shown = _shown(
        work, parent=None, resolved_roots=(), depends_on=(), actions=(), view=""
    )

    # When `render_show` runs
    text = render_show(shown, as_json=False)

    # Then the first line is `Work <id>  (no title)` and only `Path` follows it
    assert text.splitlines()[:3] == [
        "Work k3m9xq  (no title)",
        f"  Path         {PATH}",
        "",
    ]


def test_a_work_that_lists_descendants_shows_the_roots_as_written_and_resolved() -> (
    None
):
    """AC-2: roots."""
    # Given a Work with `e2e` and `@descendants`, one that resolves to nothing
    # and one without `@descendants` whose roots the hierarchy sorted
    both = _work(roots=("e2e", "@descendants"))
    plain = _work(roots=("web", "api"))

    # When `render_show` runs on each
    first = render_show(_shown(both, resolved_roots=("api", "e2e")), as_json=False)
    second = render_show(_shown(both, resolved_roots=()), as_json=False)
    third = render_show(_shown(plain, resolved_roots=("api", "web")), as_json=False)

    # Then the first is `e2e, @descendants → api, e2e`, the second ends in
    # `→ none` and the third shows its roots as written
    assert "\n  Roots        e2e, @descendants → api, e2e\n" in first
    assert "\n  Roots        e2e, @descendants → none\n" in second
    assert "\n  Roots        web, api\n" in third


def test_an_action_line_has_its_preset_its_source_and_the_on_demand_mark() -> None:
    """AC-1: defaults, an on-demand action and an undeclared name."""
    # Given the shown actions of the second scenario of AC-1
    actions = (
        _action("deliver", "defaults", stages=("build",)),
        _action(
            "amend",
            "defaults",
            on_demand=True,
            preset="amend-contract",
            stages=("amend", "review-amendment"),
        ),
        _action("ratify", "contract", stages=("ship",)),
    )

    # When `render_show` runs
    text = render_show(_shown(actions=actions), as_json=False)

    # Then the actions block is exactly the text of AC-1
    assert (
        "Actions\n"
        "  deliver  (from the config defaults)\n"
        "             build\n"
        "  amend    amend-contract  (on demand, from the config defaults)\n"
        "             amend, review-amendment\n"
        "  ratify   (from the contract)\n"
        "             ship\n"
        "\n----\n"
    ) in text


def test_a_work_with_no_action_has_none_under_actions_and_an_empty_json_array() -> None:
    """AC-1: a Work that resolves to no action."""
    # Given a shown Work with no action
    shown = _shown(actions=())

    # When `render_show` runs, as text and with JSON
    text = render_show(shown, as_json=False)
    data = json.loads(render_show(shown, as_json=True))

    # Then the text has `Actions` and the line `  none`, and the JSON `actions`
    # is `[]`
    assert "\n\nActions\n  none\n\n----\n" in text
    assert data["actions"] == []


def test_a_work_whose_actions_are_all_removed_prints_them_and_not_none() -> None:
    """AC-1: all actions removed."""
    # Given a shown Work whose actions are all removed by the contract
    actions = (
        _action("deliver", "contract", removed=True),
        _action("amend", "contract", on_demand=True, removed=True),
    )

    # When `render_show` runs
    text = render_show(_shown(actions=actions), as_json=False)

    # Then each is `removed (by the contract)` and there is no `none` line
    assert (
        "Actions\n  deliver  removed (by the contract)\n"
        "  amend    removed (by the contract)\n"
    ) in text
    assert "  none" not in text


def test_a_removed_action_has_no_on_demand_mark_and_a_list_has_no_preset_name() -> None:
    """AC-1: removed and listed."""
    # Given a removed on-demand action, an action given as a list and a preset
    # the config does not declare
    actions = (
        _action("amend", "contract", on_demand=True, removed=True),
        _action("deliver", "template", stages=("build", "ship")),
        _action("ratify", "defaults", preset="unknown"),
    )

    # When `render_show` runs
    text = render_show(_shown(actions=actions), as_json=False)

    # Then the first is `removed (by the contract)`, the second has no preset
    # name and the third has no stages line
    assert (
        "Actions\n"
        "  amend    removed (by the contract)\n"
        "  deliver  (from the template)\n"
        "             build, ship\n"
        "  ratify   unknown  (from the config defaults)\n"
        "\n----\n"
    ) in text


def test_a_related_work_without_a_title_or_not_found_is_written_as_such() -> None:
    """AC-3: related works."""
    # Given dependencies that are found, have no title, are not found and are shared
    depends = (
        Related("a7b2c4", "Twin", found=True),
        Related("a7b2c4", "Twin two", found=True),
        Related("n5p7qr", None, found=True),
        Related("y4k2mq", None, found=False),
    )

    # When `render_show` runs
    text = render_show(_shown(depends_on=depends), as_json=False)

    # Then each is `<id>  <title>`, `<id>  (no title)` or `<id>  (not found)`
    assert (
        "  After        a7b2c4  Twin\n"
        "               a7b2c4  Twin two\n"
        "               n5p7qr  (no title)\n"
        "               y4k2mq  (not found)\n"
    ) in text


def test_the_json_is_one_object_with_its_fields_in_order() -> None:
    """AC-5: the child as JSON."""
    # Given the shown Work of AC-1
    shown = _shown()

    # When `render_show` runs with JSON
    text = render_show(shown, as_json=True)

    # Then one line that parses, ends in one line ending and has the fields in
    # the order of the contract, with `null` for a title, a template, a parent
    # or a preset that there is none of
    data = json.loads(text)
    assert text == json.dumps(data) + "\n"
    fields = "id title path template parent roots resolved_roots depends_on"
    fields += " dependents actions view"
    assert list(data) == fields.split()
    assert (data["parent"], data["depends_on"], data["dependents"]) == (
        "p5n2hv",
        ["a7b2c4"],
        [],
    )
    assert (data["path"], data["roots"], data["resolved_roots"]) == (
        PATH,
        ["wio"],
        ["wio"],
    )
    assert data["view"] == VIEW
    bare = json.loads(
        render_show(_shown(_work(title=None, template=None), parent=None), as_json=True)
    )
    assert (bare["title"], bare["template"], bare["parent"]) == (None, None, None)


def test_the_json_actions_say_their_source_the_flag_the_preset_and_the_stages() -> None:
    """AC-5: JSON actions."""
    # Given a template action, a contract list, a removed on-demand action and
    # an undeclared preset
    actions = (
        _action("define", "template", preset="define-feature", stages=("define",)),
        _action("deliver", "contract", stages=("ship",)),
        _action("amend", "contract", on_demand=True, removed=True),
        _action("ratify", "defaults", preset="unknown"),
    )

    # When `render_show` runs with JSON
    data = json.loads(render_show(_shown(actions=actions), as_json=True))

    # Then each has `name`, `source`, `on_demand`, `preset` and `stages` as the
    # contract says, and a removed action has the source `contract` and no
    # preset
    assert data["actions"] == [
        {
            "name": "define",
            "source": "template",
            "on_demand": False,
            "preset": "define-feature",
            "stages": ["define"],
        },
        {
            "name": "deliver",
            "source": "contract",
            "on_demand": False,
            "preset": None,
            "stages": ["ship"],
        },
        {
            "name": "amend",
            "source": "contract",
            "on_demand": True,
            "preset": None,
            "stages": [],
        },
        {
            "name": "ratify",
            "source": "defaults",
            "on_demand": False,
            "preset": "unknown",
            "stages": [],
        },
    ]
