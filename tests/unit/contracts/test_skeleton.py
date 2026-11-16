# SPDX-License-Identifier: Apache-2.0
"""Tests of how `skeleton` checks `--keep`, carries keys and words the note."""

import tomllib
from pathlib import Path

import pytest

from wio.contracts import ContractsError
from wio.contracts.skeleton import Skeleton, carry_keys, check_keep

PARENT = (
    '<!-- wio\ntemplate = "feature.parent"\nroots = ["@descendants"]\n'
    "depends_on = []\n-->\n\n# <Work name>\n\n## Purpose\n"
)
WORK = {
    "id": "k3m9xq",
    "template": "feature.leaf",
    "roots": ["api"],
    "depends_on": ["a7b2c4"],
    "actions": {"deliver": ["ship"]},
    "x": {"ticket": "PAY-1"},
}


def _data(skeleton: Skeleton) -> dict[str, object]:
    """Read the keys of a comment block.

    Args:
        skeleton: The skeleton.

    Returns:
        The decoded keys in the order written.
    """
    head = skeleton.text.removeprefix("<!-- wio\n").partition("-->\n")[0]
    return tomllib.loads(head)


@pytest.mark.parametrize("key", ["id", "template", "depends_on", "wio"])
def test_check_keep_refuses_each_key_that_cannot_be_kept(key: str) -> None:
    """Each of the four keys that the skeleton handles is refused by name."""
    # Given a Work that has the key, where it can have one
    keys = ["id", "template", "depends_on", "roots"]

    # When it is asked for with `--keep`
    with pytest.raises(ContractsError) as raised:
        check_keep([key], keys)

    # Then the refusal says that the key cannot be kept
    assert f"`{key}` cannot be kept" in str(raised.value)


def test_check_keep_refuses_those_before_a_key_the_work_lacks() -> None:
    """A key that cannot be kept is reported before a key the Work does not have."""
    # Given a `--keep` that names a missing key and then one that cannot be kept
    keep = ["nosuch", "id"]

    # When it is checked
    with pytest.raises(ContractsError) as raised:
        check_keep(keep, ["id", "roots"])

    # Then the refusal is the one for `id`
    assert "`id` cannot be kept" in str(raised.value)
    assert "nosuch" not in str(raised.value)


def test_check_keep_lists_the_keys_that_can_be_kept_in_the_order_of_the_work() -> None:
    """The message for a missing key names what can be kept, in file order."""
    # Given a Work with keys in an order of its own
    keys = ["id", "x", "template", "roots", "depends_on", "actions"]

    # When a key it does not have is asked for
    with pytest.raises(ContractsError) as raised:
        check_keep(["nosuch"], keys)

    # Then the message names `x`, `roots` and `actions`, in that order
    assert "no key `nosuch`" in str(raised.value)
    assert "`x`, `roots`, `actions`" in str(raised.value)


def test_check_keep_says_when_the_work_has_nothing_to_keep() -> None:
    """A Work with only handled keys has nothing to keep."""
    # Given a Work with only its id

    # When a key is asked for
    with pytest.raises(ContractsError) as raised:
        check_keep(["roots"], ["id"])

    # Then the message says that there is no key to keep
    assert "no key to keep" in str(raised.value)


def test_check_keep_accepts_keys_the_work_has() -> None:
    """Keys that the Work has, repeated ones included, pass."""
    # Given a Work with `roots` and `x`

    # When both are kept, `roots` twice
    check_keep(["roots", "x", "roots"], ["id", "roots", "x"])

    # Then nothing is raised


def test_carry_keys_puts_the_id_first_and_carries_depends_on_exactly() -> None:
    """The identity is the Work's, in the template's shape."""
    # Given a Work and a prepared skeleton

    # When nothing is kept
    skeleton = carry_keys(PARENT, WORK, [])

    # Then `id` is first, `depends_on` is the Work's and the rest is the template's
    assert _data(skeleton) == {
        "id": "k3m9xq",
        "template": "feature.parent",
        "roots": ["@descendants"],
        "depends_on": ["a7b2c4"],
    }
    assert next(iter(_data(skeleton))) == "id"


def test_carry_keys_leaves_the_templates_depends_on_for_a_work_with_none() -> None:
    """A Work with no `depends_on` leaves the template's as it is."""
    # Given a Work with an id only and a template with `depends_on = []`
    work = {"id": "k3m9xq"}

    # When the keys are carried
    skeleton = carry_keys(PARENT, work, [])

    # Then the template's `depends_on` stands
    assert _data(skeleton)["depends_on"] == []
    assert skeleton.dropped == ()


