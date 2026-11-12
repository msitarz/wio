# SPDX-License-Identifier: Apache-2.0
"""Tests of the discovery of Works in `wio.contracts`."""

import pytest


@pytest.mark.skip(reason="Pending the implementation stage.")
def test_marked_files_become_works_with_their_fields_in_the_order_of_their_paths() -> (
    None
):
    """AC-1: a comment block and `+++` front matter are read into a `Work`."""
    # Given a nesting tree with a Work that sets every key, a Work of front
    # matter with a body of `##` only, a Work with no heading, a file with no
    # block, a file whose block is on its second line, a hidden directory with a
    # marked file and a symbolic link to a marked file
    # When the Works are discovered
    # Then there are three Works in the order of their paths with those ids and
    # the titles `First`, `Only` and none, the first with its template, roots,
    # dependencies and both overrides and the others with none, and there is no
    # diagnostic


@pytest.mark.skip(reason="Pending the implementation stage.")
def test_the_title_is_the_first_real_heading_at_any_level() -> None:
    """AC-1: a heading in a comment or a code block is not a title."""
    # Given Works whose bodies open with a comment holding `# Hidden`, a fenced
    # block holding `# Code`, and then `## Real`
    # When the Works are discovered
    # Then their title is `Real`


@pytest.mark.skip(reason="Pending the implementation stage.")
def test_discovery_writes_no_file() -> None:
    """AC-1: every file is read through the port and none is written."""
    # Given a tree of Works on a fake file system that records its calls
    # When the Works are discovered
    # Then the calls hold reads and listings and no write or append


@pytest.mark.skip(reason="Pending the implementation stage.")
def test_a_file_that_cannot_be_identified_is_left_out_with_one_error() -> None:
    """AC-2: seven broken files give seven errors at their places, and no more."""
    # Given a flat tree with a file that is not UTF-8, a block that does not
    # close, invalid TOML on line 3, `wio = 2` on line 2, no `id`, `id = ""`,
    # `id = 12`, and a good Work
    # When the Works are discovered
    # Then the good Work is found and there is one error for each of the seven at
    # `works/bad/utf.md`, `works/bad/open.md:1`, `works/bad/toml.md:3`,
    # `works/bad/marker.md:2`, `works/bad/noid.md`, `works/bad/empty.md` and
    # `works/bad/number.md`, and the files are in `left_out`


@pytest.mark.skip(reason="Pending the implementation stage.")
def test_a_file_that_cannot_be_read_is_left_out_with_the_reason() -> None:
    """AC-2: an `OSError` of the port is one error that gives its reason."""
    # Given a marked file that the file system fails to read with a permission
    # error, beside a good Work
    # When the Works are discovered
    # Then the good Work is found and one error is at the file's path and says
    # that it cannot be read


@pytest.mark.skip(reason="Pending the implementation stage.")
def test_a_wrong_optional_field_is_empty_and_reported_and_the_work_stays() -> None:
    """AC-3: six wrong fields give six errors and five Works."""
    # Given a nesting tree with `roots = "api"` on a parent whose child has
    # `depends_on = [1]`, an `[actions]` string and a numeric `template`,
    # `roots = ["a", 1]`, and `[actions]` with `define = 5`
    # When the Works are discovered
    # Then all five Works are found with the wrong fields empty, and there is
    # one error for each of the six fields at its file


@pytest.mark.skip(reason="Pending the implementation stage.")
def test_a_shared_id_keeps_both_works_and_refuses_its_lookup() -> None:
    """AC-4: one error names both paths, and the lookup yields it and no Work."""
    # Given a flat tree where two Works share `k3m9xq` and a third has `p5n2hv`
    # When the Works are discovered and `k3m9xq`, `p5n2hv` and `zzzzzz` are
    # looked up
    # Then all three Works are found, one error is at the two paths joined by a
    # comma and a space and names the id, the first lookup yields that
    # diagnostic, the second the Work and the third none


@pytest.mark.skip(reason="Pending the implementation stage.")
def test_a_directory_with_two_marked_files_holds_no_work_under_nesting() -> None:
    """AC-5: one error names both files, and a top-level file is not a Work."""
    # Given a nesting tree with `a/one.md` and `a/two.md`, `top.md` directly in
    # the Works directory, and `b/README.md`
    # When the Works are discovered
    # Then only `b/README.md` is a Work, one error is at the two files of `a`
    # and names the directory, and one error is at `works/top.md` and says that
    # a Work cannot sit directly in the Works directory


