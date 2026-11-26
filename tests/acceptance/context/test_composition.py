# SPDX-License-Identifier: Apache-2.0
"""System criteria for the composition of context bundles."""

import hashlib
from typing import TYPE_CHECKING

import pytest

from tests.acceptance.channels import Channel
from tests.acceptance.drivers.stub_warning import (
    WarningStubReachedError,
    identify_warning_stub,
)

if TYPE_CHECKING:
    from tests.acceptance.dsl.wio import Wio


@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
@pytest.mark.xfail(
    strict=True, raises=WarningStubReachedError, reason="Warning is stubbed"
)
def test_bundle_identity_and_body_size_for_goal_and_skill(wio: Wio) -> None:
    """AC-1: both kinds of stage state the identity and size of their text."""
    # Given a Work with goal and skill stages
    wio.fixture("context/composition")

    # When a bundle is composed for each stage
    bundles = [
        wio.run(["context", "k3m9xq", "deliver", stage]) for stage in ("goal", "skill")
    ]

    # Then each identity covers the header and body, and the size covers the body
    for bundle in bundles:
        identify_warning_stub(bundle.exit_code, bundle.stdout, bundle.stderr)
        assert (bundle.exit_code, bundle.stderr) == (0, "")
        metadata, text = bundle.stdout.split("\n\n", 1)
        header, body = text.split("\n\n", 1)
        assert metadata == f"bundle: {hashlib.sha256(text.encode()).hexdigest()[:12]}"
        assert (
            f"size: {len(body.encode())} bytes, {body.count(chr(10))} lines (body)"
            in header
        )


@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
@pytest.mark.xfail(
    strict=True, raises=WarningStubReachedError, reason="Warning is stubbed"
)
def test_skill_pointer_and_header_agree_on_directory_and_files(wio: Wio) -> None:
    """AC-2: the pointer and header describe the same two-file skill."""
    # Given a skill with its instruction and a reference
    wio.fixture("context/composition")

    # When its stage is composed
    bundle = wio.run(["context", "k3m9xq", "deliver", "skill"])
    expected = hashlib.sha256(
        b"SKILL.md\0# Example\n\0references/guide.md\0# Reference\n\0"
    ).hexdigest()

    # Then the header has the files hash and directory used by the pointer
    identify_warning_stub(bundle.exit_code, bundle.stdout, bundle.stderr)
    assert (bundle.exit_code, bundle.stderr) == (0, "")
    assert f"skill: example (.agents/skills/example, files {expected})" in bundle.stdout
    assert "`.agents/skills/example/SKILL.md`" in bundle.stdout
