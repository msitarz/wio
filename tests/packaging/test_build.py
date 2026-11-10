# SPDX-License-Identifier: Apache-2.0
"""Packaging tests: build the wheel and sdist, then inspect them."""

import email
import json
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
    # Given the files of the built wheel

    # When the files outside the package and its metadata are listed
    unexpected = [
        name
        for name in wheel_names
        if not (name.startswith("wio/") or DIST_INFO.match(name))
    ]

    # Then there are none
    assert unexpected == []


def test_wheel_ships_the_typing_marker(wheel_names: list[str]) -> None:
    # Given the files of the built wheel

    # When nothing more is done

    # Then the package's typing marker is among them
    assert "wio/py.typed" in wheel_names


def test_sdist_ships_the_typing_marker(sdist_names: list[str]) -> None:
    # Given the files of the built sdist

    # When nothing more is done

    # Then the package's typing marker is among them
    assert "src/wio/py.typed" in sdist_names


def test_wheel_has_no_editor_or_cache_files(wheel_names: list[str]) -> None:
    # Given the files of the built wheel

    # When the editor and cache files among them are listed
    junk = [name for name in wheel_names if JUNK.search(name)]

    # Then there are none
    assert junk == []


def test_wheel_has_no_glossary(wheel_names: list[str]) -> None:
    # Given the files of the built wheel

    # When the glossaries among them are listed
    glossaries = [name for name in wheel_names if name.endswith("GLOSSARY.md")]

    # Then there are none, because glossaries document the source tree
    assert glossaries == []


def test_wheel_has_no_readme(wheel_names: list[str]) -> None:
    # Given the files of the built wheel

    # When the README files among them are listed
    readmes = [name for name in wheel_names if name.endswith("README.md")]

    # Then there are none, because a README under src documents the source tree
    assert readmes == []


def test_wheel_metadata_carries_the_project_readme(wheel_path: Path) -> None:
    # Given the built wheel and the first line of the project README
    heading = (ROOT / "README.md").read_text(encoding="utf-8").splitlines()[0]

    # When its METADATA is read
    with zipfile.ZipFile(wheel_path) as wheel:
        [name] = [n for n in wheel.namelist() if n.endswith(".dist-info/METADATA")]
        metadata = wheel.read(name).decode("utf-8")

    # Then the README is its long description, though README files are excluded
    assert heading in metadata


def test_sdist_has_no_editor_or_cache_files(sdist_names: list[str]) -> None:
    # Given the files of the built sdist

    # When the editor and cache files among them are listed
    junk = [name for name in sdist_names if JUNK.search(name)]

    # Then there are none
    assert junk == []


def test_sdist_does_not_ship_the_tests(sdist_names: list[str]) -> None:
    # Given the files of the built sdist

    # When the test files among them are listed
    tests = [name for name in sdist_names if name.startswith("tests/")]

    # Then there are none
    assert tests == []


def test_wheel_ships_the_license(wheel_names: list[str]) -> None:
    # Given the files of the built wheel

    # When the license file is looked for in its metadata
    has_license = any(
        name.endswith(".dist-info/licenses/LICENSE") for name in wheel_names
    )

    # Then it is there
    assert has_license


def test_wheel_metadata_declares_license_and_typing(wheel_path: Path) -> None:
    # Given the built wheel

    # When its METADATA file is read
    with zipfile.ZipFile(wheel_path) as wheel:
        name = next(n for n in wheel.namelist() if n.endswith(".dist-info/METADATA"))
        metadata = wheel.read(name).decode()

    # Then it declares the license and the typing classifier
    assert "License-Expression: Apache-2.0" in metadata
    assert "Classifier: Typing :: Typed" in metadata


def test_wheel_imports_from_a_clean_environment(
    wheel_path: Path, tmp_path: Path
) -> None:
    # Given the built wheel and an empty directory outside the repository

    # When the package is imported in an isolated environment with only the wheel
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

    # Then it is imported from the installed wheel, not from the source tree
    assert "site-packages" in result.stdout


def _installed_wio(
    wheel_path: Path, cwd: Path, *args: str
) -> subprocess.CompletedProcess[str]:
    """Run the `wio` command of the wheel in an isolated environment.

    Args:
        wheel_path: The built wheel, the only package in the environment.
        cwd: An empty directory outside the repository.
        *args: The arguments after `wio`.

    Returns:
        The completed process, with its output decoded.
    """
    return subprocess.run(
        [
            _uv(),
            "run",
            "--no-project",
            "--isolated",
            "--with",
            str(wheel_path),
            "wio",
            *args,
        ],
        cwd=cwd,
        check=False,
        capture_output=True,
        text=True,
    )


