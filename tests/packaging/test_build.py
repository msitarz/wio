# SPDX-License-Identifier: Apache-2.0
"""Packaging tests: build the wheel and sdist, then inspect them."""

import re
import shutil
import subprocess
import tarfile
import zipfile
from pathlib import Path

import pytest

pytestmark = pytest.mark.slow

ROOT = Path(__file__).resolve().parents[2]
DIST_INFO = re.compile(r"^work_it_out-[^/]+\.dist-info/")
# Dotfiles (incl. emacs .# locks), caches, backups (~) and emacs #autosave# files.
JUNK = re.compile(r"(^|/)(\.[^/]+|__pycache__|[^/]*~|#[^/]*#|[^/]*\.pyc)(/|$)")


def _uv() -> str:
    path = shutil.which("uv")
    assert path, "uv is required to build the package"
    return path


@pytest.fixture(scope="module")
def dist_dir(tmp_path_factory: pytest.TempPathFactory) -> Path:
    out = tmp_path_factory.mktemp("dist")
    subprocess.run(
        [_uv(), "build", "--out-dir", str(out)],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return out


@pytest.fixture(scope="module")
def wheel_path(dist_dir: Path) -> Path:
    [wheel] = list(dist_dir.glob("*.whl"))
    return wheel


@pytest.fixture(scope="module")
def wheel_names(wheel_path: Path) -> list[str]:
    with zipfile.ZipFile(wheel_path) as wheel:
        return [name for name in wheel.namelist() if not name.endswith("/")]


@pytest.fixture(scope="module")
def sdist_names(dist_dir: Path) -> list[str]:
    [sdist] = list(dist_dir.glob("*.tar.gz"))
    with tarfile.open(sdist) as archive:
        # Drop the "<name>-<version>/" prefix so paths read like the repo's.
        return [
            member.name.partition("/")[2]
            for member in archive.getmembers()
            if member.isfile()
        ]


def test_wheel_contains_only_the_package(wheel_names: list[str]) -> None:
    unexpected = [
        name
        for name in wheel_names
        if not (name.startswith("wio/") or DIST_INFO.match(name))
    ]
    assert unexpected == []


def test_wheel_ships_the_typing_marker(wheel_names: list[str]) -> None:
    assert "wio/py.typed" in wheel_names


def test_sdist_ships_the_typing_marker(sdist_names: list[str]) -> None:
    assert "src/wio/py.typed" in sdist_names


def test_wheel_has_no_editor_or_cache_files(wheel_names: list[str]) -> None:
    assert [name for name in wheel_names if JUNK.search(name)] == []


def test_sdist_has_no_editor_or_cache_files(sdist_names: list[str]) -> None:
    assert [name for name in sdist_names if JUNK.search(name)] == []


def test_sdist_does_not_ship_the_tests(sdist_names: list[str]) -> None:
    assert [name for name in sdist_names if name.startswith("tests/")] == []


def test_wheel_ships_the_license(wheel_names: list[str]) -> None:
    assert any(name.endswith(".dist-info/licenses/LICENSE") for name in wheel_names)


def test_wheel_metadata_declares_license_and_typing(wheel_path: Path) -> None:
    with zipfile.ZipFile(wheel_path) as wheel:
        name = next(n for n in wheel.namelist() if n.endswith(".dist-info/METADATA"))
        metadata = wheel.read(name).decode()
    assert "License-Expression: Apache-2.0" in metadata
    assert "Classifier: Typing :: Typed" in metadata


def test_wheel_imports_from_a_clean_environment(
    wheel_path: Path, tmp_path: Path
) -> None:
    result = subprocess.run(
        [
            _uv(),
            "run",
            "--no-project",
            "--isolated",
            "--with",
            str(wheel_path),
            "python",
            "-I",
            "-c",
            "import wio; print(wio.__file__)",
        ],
        cwd=tmp_path,
        check=True,
        capture_output=True,
        text=True,
    )
    assert "site-packages" in result.stdout
