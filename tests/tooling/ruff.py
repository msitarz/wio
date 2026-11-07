# SPDX-License-Identifier: Apache-2.0
"""Run ruff on a probe, to see how the repository's lint rules treat a file."""

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
_RUFF = Path(sys.executable).parent / "ruff"


def banned_api(source: str, filename: str) -> list[str]:
    """List what the `banned-api` rule (`TID251`) reports for a probe.

    Args:
        source: The text of the probe.
        filename: The path to lint it as, which picks the per-file ignores.

    Returns:
        The message of each report of `TID251`, empty when the rule is silent.
    """
    done = subprocess.run(
        [
            str(_RUFF),
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
    found: list[dict[str, str]] = json.loads(done.stdout)
    return [item["message"] for item in found if item["code"] == "TID251"]
