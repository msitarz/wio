# SPDX-License-Identifier: Apache-2.0
"""Scenarios of `wio contracts skeleton`, which prepares a Work's skeleton."""

import tomllib
from typing import TYPE_CHECKING

import pytest

from tests.acceptance.channels import Channel

if TYPE_CHECKING:
    from tests.acceptance.dsl.results import Output
    from tests.acceptance.dsl.wio import Wio

WORKS = ".agents/wio/works"
TEMPLATES = ".agents/wio/templates"
HINT = "`wio contracts check` shows every problem."
CONFIG = """\
[works]
hierarchy = "nesting"

[templates.kinds]
feature = "feature.parent"
"""
WORK = """\
<!-- wio
id = "k3m9xq"
template = "feature.leaf"
roots = ["api"]
depends_on = ["a7b2c4"]

[actions]
deliver = ["ship"]

[x]
ticket = "PAY-1"
-->

# Pay
"""
PARENT = """\
<!-- wio
kind = "feature"

[contract]
roots = ["@descendants"]
depends_on = []
-->

# <Work name>

## Purpose
"""
TABLED = """\
<!-- wio
kind = "feature"

[contract]
roots = []

[contract.x]
ticket = ""
-->

# <Work name>

## Purpose
"""
FRONT = """\
+++
wio = 1
kind = "feature"

[contract]
roots = []
+++

# <Work name>
"""
BAD = '<!-- wio\nkind = "feature"\nbogus = 1\n-->\n\n# Bad\n'
BODY = "\n# <Work name>\n\n## Purpose\n"
NOTE = (
    "note: .agents/wio/works/w/README.md: Not carried over: `roots`, `actions`, "
    "`x`. Use `--keep <key>` to carry one.\n"
)


def _put(wio: Wio, files: dict[str, str | bytes]) -> None:
    """Write files into the repository of the scenario.

    Args:
        wio: The facade.
        files: The files, by path relative to the root of the repository.
    """
    for path, text in files.items():
        wio.put(path, text if isinstance(text, bytes) else text.encode())


def _project(wio: Wio, work: str = WORK) -> None:
    """Build the project of AC-1: a Work and the templates it may move to.

    Args:
        wio: The facade.
        work: The text of the Work `k3m9xq`.
    """
    wio.fixture("contracts/show-base")
    _put(
        wio,
        {
            ".agents/wio/config.toml": CONFIG,
            f"{TEMPLATES}/feature.parent.md": PARENT,
            f"{TEMPLATES}/t.tabled.md": TABLED,
            f"{TEMPLATES}/t.front.md": FRONT,
            f"{TEMPLATES}/t.crlf.md": PARENT.replace("\n", "\r\n"),
            f"{TEMPLATES}/bad.md": BAD,
            f"{WORKS}/w/README.md": work,
        },
    )


def _skeleton(wio: Wio, *arguments: str) -> Output:
    """Run `wio contracts skeleton`.

    Args:
        wio: The facade.
        arguments: What follows `skeleton`.

    Returns:
        What it wrote and its exit code.
    """
    return wio.run(["contracts", "skeleton", *arguments])


def _split(text: str) -> tuple[dict[str, object], str]:
    """Split a skeleton into its block's data and its body.

    Args:
        text: The skeleton, in the comment form or in front matter.

    Returns:
        The decoded keys in the order written, and the text after the block.
    """
    text = text.replace("\r\n", "\n")
    if text.startswith("+++\n"):
        head, _, body = text[4:].partition("\n+++\n")
    else:
        head, _, body = text.removeprefix("<!-- wio\n").partition("-->\n")
    return tomllib.loads(head), body


def _refused(output: Output) -> bool:
    """Tell a refusal from a skeleton.

    Args:
        output: What the command wrote.

    Returns:
        Whether it exited 2 with nothing on standard output.
    """
    return output.stdout == "" and output.exit_code == 2