def _wheel_metadata(wheel_path: Path) -> email.message.Message:
    """Read the `METADATA` file of a wheel.

    Args:
        wheel_path: The built wheel.

    Returns:
        Its parsed headers.
    """
    with zipfile.ZipFile(wheel_path) as wheel:
        [name] = [n for n in wheel.namelist() if n.endswith(".dist-info/METADATA")]
        return email.message_from_bytes(wheel.read(name))


def test_the_installed_command_shows_the_summary_of_its_wheel(
    wheel_path: Path, tmp_path: Path
) -> None:
    """Bare `wio` in the wheel prints the wheel's `Summary` and exits 0."""
    # Given the built wheel, and an empty directory outside the repository
    summary = _wheel_metadata(wheel_path)["Summary"]

    # When `wio` runs in an isolated environment with only the wheel
    result = _installed_wio(wheel_path, tmp_path)

    # Then it prints the wheel's Summary to standard output and exits 0
    assert result.returncode == 0
    assert summary in result.stdout


def test_the_installed_command_shows_the_version_of_its_wheel(
    wheel_path: Path, tmp_path: Path
) -> None:
    """`wio --version` in the wheel prints `wio <version>` and exits 0."""
    # Given the built wheel, and an empty directory outside the repository
    version = _wheel_metadata(wheel_path)["Version"]

    # When `wio --version` runs in an isolated environment with only the wheel
    result = _installed_wio(wheel_path, tmp_path, "--version")

    # Then it prints wio and the wheel's version, and exits 0
    assert (result.returncode, result.stdout) == (0, f"wio {version}\n")


def _check_in_project(wheel: Path, project: Path) -> subprocess.CompletedProcess[str]:
    """Run `wio config check` from the installed wheel in a project.

    Args:
        wheel: The built wheel.
        project: A directory that is not this repository.

    Returns:
        The finished process, whatever its exit code.
    """
    return subprocess.run(
        [_uv(), "run", "--no-project", "--isolated", "--with", str(wheel)]
        + ["wio", "config", "check"],
        cwd=project,
        capture_output=True,
        text=True,
        check=False,
    )


def _project(tmp_path: Path, name: str, config: str) -> Path:
    """Make a git repository whose config has some text.

    Args:
        tmp_path: A directory of the test.
        name: The name of the repository's directory.
        config: The content of `.agents/wio/config.toml`.

    Returns:
        The repository's root.
    """
    root = tmp_path / name
    (root / ".agents" / "wio").mkdir(parents=True)
    (root / ".agents" / "wio" / "config.toml").write_text(config, encoding="utf-8")
    subprocess.run(["git", "init", "--quiet"], cwd=root, check=True)
    return root


def test_the_installed_wheel_checks_the_config_of_a_project(
    wheel_path: Path, tmp_path: Path
) -> None:
    """AC-4: the wheel gives a working `wio config check` outside this repository."""
    # Given the built wheel, and two repositories that are not this one, one with
    # a valid config and one with an unknown key
    valid = _project(tmp_path, "valid", '[works]\nhierarchy = "nesting"\n')
    invalid = _project(tmp_path, "invalid", "[works]\nnonsense = 1\n")

    # When `wio config check` runs from the installed wheel in each
    passed = _check_in_project(wheel_path, valid)
    failed = _check_in_project(wheel_path, invalid)

    # Then the first exits 0, and the second exits 1 with its errors on standard
    # output
    assert (passed.returncode, passed.stdout) == (0, "Config check passed!\n")
    assert failed.returncode == 1
    assert failed.stdout.startswith("error: works.nonsense: unknown key `nonsense`")


def _run_in_project(
    wheel: Path, project: Path, *args: str
) -> subprocess.CompletedProcess[str]:
    """Run `wio` with some arguments from the installed wheel in a project.

    Args:
        wheel: The built wheel.
        project: A directory that is not this repository.
        *args: The arguments after `wio`.

    Returns:
        The finished process, whatever its exit code.
    """
    return subprocess.run(
        [_uv(), "run", "--no-project", "--isolated", "--with", str(wheel)]
        + ["wio", *args],
        cwd=project,
        capture_output=True,
        text=True,
        check=False,
    )


def test_the_installed_wheel_shows_the_settings_of_a_project(
    wheel_path: Path, tmp_path: Path
) -> None:
    """AC-1: `wio config`, `list` and `show` work outside this repository."""
    # Given the built wheel, and a repository that is not this one whose config
    # sets one stage
    project = _project(tmp_path, "project", '[stages.define]\ngoal = "Define."\n')

    # When `wio config`, `wio config list` and `wio config show stages` run from
    # the installed wheel there
    bare = _run_in_project(wheel_path, project, "config")
    listed = _run_in_project(wheel_path, project, "config", "list")
    shown = _run_in_project(wheel_path, project, "config", "show", "stages")

    # Then the first prints the help, the second lists the settings with the keys
    # the stage sets marked `file` and the rest `default`, the third prints the
    # stage in full, and each exits 0
    assert [bare.returncode, listed.returncode, shown.returncode] == [0, 0, 0]
    assert bare.stdout.startswith("usage: wio config")
    lines = listed.stdout.splitlines()
    assert 'stages.define.goal = "Define."  # file' in lines
    assert 'gates.results = ["pass", "fail", "unknown"]  # default' in lines
    assert all(line.endswith(("# file", "# default")) for line in lines)
    assert [line for line in lines if line.endswith("# file")] == [
        'stages.define.goal = "Define."  # file'
    ]
    stage = shown.stdout.splitlines()
    assert 'stages.define.goal = "Define."  # file' in stage
    assert 'stages.define.session = "any"  # default' in stage
    assert all(line.startswith("stages.define.") for line in stage)


