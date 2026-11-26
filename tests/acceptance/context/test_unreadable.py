# SPDX-License-Identifier: Apache-2.0
"""Refusals of an unreadable config, tree, Work or rules by `wio context`."""

from typing import TYPE_CHECKING

import pytest

from tests.acceptance.channels import Channel

if TYPE_CHECKING:
    from tests.acceptance.dsl.wio import Output, Wio


_RUN = ["context", "k3m9xq", "deliver", "implementation"]
_CONFIG = ".agents/wio/config.toml"
_WORKS = ".agents/wio/works"
_RULES = ".agents/wio/rules"


def _marked(work_id: str, extra: str = "", body: str = "# Demo\n") -> bytes:
    """Write a contract with a metadata block.

    Args:
        work_id: The Work's id.
        extra: More lines of the block.
        body: The text after the block.

    Returns:
        The file's bytes.
    """
    return f'<!-- wio\nid = "{work_id}"\n{extra}-->\n\n{body}'.encode()


def _nested(wio: Wio) -> None:
    """Start from the sample project with its Works nested by directory.

    Args:
        wio: The scenario's facade.
    """
    wio.fixture("context/unreadable")
    wio.put(_CONFIG, wio.read(_CONFIG) + b'[works]\nhierarchy = "nesting"\n')


def _refused(result: Output, *named: str) -> None:
    """Require a refusal that prints no bundle and names what is at fault.

    Args:
        result: The output of the run.
        *named: Texts that standard error holds.
    """
    assert (result.exit_code, result.stdout) == (2, "")
    assert [text for text in named if text not in result.stderr] == []


@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
def test_a_config_with_an_error_is_refused(wio: Wio) -> None:
    """AC-1: the diagnostics are those that every command prints."""
    # Given a config with a key that the schema does not know
    wio.fixture("context/unreadable")
    wio.put(_CONFIG, b"mistyped = 1\n" + wio.read(_CONFIG))
    other = wio.run(["contracts", "list"])

    # When the context command runs
    result = wio.run(_RUN)

    # Then it prints that command's diagnostics and no bundle
    _refused(result, "mistyped")
    assert result.stderr == other.stderr


@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
def test_two_marked_files_in_a_directory_are_refused(wio: Wio) -> None:
    """AC-2: the refusal names both files."""
    # Given a nesting tree with a directory that holds two marked files
    _nested(wio)
    wio.put(f"{_WORKS}/pair/README.md", _marked("a1b2c3"))
    wio.put(f"{_WORKS}/pair/other.md", _marked("d4e5f6"))

    # When a Work of the tree is requested
    result = wio.run(_RUN)

    # Then both files are named
    _refused(result, "pair/README.md", "pair/other.md")


@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
def test_a_work_with_no_id_is_refused(wio: Wio) -> None:
    """AC-2: a marked file without an id leaves the tree incomplete."""
    # Given a marked file whose metadata block has no id
    wio.fixture("context/unreadable")
    wio.put(f"{_WORKS}/anonymous/README.md", b"<!-- wio\n-->\n\n# Anonymous\n")

    # When another Work of the tree is requested
    result = wio.run(_RUN)

    # Then the file is named
    _refused(result, "anonymous/README.md")


@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
@pytest.mark.parametrize(
    "argument", ["nope11", "works/a/README.md", ".agents/wio/works/demo/README.md"]
)
def test_an_id_that_no_work_has_is_refused(wio: Wio, argument: str) -> None:
    """AC-3: an argument that looks like a path is an id that no Work has."""
    # Given a complete tree
    wio.fixture("context/unreadable")

    # When the argument is the id of no Work
    result = wio.run(["context", argument, "deliver", "implementation"])

    # Then the refusal says that no Work has it
    _refused(result, f"No Work has the id `{argument}`.")


@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
def test_a_shared_id_refuses_only_its_own_lookup(wio: Wio) -> None:
    """AC-4: another Work of the tree still gets its bundle."""
    # Given two Works with one id and a third with its own
    wio.fixture("context/unreadable")
    wio.put(f"{_WORKS}/one/README.md", _marked("s1s1s1"))
    wio.put(f"{_WORKS}/two/README.md", _marked("s1s1s1"))

    # When the shared id and then the third Work are requested
    shared = wio.run(["context", "s1s1s1", "deliver", "implementation"])
    third = wio.run(_RUN)

    # Then only the shared id is refused, with both paths
    _refused(shared, "one/README.md", "two/README.md")
    assert third.exit_code == 0
    assert third.stdout.startswith("bundle: ")


@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
def test_faults_that_leave_the_tree_complete_do_not_refuse(wio: Wio) -> None:
    """AC-5: metadata, graph and template faults do not stop the bundle."""
    # Given a Work with a dangling dependency, an unknown key and no such
    # template, and another with a repeated heading and a mistyped dependency
    wio.fixture("context/unreadable")
    faults = 'depends_on = ["zzzzzz"]\nunknown = 1\ntemplate = "no.such"\n'
    wio.put(f"{_WORKS}/demo/README.md", _marked("k3m9xq", faults))
    repeated = "# Other\n\n## Goals\n\n## Goals\n"
    other = _marked("a1b2c3", "depends_on = 1\n", repeated)
    wio.put(f"{_WORKS}/other/README.md", other)

    # When the first Work is requested
    result = wio.run(_RUN)

    # Then the bundle is printed
    assert result.exit_code == 0
    assert result.stdout.startswith("bundle: ")


@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
@pytest.mark.parametrize(
    ("files", "named"),
    [
        (
            {
                "ruleset.toml": b'[families]\nARC = "Architecture"\n',
                "ERR001-undeclared.md": (
                    b'<!-- wio\ncode = "ERR001"\nname = "undeclared"\n-->\n\nText.\n'
                ),
            },
            "demo/ERR001-undeclared.md",
        ),
        (
            {
                "ARC001-no-manifest.md": (
                    b'<!-- wio\ncode = "ARC001"\nname = "no-manifest"\n-->\n\nText.\n'
                ),
            },
            ".agents/wio/rules/demo",
        ),
    ],
)
def test_a_fault_in_the_rules_is_refused(
    wio: Wio, files: dict[str, bytes], named: str
) -> None:
    """AC-6: the diagnostics are those of `wio rules`."""
    # Given a ruleset with a fault
    wio.fixture("context/unreadable")
    for name, data in files.items():
        wio.put(f"{_RULES}/demo/{name}", data)
    listed = wio.run(["rules", "list"])

    # When the context command runs
    result = wio.run(_RUN)

    # Then it names what is at fault with the diagnostics of `wio rules`
    _refused(result, named)
    assert result.stderr == listed.stderr