@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
def test_a_moved_leaf_keeps_its_identity_and_names_what_it_dropped(
    wio: Wio,
) -> None:
    """AC-1: a leaf moved to the parent template."""
    # Given the Work `k3m9xq` with roots, an `[actions]` table and an `[x]`
    # table, and the template `feature.parent`
    _project(wio)
    before = wio.fingerprint(WORKS)

    # When `wio contracts skeleton feature.parent --work k3m9xq` runs
    output = _skeleton(wio, "feature.parent", "--work", "k3m9xq")

    # Then standard output has the values and body of AC-1, standard error is the
    # note, nothing is written and it exits 0
    data, body = _split(output.stdout)
    assert data == {
        "id": "k3m9xq",
        "template": "feature.parent",
        "roots": ["@descendants"],
        "depends_on": ["a7b2c4"],
    }
    assert next(iter(data)) == "id"
    assert body == BODY
    assert output.stderr == NOTE
    assert (output.exit_code, wio.fingerprint(WORKS)) == (0, before)


@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
def test_keep_replaces_a_key_and_the_note_names_only_what_is_still_dropped(
    wio: Wio,
) -> None:
    """AC-2: roots and a table are kept."""
    # Given the Work and the template of AC-1
    _project(wio)

    # When the command runs with `--keep roots --keep x`
    output = _skeleton(
        wio, "feature.parent", "--work", "k3m9xq", "--keep", "roots", "--keep", "x"
    )

    # Then standard output has `roots` and `[x]` of the Work, and the note names
    # only `actions`
    data, body = _split(output.stdout)
    assert data == {
        "id": "k3m9xq",
        "template": "feature.parent",
        "roots": ["api"],
        "depends_on": ["a7b2c4"],
        "x": {"ticket": "PAY-1"},
    }
    assert body == BODY
    assert output.stderr == (
        "note: .agents/wio/works/w/README.md: Not carried over: `actions`. "
        "Use `--keep <key>` to carry one.\n"
    )
    assert output.exit_code == 0


@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
def test_keeping_everything_leaves_no_note(wio: Wio) -> None:
    """AC-2: every key is kept."""
    # Given the Work and the template of AC-1
    _project(wio)

    # When the command runs with `--keep roots --keep actions --keep x`
    output = _skeleton(
        wio,
        *("feature.parent", "--work", "k3m9xq"),
        *("--keep", "roots", "--keep", "actions", "--keep", "x"),
    )

    # Then standard output has all three and standard error is empty
    data, _ = _split(output.stdout)
    assert data["roots"] == ["api"]
    assert data["actions"] == {"deliver": ["ship"]}
    assert data["x"] == {"ticket": "PAY-1"}
    assert (output.stderr, output.exit_code) == ("", 0)


@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
def test_a_kept_table_replaces_the_template_s_own_and_is_added_when_it_has_none(
    wio: Wio,
) -> None:
    """AC-2: a template with a table of its own."""
    # Given the Work of AC-1 and the template `t.tabled` with its own `[x]`
    _project(wio)

    # When `wio contracts skeleton t.tabled --work k3m9xq --keep actions` runs
    output = _skeleton(wio, "t.tabled", "--work", "k3m9xq", "--keep", "actions")

    # Then the template's `[x]` and `roots = []` stand, `[actions]` is added, and
    # the note names `roots` and `x`
    data, body = _split(output.stdout)
    assert data == {
        "id": "k3m9xq",
        "template": "t.tabled",
        "roots": [],
        "depends_on": ["a7b2c4"],
        "x": {"ticket": ""},
        "actions": {"deliver": ["ship"]},
    }
    assert body == BODY
    assert output.stderr == (
        "note: .agents/wio/works/w/README.md: Not carried over: `roots`, `x`. "
        "Use `--keep <key>` to carry one.\n"
    )


