# SPDX-License-Identifier: Apache-2.0
"""Warnings for stages that need a Work's roots."""

from typing import TYPE_CHECKING

import pytest

from tests.acceptance.channels import Channel
from tests.acceptance.drivers.stub_warning import (
    WarningStubReachedError,
    identify_warning_stub,
)

if TYPE_CHECKING:
    from tests.acceptance.dsl.wio import Wio


class _WarningNotWiredError(Exception):
    """The bundle is valid, but the warning is not wired yet."""


@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
@pytest.mark.xfail(strict=True, raises=(WarningStubReachedError, _WarningNotWiredError))
def test_empty_work_roots_warn_for_both_selection_forms(wio: Wio) -> None:
    """AC-1: empty, absent and descendant roots warn with a bundle."""
    # Given a Work and stages selecting its roots implicitly or with @work
    wio.fixture("context/no-roots")

    # When each way to have no roots is used with both stages
    results = []
    for roots in ("roots = []\n", "", 'roots = ["@descendants"]\n'):
        work = f'<!-- wio\nid = "k3m9xq"\n{roots}-->\n\n# Demo\n'
        wio.put(".agents/wio/works/demo/README.md", work.encode())
        results.extend(
            wio.run(["context", "k3m9xq", "deliver", stage])
            for stage in ("implementation", "explicit")
        )

    # Then every run prints a bundle and one warning naming the Work
    for result in results:
        identify_warning_stub(result.exit_code, result.stdout, result.stderr)
        assert result.exit_code == 0
        assert result.stdout.startswith("bundle: ")
    if all(not result.stderr for result in results):
        raise _WarningNotWiredError
    for result in results:
        assert len(result.stderr.splitlines()) == 1
        assert "warning:" in result.stderr
        assert "k3m9xq" in result.stderr
        assert "no roots" in result.stderr


@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
@pytest.mark.xfail(
    strict=True, raises=WarningStubReachedError, reason="Warning is stubbed"
)
def test_no_warning_when_work_roots_exist_or_are_not_selected(wio: Wio) -> None:
    """AC-2: present roots and stages with their own roots need no warning."""
    # Given a Work with roots and stages selecting or excluding them
    wio.fixture("context/no-roots")
    wio.put(
        ".agents/wio/works/demo/README.md",
        b'<!-- wio\nid = "k3m9xq"\nroots = ["api"]\n-->\n\n# Demo\n',
    )

    # When its roots are selected and an empty Work's roots are not selected
    present = wio.run(["context", "k3m9xq", "deliver", "implementation"])
    wio.put(
        ".agents/wio/works/demo/README.md",
        b'<!-- wio\nid = "k3m9xq"\nroots = []\n-->\n\n# Demo\n',
    )
    unselected = [
        wio.run(["context", "k3m9xq", "deliver", stage]) for stage in ("own", "empty")
    ]

    # Then every run succeeds without a warning
    for result in (present, *unselected):
        identify_warning_stub(result.exit_code, result.stdout, result.stderr)
        assert result.exit_code == 0
        assert result.stdout.startswith("bundle: ")
        assert result.stderr == ""