@pytest.mark.skip(reason="Pending the implementation stage.")
def test_a_marked_file_that_is_left_out_still_counts_in_its_directory() -> None:
    """AC-5: a missing `id` gives two errors, and a file that is not UTF-8 one."""
    # Given a nesting tree with `a/one.md` and `a/two.md` whose block has no
    # `id`, and a directory with a marked file and a file that is not UTF-8
    # When the Works are discovered
    # Then there is no Work in `a`, one error for the collision and one for the
    # missing id, and the other directory holds its Work and the one error of
    # the file that cannot be decoded


@pytest.mark.skip(reason="Pending the implementation stage.")
def test_under_flat_a_directory_may_hold_any_number_of_works() -> None:
    """AC-6: the files of the nesting collision are all Works."""
    # Given a flat tree with the files of the first collision scenario
    # When the Works are discovered
    # Then `a/one.md`, `a/two.md`, `top.md` and `b/README.md` are Works and
    # there is no diagnostic


@pytest.mark.skip(reason="Pending the implementation stage.")
def test_a_missing_default_directory_and_an_empty_one_hold_no_works() -> None:
    """AC-7: neither gives a diagnostic."""
    # Given the default Works directory missing, and an empty configured one
    # When the Works are discovered for each
    # Then there is no Work and no diagnostic


@pytest.mark.skip(reason="Pending the implementation stage.")
def test_a_works_directory_that_cannot_be_walked_is_one_error() -> None:
    """AC-7: missing, a file and a symbolic link each give one error."""
    # Given a configured Works directory that is missing, one that is a file and
    # one that is a symbolic link to a directory
    # When the Works are discovered for each
    # Then each gives no Work and one error whose message begins `The Works
    # directory` and whose place is the directory as written


@pytest.mark.skip(reason="Pending the implementation stage.")
def test_the_works_and_the_diagnostics_are_in_a_fixed_order() -> None:
    """AC-1: the Works by their paths and the diagnostics as `order_diagnostics`."""
    # Given a tree whose files the file system lists in another order, with
    # errors at lines 4 and 12 of one file and at an earlier file
    # When the Works are discovered twice
    # Then both results are equal, the Works are sorted by the string of their
    # paths, and line 4 precedes line 12


@pytest.mark.skip(reason="Pending the implementation stage.")
def test_each_file_that_is_not_a_work_has_the_first_reason_that_applies() -> None:
    """AC-8: thirteen paths each name their subject, and a Work has none."""
    # Given a nesting tree and thirteen paths: one that does not exist, a
    # directory, `x.txt`, a symbolic link, a path through a symbolic link, a
    # file outside the Works directory, one under a hidden directory, an `.md`
    # with no block, one with its block on line 2, front matter without `wio`, a
    # file beside another marked file, a marked file directly in the Works
    # directory, a file whose block does not close, and a good Work
    # When the reason each is not a Work is asked for
    # Then each of the thirteen has a reason that names the path, the other
    # files, the Works directory or the error of discovery as its subject, and
    # the Work has none


@pytest.mark.skip(reason="Pending the implementation stage.")
def test_the_reasons_are_the_same_for_a_relative_and_an_absolute_path() -> None:
    """AC-8: the path may be written either way."""
    # Given a path that is not a Work, written relative to the root and absolute
    # When the reason is asked for each
    # Then the two reasons are equal


@pytest.mark.skip(reason="Pending the implementation stage.")
def test_under_flat_a_shared_directory_is_no_reason() -> None:
    """AC-8: the two collision reasons apply to nesting alone."""
    # Given a flat tree with two marked files in a directory and one directly in
    # the Works directory
    # When the reason each is not a Work is asked for
    # Then none has a reason


@pytest.mark.skip(reason="Pending the implementation stage.")
def test_the_errors_are_sorted_into_incomplete_and_ambiguous() -> None:
    """AC-2 to AC-5, AC-7: a wrong optional field is in neither."""
    # Given trees with a Work left out, a nesting collision, a marked file
    # directly in the Works directory, a Works directory that cannot be walked,
    # a shared id, and one with only a wrong optional field
    # When the Works are discovered for each
    # Then the first four have their error in `incomplete` and not in
    # `ambiguous`, the shared id has its error in `ambiguous` and not in
    # `incomplete`, and the last has neither, though its error is in
    # `diagnostics`


@pytest.mark.skip(reason="Pending the implementation stage.")
def test_the_marked_files_of_a_collision_are_excluded_and_not_left_out() -> None:
    """AC-5: the files of a collided directory and a top-level file are `excluded`."""
    # Given the nesting tree of the first collision scenario and one with a file
    # that is left out
    # When the Works are discovered
    # Then `a/one.md`, `a/two.md` and `top.md` are in `excluded` and not in
    # `left_out`, and a file that is left out is in `left_out` and not in
    # `excluded`