_TEMPLATES_CONFIG = """\
[templates.kinds]
feature = "feature.draft"

[actions.define]
description = "Define."

[stages.implementation]
goal = "Implement."

[stage_presets]
define-feature = ["implementation"]
"""
_DRAFT = (
    '<!-- wio\nkind = "feature"\nshape = "draft"\n[actions]\n'
    'define = "define-feature"\n-->\n\n# Draft\n'
)
_LEAF = (
    '<!-- wio\nkind = "feature"\nshape = "leaf"\n[actions]\n'
    'define = ["implementation"]\n[contract]\nroots = []\n-->\n\n'
    "# Title\n\n## Goals <!-- wio: required -->\n"
)


def _templates_project(tmp_path: Path) -> Path:
    """Make a git repository with the kind `feature` and two templates.

    Args:
        tmp_path: A directory of the test.

    Returns:
        The repository's root.
    """
    root = _project(tmp_path, "templates", _TEMPLATES_CONFIG)
    directory = root / ".agents" / "wio" / "templates"
    directory.mkdir()
    (directory / "feature.draft.md").write_text(_DRAFT, encoding="utf-8")
    (directory / "feature.leaf.md").write_text(_LEAF, encoding="utf-8")
    return root


def test_the_installed_wheel_lists_shows_and_checks_templates(
    wheel_path: Path, tmp_path: Path
) -> None:
    """Parent AC-1: the wheel gives a working `templates` outside this repository."""
    # Given the built wheel and a repository that is not this one, whose config
    # declares the kind `feature` with the entry template `feature.draft` and the
    # actions of the two templates, and whose templates directory holds both
    project = _templates_project(tmp_path)

    # When `wio templates list`, `show feature.leaf` and `check` run there
    listed = _run_in_project(wheel_path, project, "templates", "list")
    shown = _run_in_project(wheel_path, project, "templates", "show", "feature.leaf")
    checked = _run_in_project(wheel_path, project, "templates", "check")

    # Then the first prints the kind with its two templates and marks the draft as
    # the entry, the second the skeleton of the leaf, and the third passes, each
    # exiting 0
    lines = listed.stdout.splitlines()
    assert lines[0] == "feature"
    assert lines[1].split()[:2] == ["feature.draft", "[entry]"]
    assert any(line.split()[:1] == ["feature.leaf"] for line in lines[2:])
    assert shown.stdout.startswith('<!-- wio\ntemplate = "feature.leaf"\n')
    assert checked.stdout == "The templates pass.\n"
    assert [r.returncode for r in (listed, shown, checked)] == [0, 0, 0]


def test_the_installed_wheel_refuses_a_name_that_no_template_has(
    wheel_path: Path, tmp_path: Path
) -> None:
    """Parent AC-1: `show nosuch` names it on standard error and exits 2."""
    # Given the built wheel and the same kind of repository
    project = _templates_project(tmp_path)

    # When `wio templates show nosuch` runs there
    result = _run_in_project(wheel_path, project, "templates", "show", "nosuch")

    # Then it names `nosuch` on standard error, prints nothing else and exits 2
    assert "`nosuch`" in result.stderr
    assert (result.stdout, result.returncode) == ("", 2)


def test_the_installed_wheel_explains_the_directives_outside_a_repository(
    wheel_path: Path, tmp_path: Path
) -> None:
    """Parent AC-1: `directives` works in a directory that is no repository."""
    # Given the built wheel and a directory that is not in a git repository
    # (the pytest directory is outside this one)

    # When `wio templates directives` and `directives --json` run there
    text = _run_in_project(wheel_path, tmp_path, "templates", "directives")
    machine = _run_in_project(wheel_path, tmp_path, "templates", "directives", "--json")

    # Then the first prints every directive with how they combine, and the second
    # the same as one JSON object, each exiting 0
    for name in ("required", "items", "pattern", "inherit", "several directives"):
        assert name in text.stdout
    data = json.loads(machine.stdout)
    assert [entry["name"] for entry in data["directives"]] == [
        "required",
        "items",
        "pattern",
        "inherit",
    ]
    assert data["combining"][0]["name"] == "several directives"
    assert (text.returncode, machine.returncode) == (0, 0)