@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
def test_a_bare_work_and_a_front_matter_work_differ_from_templates_show_only_by_the_id(
    wio: Wio,
) -> None:
    """AC-3: a bare Work and a `+++` Work."""
    # Given the Works `k3m9xq` and `p5n2hv`, bare and in `+++` form, and the
    # template `feature.parent`
    _project(wio, '<!-- wio\nid = "k3m9xq"\n-->\n\n# Bare\n')
    _put(
        wio,
        {f"{WORKS}/p/README.md": '+++\nwio = 1\nid = "p5n2hv"\n+++\n\n# Front\n'},
    )

    # When the command runs for each and `wio templates show feature.parent` runs
    bare = _skeleton(wio, "feature.parent", "--work", "k3m9xq")
    front = _skeleton(wio, "feature.parent", "--work", "p5n2hv")
    shown = wio.run(["templates", "show", "feature.parent"])

    # Then each skeleton is the output of `templates show` with the `id` first,
    # and standard error is empty
    base, base_body = _split(shown.stdout)
    for output, work_id in ((bare, "k3m9xq"), (front, "p5n2hv")):
        data, body = _split(output.stdout)
        assert output.stdout.startswith("<!-- wio\n")
        assert next(iter(data)) == "id"
        assert data == {"id": work_id, **base}
        assert body == base_body
        assert (output.stderr, output.exit_code) == ("", 0)


@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
def test_a_front_matter_template_keeps_its_form(wio: Wio) -> None:
    """AC-3: a template in front matter."""
    # Given the Work of AC-1 and the template `t.front`
    _project(wio)

    # When `wio contracts skeleton t.front --work k3m9xq` runs
    output = _skeleton(wio, "t.front", "--work", "k3m9xq")

    # Then it is in `+++` form with `wio = 1`, `id` and `template` in that order
    assert output.stdout.startswith('+++\nwio = 1\nid = "k3m9xq"\ntemplate = "t.front"')


# The CLI channel decodes the output as text, which folds CRLF into LF, so only
# the channel that reads the streams as they are can see the endings.
@pytest.mark.channels(Channel.IN_PROCESS)
def test_a_crlf_template_has_crlf_endings_throughout(wio: Wio) -> None:
    """AC-3: a template with CRLF."""
    # Given the Work of AC-1 and the template `t.crlf`
    _project(wio)

    # When `wio contracts skeleton t.crlf --work k3m9xq --keep x` runs
    output = _skeleton(wio, "t.crlf", "--work", "k3m9xq", "--keep", "x")

    # Then it has CRLF endings throughout, including the kept table
    assert "\r\n" in output.stdout
    assert "\n" not in output.stdout.replace("\r\n", "")
    assert '\r\n[x]\r\nticket = "PAY-1"\r\n' in output.stdout


@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
def test_each_mistake_prints_nothing_and_says_what_to_do(wio: Wio) -> None:
    """AC-4: each mistake."""
    # Given the Work of AC-1, two Works that share an id and a rejected template
    _project(wio)
    _put(
        wio,
        {
            f"{WORKS}/s1/README.md": '<!-- wio\nid = "a7b2c4"\n-->\n\n# One\n',
            f"{WORKS}/s2/README.md": '<!-- wio\nid = "a7b2c4"\n-->\n\n# Two\n',
        },
    )
    template = "feature.parent"

    # When the command runs with each mistake in turn
    unknown = _skeleton(wio, template, "--work", "k3m9xr")
    shared = _skeleton(wio, template, "--work", "a7b2c4")
    nosuch = _skeleton(wio, template, "--work", "k3m9xq", "--keep", "nosuch")
    cannot = {
        key: _skeleton(wio, template, "--work", "k3m9xq", "--keep", key)
        for key in ("id", "template", "depends_on", "wio")
    }
    missing = _skeleton(wio, "nosuch", "--work", "k3m9xq")
    rejected = _skeleton(wio, "bad", "--work", "k3m9xq")
    no_work = _skeleton(wio, template)
    other = _skeleton(wio, template, "--work", "k3m9xq")

    # Then each exits 2 with its own message and nothing on standard output, and a
    # lookup of another id is not refused by the shared one
    every = [unknown, shared, nosuch, missing, rejected, no_work, *cannot.values()]
    assert all(_refused(output) for output in every)
    assert "No Work has the id `k3m9xr`" in unknown.stderr
    assert "`k3m9xq`" in unknown.stderr
    assert f"{WORKS}/s1/README.md" in shared.stderr
    assert f"{WORKS}/s2/README.md" in shared.stderr
    assert "no key `nosuch`" in nosuch.stderr
    assert "`roots`, `actions`, `x`" in nosuch.stderr
    for key, output in cannot.items():
        assert f"`{key}` cannot be kept" in output.stderr
    assert "`nosuch` was not found; run `wio templates list`" in missing.stderr
    assert "`bad` is rejected; run `wio templates check`" in rejected.stderr
    assert "`--work` is required" in no_work.stderr
    assert "wio templates show" in no_work.stderr
    assert other.stdout.startswith('<!-- wio\nid = "k3m9xq"')
    assert other.exit_code == 0


