# SPDX-License-Identifier: Apache-2.0
"""Tests for `LocalFileSystem`, the adapter of the `FileSystem` port."""

from typing import TYPE_CHECKING

import pytest

from wio.io.adapters import LocalFileSystem

if TYPE_CHECKING:
    from pathlib import Path


def test_reading_returns_text_as_stored_and_bytes_and_rejects_bad_utf8(
    tmp_path: Path,
) -> None:
    """AC-2: reads keep line ends, and text that is not UTF-8 raises."""
    # Given a directory with a UTF-8 file and a file that is not valid UTF-8
    (tmp_path / "a.txt").write_bytes("héllo\r\n".encode())
    (tmp_path / "b.bin").write_bytes(b"\xff\xfe\x00")
    disk = LocalFileSystem()

    # When they are read as text and as bytes
    text = disk.read_text(tmp_path / "a.txt")
    data = disk.read_bytes(tmp_path / "b.bin")

    # Then the text keeps its line end, the bytes are returned, and bad text raises
    assert text == "héllo\r\n"
    assert data == b"\xff\xfe\x00"
    with pytest.raises(UnicodeDecodeError):
        disk.read_text(tmp_path / "b.bin")


def test_writing_creates_parents_and_appending_adds_to_the_file(
    tmp_path: Path,
) -> None:
    """AC-2: a write creates parent directories, and an append extends the file."""
    # Given a directory without a subdirectory
    disk = LocalFileSystem()
    target = tmp_path / "x" / "y" / "f"

    # When text is written to a path inside it and then appended
    disk.write_text(target, "a")
    disk.append_text(target, "b")

    # Then the file holds both texts and the existence checks answer for each path
    assert target.read_text(encoding="utf-8") == "ab"
    assert (disk.exists(target), disk.is_file(target), disk.is_dir(target)) == (
        True,
        True,
        False,
    )
    assert (disk.exists(target.parent), disk.is_dir(target.parent)) == (True, True)
    assert disk.exists(tmp_path / "missing") is False


def test_listing_is_sorted_and_missing_paths_raise(tmp_path: Path) -> None:
    """AC-2: list_dir is sorted and the errors are the ones the port names."""
    # Given a directory with three entries, a file and a missing path
    for name in ("b", "a", "c"):
        (tmp_path / "d").mkdir(exist_ok=True)
        (tmp_path / "d" / name).write_text("", encoding="utf-8")
    disk = LocalFileSystem()

    # When each is listed and the missing path is read as text
    listing = disk.list_dir(tmp_path / "d")

    # Then the listing is sorted and the file and the missing path raise
    assert [entry.name for entry in listing] == ["a", "b", "c"]
    with pytest.raises(NotADirectoryError):
        disk.list_dir(tmp_path / "d" / "a")
    with pytest.raises(FileNotFoundError):
        disk.list_dir(tmp_path / "missing")
    with pytest.raises(FileNotFoundError):
        disk.read_text(tmp_path / "missing")


def test_a_symbolic_link_is_told_apart_from_the_file_it_points_to(
    tmp_path: Path,
) -> None:
    """AC-1 of discovery: a link is a link, broken or not, and a file is not."""
    # Given a file, a link to it, a link to nothing and a directory
    (tmp_path / "file").write_text("x")
    (tmp_path / "link").symlink_to(tmp_path / "file")
    (tmp_path / "broken").symlink_to(tmp_path / "nothing")
    (tmp_path / "dir").mkdir()
    disk = LocalFileSystem()

    # When each is asked whether it is a symbolic link
    answers = {
        name: disk.is_symlink(tmp_path / name)
        for name in ("file", "link", "broken", "dir", "absent")
    }

    # Then only the two links are
    assert answers == {
        "file": False,
        "link": True,
        "broken": True,
        "dir": False,
        "absent": False,
    }
