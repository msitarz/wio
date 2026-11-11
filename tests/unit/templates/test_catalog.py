# SPDX-License-Identifier: Apache-2.0
"""Tests of the catalog of templates that `wio.contracts` asks for."""

from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import override

from tests.unit.fakes import ROOT, FakeRepository, MemoryFileSystem
from wio.models.config import Config, Templates
from wio.models.frozen import freeze
from wio.templates import TemplatesCatalog, check_templates, discover

DIR = ROOT / ".agents" / "wio" / "templates"
VALID = '<!-- wio\nkind = "feature"\n-->\n\n# Title\n'


@dataclass
class _Settings:
    """A `Settings` that gives a fixed config and counts the loads."""

    config: Config
    loads: int = 0

    def load(self) -> Config:
        """Give the config.

        Returns:
            The fixed config.
        """
        self.loads += 1
        return self.config


@dataclass
class _Counting(MemoryFileSystem):
    """A file system that counts the reads of each file."""

    reads: Counter[Path] = field(default_factory=Counter)

    @override
    def read_text(self, path: Path) -> str:
        """Count the read and give the file.

        Args:
            path: The file.

        Returns:
            Its text.
        """
        self.reads[path] += 1
        return super().read_text(path)


def _config(entry: str = "feature.draft") -> Config:
    """Make a config that declares the kind `feature`.

    Args:
        entry: The entry template of the kind.

    Returns:
        The config.
    """
    return Config(templates=Templates(kinds=freeze({"feature": entry})))


def _catalog(
    files: MemoryFileSystem, config: Config | None = None
) -> tuple[TemplatesCatalog, _Settings]:
    """Build a catalog over a file system and a fixed config.

    Args:
        files: The stored files.
        config: The settings, or the default that declares the kind `feature`.

    Returns:
        The catalog and the settings it loads through.
    """
    settings = _Settings(config or _config())
    return TemplatesCatalog(settings, FakeRepository(), files), settings


def test_a_template_is_found_by_name_and_a_missing_name_gives_none() -> None:
    """AC-3: `feature.leaf` in a subdirectory is found with its path."""
    # Given a config with the kind `feature` and a valid template `feature.leaf`
    # of that kind in a subdirectory of the templates directory
    catalog, _ = _catalog(MemoryFileSystem({DIR / "sub" / "feature.leaf.md": VALID}))

    # When `find("feature.leaf")` and `find("nosuch")` run
    found, missing = catalog.find("feature.leaf"), catalog.find("nosuch")

    # Then the first gives that template with its `path` relative to the root and
    # the second gives none
    assert found is not None
    assert found.path == Path(".agents/wio/templates/sub/feature.leaf.md")
    assert missing is None


def test_a_template_with_an_error_is_rejected_and_a_missing_one_is_not() -> None:
    """AC-4: errors reject, warnings and missing names do not."""
    # Given templates `good`, `warned`, `badkey`, `unclosed`, `baddirective` and
    # two files named `twin`
    files = MemoryFileSystem(
        {
            DIR / "good.md": VALID,
            DIR / "warned.md": VALID + "\n## A\n\n## A\n",
            DIR / "badkey.md": VALID.replace('"feature"', '"feature"\nzzz = 1'),
            DIR / "unclosed.md": '<!-- wio\nkind = "feature"\n\n# T\n',
            DIR / "baddirective.md": VALID + "\n## A <!-- wio: mandatory -->\n",
            DIR / "a" / "twin.md": VALID,
            DIR / "b" / "twin.md": VALID,
        }
    )
    catalog, _ = _catalog(files, _config("good"))

    # When `is_rejected` runs for each and for `nosuch`, and `find` runs for
    # `unclosed`
    names = ("good", "warned", "badkey", "unclosed", "baddirective", "twin", "nosuch")
    rejected = {name: catalog.is_rejected(name) for name in names}
    unbuilt = catalog.find("unclosed")

    # Then it is false for `good`, `warned` and `nosuch`, and true for the rest,
    # and `find("unclosed")` gives none
    assert rejected == {
        "good": False,
        "warned": False,
        "badkey": True,
        "unclosed": True,
        "baddirective": True,
        "twin": True,
        "nosuch": False,
    }
    assert unbuilt is None


def test_a_refused_templates_directory_rejects_no_name() -> None:
    """AC-4: a symbolic link as the directory."""
    # Given a templates directory that is a symbolic link
    files = MemoryFileSystem({}, links={DIR})
    catalog, _ = _catalog(files)

    # When `is_rejected` runs for any name
    rejected = [catalog.is_rejected(name) for name in ("templates", "good")]

    # Then it is false
    assert rejected == [False, False]


def test_the_templates_are_discovered_once_and_checked_once() -> None:
    """AC-5: the reads are those of one discovery and one check, in either order."""
    # Given a catalog over a file system that counts the reads of each template,
    # and the counts of a reference `discover` and a whole `check_templates`
    stored = {DIR / "feature.draft.md": VALID, DIR / "sub" / "other.md": VALID}
    config = _config()
    reference = _Counting(stored)
    discover(ROOT, config.templates, reference)
    discovered = Counter(reference.reads)
    whole = _Counting(stored)
    check_templates(ROOT, config, whole)
    checked = Counter(whole.reads)
    first, second = _Counting(stored), _Counting(stored)
    one, settings_one = _catalog(first)
    two, settings_two = _catalog(second)

    # When `find` runs twice and `is_rejected` three times, and on a fresh catalog
    # `is_rejected` runs twice and `find` twice
    one.find("feature.draft")
    one.find("other")
    after_find = Counter(first.reads)
    for _ in range(3):
        one.is_rejected("other")
    after_both = Counter(first.reads)
    two.is_rejected("other")
    two.is_rejected("feature.draft")
    after_check = Counter(second.reads)
    two.find("other")
    two.find("other")
    after_both_reversed = Counter(second.reads)

    # Then the counts follow the reference runs after each call, and the config
    # is loaded once
    assert after_find == discovered
    assert after_both == discovered + checked
    assert after_check == checked
    assert after_both_reversed == checked + discovered
    assert (settings_one.loads, settings_two.loads) == (1, 1)