@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
def test_a_tree_that_is_not_complete_refuses_the_command(wio: Wio) -> None:
    """AC-4: an unreadable Work file."""
    # Given the Work of AC-1 and an unreadable Work file
    _project(wio)
    wio.put(f"{WORKS}/u/README.md", b"\xff\xfe")

    # When `wio contracts skeleton feature.parent --work k3m9xq` runs
    output = _skeleton(wio, "feature.parent", "--work", "k3m9xq")

    # Then it exits 2 with the error of finding the Works and the pointer to
    # `wio contracts check`, and nothing on standard output
    assert _refused(output)
    assert f"{WORKS}/u/README.md" in output.stderr
    assert output.stderr.endswith(HINT + "\n")


@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
def test_a_wrong_type_of_depends_on_is_carried_as_the_file_has_it(wio: Wio) -> None:
    """AC-4: a `depends_on` that is a string."""
    # Given a Work whose `depends_on` is the string `"a7b2c4"`
    _project(wio, '<!-- wio\nid = "k3m9xq"\ndepends_on = "a7b2c4"\n-->\n\n# Odd\n')

    # When the command runs
    output = _skeleton(wio, "feature.parent", "--work", "k3m9xq")

    # Then it prints `depends_on = "a7b2c4"` and exits 0
    data, _ = _split(output.stdout)
    assert data["depends_on"] == "a7b2c4"
    assert 'depends_on = "a7b2c4"' in output.stdout
    assert (output.stderr, output.exit_code) == ("", 0)


@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
def test_several_mistakes_report_only_the_first_of_the_order(wio: Wio) -> None:
    """AC-4: a usage error and an incomplete tree come before the rest."""
    # Given the tree of the mistakes, an unreadable file and a rejected template
    _project(wio)
    wio.put(f"{WORKS}/u/README.md", b"\xff\xfe")

    # When `skeleton bad` and `skeleton bad --work k3m9xr --keep nosuch` run
    usage = _skeleton(wio, "bad")
    tree = _skeleton(wio, "bad", "--work", "k3m9xr", "--keep", "nosuch")

    # Then the first reports only that `--work` is required and the second only
    # the error of finding the Works
    assert _refused(usage)
    assert "`--work` is required" in usage.stderr
    assert "unreadable" not in usage.stderr
    assert _refused(tree)
    assert tree.stderr.endswith(HINT + "\n")
    assert "No Work has" not in tree.stderr
    assert "rejected" not in tree.stderr
    assert "nosuch" not in tree.stderr


@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
def test_nothing_is_written_and_two_runs_print_the_same_bytes(wio: Wio) -> None:
    """AC-5: twice, with and without `--keep roots`."""
    # Given the Work and the template of AC-1 and a hash of each contract
    _project(wio)
    before = wio.fingerprint(WORKS)
    arguments = ("feature.parent", "--work", "k3m9xq")

    # When the command runs twice, with and without `--keep roots`
    plain = [_skeleton(wio, *arguments) for _ in range(2)]
    kept = [_skeleton(wio, *arguments, "--keep", "roots") for _ in range(2)]

    # Then the outputs of each are identical and no contract changed
    assert plain[0] == plain[1]
    assert kept[0] == kept[1]
    assert plain[0] != kept[0]
    assert wio.fingerprint(WORKS) == before
