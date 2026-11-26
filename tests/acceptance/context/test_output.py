# SPDX-License-Identifier: Apache-2.0
"""Delivery of context bundles to files."""

from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from tests.acceptance.channels import Channel

if TYPE_CHECKING:
    from tests.acceptance.dsl.wio import Wio
    from tests.sandbox import Sandbox

_CONTEXT_ARGS = ["context", "k3m9xq", "deliver", "implementation"]


@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
@pytest.mark.xfail(strict=True, raises=AssertionError, reason="output option pending")
def test_output_option_accepts_the_two_explicit_path_forms(wio: Wio) -> None:
    """AC-6: a bare option consumes the next argument as its path."""
    # Given a Work and its action and stage
    wio.fixture("context/unreadable")
    args = ["k3m9xq", "deliver", "implementation"]

    # When a bare option precedes the arguments, or is followed by a path
    missing = wio.run(["context", "--output", *args])
    named = wio.run(["context", "--output", "b.md", *args])
    equals = wio.run(["context", "--output=b.md", *args])

    # Then only the form without a path is a usage error
    assert (missing.exit_code, missing.stdout) == (2, "")
    assert (named.exit_code, equals.exit_code) == (0, 0)
    assert (named.stdout, equals.stdout) == ("b.md\n", "b.md\n")


@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
@pytest.mark.xfail(strict=True, raises=AssertionError, reason="default output pending")
def test_default_output_is_in_the_temporary_directory(
    wio: Wio, sandbox: Sandbox
) -> None:
    """AC-1: the default path is keyed by clone and bundle identity."""
    # Given a Work and a named temporary directory
    wio.fixture("context/unreadable")
    sandbox.env["TMPDIR"] = str(sandbox.root.parent / "temp")
    args = _CONTEXT_ARGS
    bundle = wio.run(args)
    bundle_id = bundle.stdout.splitlines()[0].removeprefix("bundle: ")

    # When the command requests the default output file
    result = wio.run([*args, "--output"])

    # Then the printed file holds the bundle under the temporary directory
    assert result.exit_code == 0
    path = Path(result.stdout.strip())
    assert path.parent.parent == Path(sandbox.env["TMPDIR"]) / "wio"
    assert path.name == f"{bundle_id}.md"
    assert path.read_text(encoding="utf-8") == bundle.stdout


@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
@pytest.mark.xfail(strict=True, raises=AssertionError, reason="output warnings pending")
def test_output_inside_the_worktree_warns(wio: Wio, sandbox: Sandbox) -> None:
    """AC-3: resolved paths inside the worktree warn, including a link."""
    # Given a Work, an outside link into its repository, and an outside path
    wio.fixture("context/unreadable")
    link = sandbox.root.parent / "link.md"
    link.symlink_to(sandbox.root / "linked.md")
    outside = sandbox.root.parent / "outside.md"
    args = _CONTEXT_ARGS
    paths = ["inside.md", str(link), str(outside)]

    # When the bundle is written to each path
    results = [wio.run([*args, "--output", path]) for path in paths]

    # Then the inside destinations warn and the outside destination does not
    assert all(result.exit_code == 0 for result in results)
    assert all("committed" in result.stderr for result in results[:2])
    assert "committed" not in results[2].stderr


@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
@pytest.mark.xfail(strict=True, raises=AssertionError, reason="output errors pending")
def test_invalid_output_paths_are_refused(wio: Wio, sandbox: Sandbox) -> None:
    """AC-5: an unwritable default, directory path, and empty path are refused."""
    # Given a Work and a temporary directory below a file
    wio.fixture("context/unreadable")
    blocker = sandbox.root.parent / "blocker"
    blocker.write_text("file", encoding="utf-8")
    sandbox.env["TMPDIR"] = str(blocker / "tmp")
    args = _CONTEXT_ARGS

    # When the default file, a directory, and an empty path are requested
    default = wio.run([*args, "--output"])
    directory = wio.run([*args, "--output", "."])
    empty = wio.run([*args, "--output="])

    # Then all are errors and the default explains its alternatives
    assert all(
        (result.exit_code, result.stdout) == (2, "")
        for result in (default, directory, empty)
    )
    assert "$TMPDIR" in default.stderr
    assert "--output" in default.stderr
    assert "." in directory.stderr


@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
@pytest.mark.xfail(strict=True, raises=AssertionError, reason="output details pending")
def test_output_keeps_the_last_option_and_does_not_expand_tilde(
    wio: Wio, sandbox: Sandbox
) -> None:
    """AC-7: a repeated option and literal tilde use their specified paths."""
    # Given a Work and a relative temporary directory
    wio.fixture("context/unreadable")
    sandbox.env["TMPDIR"] = "rel/tmp"
    args = _CONTEXT_ARGS

    # When a bare output follows a named one, and a tilde path is given
    default = wio.run([*args, "--output=x.md", "--output"])
    tilde = wio.run([*args, "--output", "~/b.md"])

    # Then the last option uses the relative temporary directory and tilde is literal
    assert (default.exit_code, tilde.exit_code) == (0, 0)
    assert default.stdout.startswith("rel/tmp/wio/")
    assert tilde.stdout == "~/b.md\n"
    assert (sandbox.root / "~" / "b.md").is_file()


@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
@pytest.mark.xfail(strict=True, raises=AssertionError, reason="file delivery pending")
def test_a_given_output_path_receives_the_bundle(wio: Wio) -> None:
    """AC-2: the named file is created and then replaced with the bundle."""
    # Given a Work and a path whose parent directory does not exist
    wio.fixture("context/unreadable")
    args = _CONTEXT_ARGS
    bundle = wio.run(args)

    # When the bundle is written to the path twice
    first = wio.run([*args, "--output", "out/b.md"])
    assert first.exit_code == 0
    wio.put("out/b.md", b"old text")
    second = wio.run([*args, "--output", "out/b.md"])

    # Then the path alone is printed and the file has exactly the bundle
    assert (first.stdout, second.stdout, second.exit_code) == (
        "out/b.md\n",
        "out/b.md\n",
        0,
    )
    assert wio.read("out/b.md").decode() == bundle.stdout
