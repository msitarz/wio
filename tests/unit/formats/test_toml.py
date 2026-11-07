# SPDX-License-Identifier: Apache-2.0
"""Tests of the TOML decoder in `wio.formats`."""

import json
import subprocess
import sys
from pathlib import Path

import pytest

from wio.errors import WioError
lazy from wio.formats import TomlSyntaxError, decode_toml

ROOT = Path(__file__).resolve().parents[3]
RUFF = Path(sys.executable).parent / "ruff"

FORMS = (
    "import tomllib",
    "from tomllib import loads",
    "import tomllib.x",
    "lazy import tomllib",
    "lazy from tomllib import loads",
)

_PROBE = """
import json, sys
import wio.formats
before = "tomllib" in sys.modules
wio.formats.decode_toml("a = 1")
sys.stdout.write(json.dumps([before, "tomllib" in sys.modules]))
"""


def test_a_toml_text_becomes_plain_data() -> None:
    """AC-1: a valid document is nested dicts, lists and scalars."""
    # Given a document with a key, a table, a string and a list, and an empty text
    text = 'a = 1\n[t]\ns = "x"\nl = [1, 2]\n'

    # When decode_toml runs on each
    data = decode_toml(text)
    empty = decode_toml("")

    # Then the document is returned as written, and the empty text gives {}
    assert data == {"a": 1, "t": {"s": "x", "l": [1, 2]}}
    assert empty == {}


def test_an_invalid_value_carries_its_position() -> None:
    """AC-2: a syntax error is a WioError with a message, a line and a column."""
    # Given a text whose second line is an invalid value
    text = "a = 1\nb = = 2\n"

    # When decode_toml runs
    with pytest.raises(TomlSyntaxError) as caught:
        decode_toml(text)

    # Then the error is a WioError at line 2, column 5, and str holds all three
    error = caught.value
    assert isinstance(error, WioError)
    assert (error.line, error.column) == (2, 5)
    assert error.message
    assert str(error) == f"{error.message} (line 2, column 5)"


@pytest.mark.parametrize(
    ("text", "position"),
    [("a = 1\na = 2\n", (2, 6)), ('a = "x', (1, 7))],
)
def test_a_duplicate_key_and_an_unterminated_string_are_placed(
    text: str, position: tuple[int, int]
) -> None:
    """AC-2: the position is the problem's, not the start of the text."""
    # Given a text with a duplicate key, or an unterminated string

    # When decode_toml runs on it
    with pytest.raises(TomlSyntaxError) as caught:
        decode_toml(text)

    # Then the error is at the position of the problem
    assert (caught.value.line, caught.value.column) == position


@pytest.mark.slow
@pytest.mark.parametrize("form", FORMS)
def test_only_wio_formats_may_import_tomllib(form: str) -> None:
    """AC-3: ruff reports every form outside `wio.formats`, and only there."""
    # Given a probe file holding one form of the import

    # When it is linted as a file of wio.config, of wio.formats and of tests
    reported = {
        path: _tid251(form, path)
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
def test_importing_the_decoder_loads_no_toml_parser() -> None:
    """AC-4: `tomllib` loads on the first decode, not on import."""
    # Given a new Python process

    # When it imports wio.formats, checks sys.modules, decodes, and checks again
    done = subprocess.run(
        [sys.executable, "-c", _PROBE],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )

    # Then tomllib is absent the first time and present the second
    assert json.loads(done.stdout) == [False, True]


def _tid251(source: str, filename: str) -> bool:
    """Say whether ruff reports `TID251` for source linted as the given file.

    Args:
        source: The text of the probe.
        filename: The path to lint it as, which picks the per-file ignores.

    Returns:
        Whether the rule `TID251` was reported.
    """
    done = subprocess.run(
        [
            str(RUFF),
            "check",
            "--select",
            "TID251",
            "--stdin-filename",
            filename,
            "--output-format",
            "json",
            "-",
        ],
        cwd=ROOT,
        input=source,
        capture_output=True,
        text=True,
        check=False,
    )
    found: list[dict[str, object]] = json.loads(done.stdout)
    return any(item["code"] == "TID251" for item in found)
