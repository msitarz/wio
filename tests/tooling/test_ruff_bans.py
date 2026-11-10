# SPDX-License-Identifier: Apache-2.0
"""Tests that ruff bans, outside their one place, what the design bans."""

import pytest

from tests.tooling.ruff import banned_api

FORMS = (
    "import tomllib",
    "from tomllib import loads",
    "import tomllib.x",
    "lazy import tomllib",
    "lazy from tomllib import loads",
)

CWD_PROBE = (
    "import os\nfrom pathlib import Path\n\n"
    "HERE = (Path.cwd(), os.getcwd(), os.getcwdb())\n"
)


@pytest.mark.slow
@pytest.mark.parametrize("form", FORMS)
def test_only_wio_formats_may_import_tomllib(form: str) -> None:
    """AC-3 of the decoder: ruff reports every form outside `wio.formats`."""
    # Given a probe file holding one form of the import

    # When it is linted as a file of wio.config, of wio.formats and of tests
    reported = {
        path: bool(banned_api(form, path))
        for path in (
            "src/wio/config/probe.py",
            "src/wio/formats/probe.py",
            "tests/unit/probe.py",
        )
    }

    # Then it is reported the first time and neither of the other times
    assert reported == {
        "src/wio/config/probe.py": True,
        "src/wio/formats/probe.py": False,
        "tests/unit/probe.py": False,
    }


@pytest.mark.slow
def test_only_the_environment_adapter_may_read_the_working_directory() -> None:
    """AC-5 of the ports: ruff bans `Path.cwd` and `os.getcwd` outside the adapter."""
    # Given probes that read the working directory, linted as other files

    # When ruff checks each
    reported = {
        name: len(banned_api(CWD_PROBE, name))
        for name in (
            "src/wio/io/probe.py",
            "src/wio/env/probe.py",
            "src/wio/env/adapters.py",
        )
    }

    # Then only the adapter of the environment is let through
    assert reported == {
        "src/wio/io/probe.py": 3,
        "src/wio/env/probe.py": 3,
        "src/wio/env/adapters.py": 0,
    }


@pytest.mark.skip(reason="Pending the implementation stage.")
@pytest.mark.slow
def test_only_wio_formats_may_import_markdown_it() -> None:
    """AC-5: ruff reports an import of the Markdown parser outside `wio.formats`."""
    # Given a probe file that imports `markdown_it`
    # When it is linted as a file of wio.templates and of wio.formats
    # Then it is reported for the first and not for the second