def test_carry_keys_gives_an_empty_depends_on_for_an_empty_one() -> None:
    """`depends_on = []` of the Work is carried as it is."""
    # Given a Work with `depends_on = []` and a template that lists one
    template = PARENT.replace("depends_on = []", 'depends_on = ["z9z9z9"]')

    # When the keys are carried
    skeleton = carry_keys(template, {"id": "k3m9xq", "depends_on": []}, [])

    # Then `depends_on` is empty
    assert _data(skeleton)["depends_on"] == []


def test_carry_keys_carries_a_wrong_type_of_depends_on_as_the_file_has_it() -> None:
    """A string `depends_on` is not an error."""
    # Given a Work whose `depends_on` is a string
    work = {"id": "k3m9xq", "depends_on": "a7b2c4"}

    # When the keys are carried
    skeleton = carry_keys(PARENT, work, [])

    # Then it is written as a string
    assert 'depends_on = "a7b2c4"' in skeleton.text


def test_carry_keys_replaces_a_template_key_and_adds_a_missing_one_when_kept() -> None:
    """A kept key replaces the template's, or is added."""
    # Given a Work with `roots` that the template has and `actions` that it lacks

    # When both are kept
    skeleton = carry_keys(PARENT, WORK, ["roots", "actions"])

    # Then `roots` is the Work's and `actions` is added
    data = _data(skeleton)
    assert data["roots"] == ["api"]
    assert data["actions"] == {"deliver": ["ship"]}


def test_carry_keys_carries_a_kept_table_as_a_value() -> None:
    """A table of the Work is written as a standard table."""
    # Given a Work with an `[x]` table

    # When it is kept
    skeleton = carry_keys(PARENT, WORK, ["x"])

    # Then the table is written with its own header
    assert '\n[x]\nticket = "PAY-1"\n' in skeleton.text


def test_carry_keys_lists_the_dropped_keys_in_the_order_of_the_work() -> None:
    """What was not carried is named, without `template`, in file order."""
    # Given a Work whose keys are in the order of `WORK`

    # When nothing is kept, and when `roots` is kept twice
    none = carry_keys(PARENT, WORK, [])
    some = carry_keys(PARENT, WORK, ["roots", "roots"])

    # Then the dropped keys follow the order of the Work, and a kept one is gone
    assert none.dropped == ("roots", "actions", "x")
    assert some.dropped == ("actions", "x")


def test_carry_keys_keeps_the_form_the_endings_and_the_body() -> None:
    """The template's form, line endings and body are the skeleton's."""
    # Given templates in front matter and with CRLF
    front = '+++\nwio = 1\ntemplate = "t"\n+++\n\n# <Work name>\n'
    crlf = PARENT.replace("\n", "\r\n")

    # When the keys are carried
    in_front = carry_keys(front, WORK, [])
    in_crlf = carry_keys(crlf, WORK, ["x"])

    # Then the first is front matter with `wio = 1` before `id`, the second has
    # CRLF throughout, and each body is as it was
    assert in_front.text.startswith('+++\nwio = 1\nid = "k3m9xq"\ntemplate = "t"')
    assert in_front.text.endswith("+++\n\n# <Work name>\n")
    assert "\n" not in in_crlf.text.replace("\r\n", "")
    assert in_crlf.text.endswith("-->\r\n\r\n# <Work name>\r\n\r\n## Purpose\r\n")


def test_skeleton_note_names_the_keys_in_order_without_values() -> None:
    """The note is one line that names the dropped keys."""
    # Given a skeleton that dropped `roots`, `actions` and `x`
    skeleton = Skeleton("text", ("roots", "actions", "x"))

    # When the note is written for a path
    note = skeleton.note(Path(".agents/wio/works/w/README.md"))

    # Then it is the line of the contract
    assert note == (
        "note: .agents/wio/works/w/README.md: Not carried over: `roots`, `actions`, "
        "`x`. Use `--keep <key>` to carry one.\n"
    )


def test_skeleton_note_is_empty_when_nothing_was_dropped() -> None:
    """A skeleton that dropped nothing has no note."""
    # Given a skeleton that dropped nothing
    skeleton = Skeleton("text", ())

    # When the note is written
    note = skeleton.note(Path("w/README.md"))

    # Then it is empty
    assert note == ""
