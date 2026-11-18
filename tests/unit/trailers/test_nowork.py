# SPDX-License-Identifier: Apache-2.0
"""Tests of the `none` form of `wio trailers`, run with fakes of its ports.

The examples use the services of `test_command.py`. The form takes no argument, so
the calls differ only in what follows `none`.
"""

import pytest

from tests.unit.trailers.test_command import _form
from wio.trailers.errors import TrailersError

ARCHITECTURE_STUB = "architecture stub: the form is declared in nowork.pyi"


@pytest.mark.skip(reason=ARCHITECTURE_STUB)
def test_the_none_form_prints_the_record_for_no_work() -> None:
    """AC-1: `none` alone prints `Wio-Work: none` and a newline."""
    # Given the services of the command
    # When `wio trailers none` runs
    code, out, err = _form(["none"])

    # Then it exits 0 and prints exactly the record, with nothing on standard error
    assert (code, out, err) == (0, "Wio-Work: none\n", "")


@pytest.mark.skip(reason=ARCHITECTURE_STUB)
@pytest.mark.parametrize(
    "forms",
    [
        ["none", "deliver", "architecture"],
        ["none", "--items", "AC-1"],
        ["none", "--result", "pass"],
        ["none", "--judge", "human"],
        ["none", "--cite", "AC-1=pass"],
    ],
    ids=["action and stage", "items", "result", "judge", "cite"],
)
def test_the_none_form_takes_no_argument(forms: list[str]) -> None:
    """AC-2: an action, a stage or an option after `none` is a usage mistake."""
    # Given the services of the command
    # When `wio trailers none` runs with an action and a stage, and with each option
    # Then each raises the usage mistake that `wio.cli` turns into exit 2
    with pytest.raises(TrailersError):
        _form(forms)
