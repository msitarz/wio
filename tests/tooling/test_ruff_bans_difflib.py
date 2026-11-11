# SPDX-License-Identifier: Apache-2.0
"""Tests that ruff bans `difflib` outside `wio.formats`."""

import pytest

from tests.tooling.ruff import banned_api

FORMS = (
    "import difflib",
    "from difflib import get_close_matches",
    "lazy import difflib",
    "lazy from difflib import get_close_matches",
)


@pytest.mark.slow
@pytest.mark.parametrize("form", FORMS)
def test_only_wio_formats_may_import_difflib(form: str) -> None:
    """AC-4: ruff reports `TID251` for `difflib` outside `wio.formats`."""
    # Given a probe file that imports `difflib` in one form
    # When it is linted as a file of wio.config and as a file of wio.formats
    reported = {
        path: bool(banned_api(form, path))
        for path in ("src/wio/config/probe.py", "src/wio/formats/probe.py")
    }

    # Then it is reported for the first and not for the second
    assert reported == {
        "src/wio/config/probe.py": True,
        "src/wio/formats/probe.py": False,
    }
