# SPDX-License-Identifier: Apache-2.0
"""Delivery of context bundles to files."""

import hashlib
import os
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from tests.acceptance.channels import Channel
from tests.sandbox import unreadable

if TYPE_CHECKING:
    from tests.acceptance.dsl.wio import Wio
    from tests.sandbox import Sandbox

_CONTEXT_ARGS = ["context", "k3m9xq", "deliver", "implementation"]


@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
def test_output_option_accepts_the_two_explicit_path_forms(wio: Wio) -> None:
    """AC-6: a bare option consumes the next argument as its path."""
    # Given a Work and its action and stage
    wio.fixture("context/unreadable")
    args = ["k3m9xq", "deliver", "implementation"]

    # When a bare option precedes the arguments, or is followed by a path
    missing = wio.run(["context", "--output", *args])
    named = wio.run(["context", "--output", "b.md", *args])
    equals = wio.run(["context", "--output=c.md", *args])

    # Then only the form without a path is a usage error
    assert (missing.exit_code, missing.stdout) == (2, "")
    assert (named.exit_code, equals.exit_code) == (0, 0)
    assert (named.stdout, equals.stdout) == ("b.md\n", "c.md\n")
    assert wio.read("b.md").startswith(b"bundle: ")
    assert wio.read("c.md").startswith(b"bundle: ")


@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
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
    identity = sandbox.root.resolve() / ".git"
    digest = hashlib.sha256(os.fsencode(identity)).hexdigest()[:12]
    expected = Path(sandbox.env["TMPDIR"]) / "wio" / f"repo-{digest}"
    assert path == expected / f"{bundle_id}.md"
    assert result.stdout == f"{path}\n"
    assert path.read_text(encoding="utf-8") == bundle.stdout


@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
def test_output_inside_the_worktree_warns(wio: Wio, sandbox: Sandbox) -> None:
    """AC-3: resolved paths inside the worktree warn, including a link."""
    # Given inside paths, a link into the worktree and an outside path
    wio.fixture("context/unreadable")
    link = sandbox.root.parent / "link.md"
    link.symlink_to(sandbox.root / "linked.md")
    outside = sandbox.root.parent / "outside.md"
    (sandbox.root / "sub").mkdir()
    sandbox.env["TMPDIR"] = str(sandbox.root / "tmp")
    paths = [str(sandbox.root / "absolute.md"), "inside.md", "sub/../dot.md", str(link)]

    # When each path, the outside path, and the default are requested
    inside = [wio.run([*_CONTEXT_ARGS, "--output", path]) for path in paths]
    external = wio.run([*_CONTEXT_ARGS, "--output", str(outside)])
    default = wio.run([*_CONTEXT_ARGS, "--output"])

    # Then every path is written, with a warning only for the inside paths
    assert all(result.exit_code == 0 for result in (*inside, external, default))
    for result in (*inside, default):
        assert "uncommitted" in result.stderr
        assert "committed" in result.stderr
        assert (
            Path(result.stdout.strip()).is_file()
            if Path(result.stdout.strip()).is_absolute()
            else (sandbox.root / result.stdout.strip()).is_file()
        )
    assert "uncommitted" not in external.stderr
    assert outside.is_file()


@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
def test_invalid_output_paths_are_refused(wio: Wio, sandbox: Sandbox) -> None:
    """AC-5: an unwritable default, directory path, and empty path are refused."""
    # Given a Work and an existing unwritable temporary directory
    wio.fixture("context/unreadable")
    temporary = sandbox.root.parent / "closed-temp"
    temporary.mkdir()
    sandbox.env["TMPDIR"] = str(temporary)
    args = _CONTEXT_ARGS

    # When the default file, a directory, and an empty path are requested
    with unreadable(temporary):
        default = wio.run([*args, "--output"])
    directory = wio.run([*args, "--output", str(sandbox.root)])
    empty = wio.run([*args, "--output="])

    # Then all are errors and the default explains its alternatives
    assert all(
        (result.exit_code, result.stdout) == (2, "")
        for result in (default, directory, empty)
    )
    assert "$TMPDIR" in default.stderr
    assert "--output <path>" in default.stderr
    bundle = wio.run(args)
    bundle_id = bundle.stdout.splitlines()[0].removeprefix("bundle: ")
    identity = sandbox.root.resolve() / ".git"
    digest = hashlib.sha256(os.fsencode(identity)).hexdigest()[:12]
    failed_path = temporary / "wio" / f"repo-{digest}" / f"{bundle_id}.md"
    assert str(failed_path) in default.stderr
    assert str(sandbox.root) in directory.stderr
    assert "$TMPDIR" not in directory.stderr
    assert "--output" not in directory.stderr
    assert "usage:" in empty.stderr


@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
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
    sandbox.env["TMPDIR"] = str(sandbox.root.parent / "new-temp")
    missing = wio.run([*args, "--output"])

    # Then the last option uses the relative temporary directory and tilde is literal
    assert (default.exit_code, tilde.exit_code, missing.exit_code) == (0, 0, 0)
    assert default.stdout.startswith("rel/tmp/wio/")
    assert (sandbox.root / default.stdout.strip()).is_file()
    assert Path(missing.stdout.strip()).is_file()
    assert tilde.stdout == "~/b.md\n"
    assert (sandbox.root / "~" / "b.md").is_file()


@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
def test_a_given_output_path_receives_the_bundle(wio: Wio) -> None:
    """AC-2: the named file is created and then replaced with the bundle."""
    # Given a Work and a path whose parent directory does not exist
    wio.fixture("context/unreadable")
    args = _CONTEXT_ARGS
    bundle = wio.run(args)

    # When the bundle is written to the path twice
    first = wio.run([*args, "--output", "out/b.md"])
    assert first.exit_code == 0
    assert wio.read("out/b.md").decode() == bundle.stdout
    wio.put("out/b.md", b"old text")
    second = wio.run([*args, "--output", "out/b.md"])

    # Then the path alone is printed and the file has exactly the bundle
    assert (first.stdout, second.stdout, second.exit_code) == (
        "out/b.md\n",
        "out/b.md\n",
        0,
    )
    assert wio.read("out/b.md").decode() == bundle.stdout


@pytest.mark.usefixtures("unavailable_temp")
def test_unusable_system_temp_is_reported_by_the_command(wio: Wio) -> None:
    """AC-5: an unavailable system directory is a user-facing error."""
    # Given a Work and an unavailable system temporary directory
    wio.fixture("context/unreadable")

    # When the command requests its default output
    result = wio.run([*_CONTEXT_ARGS, "--output"])

    # Then it refuses without output and explains both alternatives
    assert (result.exit_code, result.stdout) == (2, "")
    assert "$TMPDIR" in result.stderr
    assert "--output <path>" in result.stderr
