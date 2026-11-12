# SPDX-License-Identifier: Apache-2.0
"""Test stubs of the id and the place of a new Work.

Each stub is one scenario of the Work's acceptance criteria. The
implementation stage replaces its body with the scenario.
"""

import pytest

pytestmark = pytest.mark.skip(
    reason="architecture stub: the implementation stage fills it"
)


def test_a_slug_is_derived_from_a_title_by_one_rule() -> None:
    """Check a scenario of AC-1."""
    # Given the titles `Read config.toml`, `Łódź café`, `Straße æon`, `  --A
    # B--  `, `aпb`, 47 letters and a space and `b`, and `Привет`
    # When the slug of each is derived
    # Then the slugs are as AC-1 states and the last is an error that asks for `--slug`
    raise NotImplementedError


def test_a_given_slug_must_be_lowercase_kebab_case() -> None:
    """Check a scenario of AC-2."""
    # Given the slugs `login`, `2026-11-02-login-design`, `.draft`, `a/b`, `..`,
    # `Login`, `a_b`, `a--b`, `-a` and an empty one
    # When each is checked
    # Then the first two are used as written and each other is an error that
    # says what a slug is
    raise NotImplementedError


def test_the_default_place_follows_the_arguments_under_nesting() -> None:
    """Check a scenario of AC-3."""
    # Given `nesting`, Works `p5n2hv` at `p/README.md` and `k3m9xq` at
    # `q/spec.md`, and the title `Child`
    # When the place is decided with the title alone, with each parent, and with
    # a slug and a title
    # Then the paths are those of AC-3
    raise NotImplementedError


def test_options_that_exclude_each_other_or_name_nothing_are_refused() -> None:
    """Check a scenario of AC-3."""
    # Given the same Works, an existing empty directory `child` and a shared id
    # When the place is decided with no name, with `--path` and `--slug`,
    # `--path` and `--parent`, an unknown parent, a shared parent and an
    # existing directory
    # Then each is the error that AC-3 states
    raise NotImplementedError


def test_a_parent_needs_nesting() -> None:
    """Check a scenario of AC-3."""
    # Given `flat`
    # When the place is decided with `--parent`
    # Then it is an error that says `--parent` needs `nesting`
    raise NotImplementedError


def test_a_path_must_be_one_that_a_work_could_have() -> None:
    """Check a scenario of AC-4."""
    # Given `nesting`, a Work at `p/README.md` and the paths of AC-4, one a
    # symbolic link
    # When each is checked as the path of a new Work
    # Then the first is accepted and each other is an error that names the path
    # and says why
    raise NotImplementedError


def test_a_directory_that_exists_and_a_file_that_was_left_out() -> None:
    """Check a scenario of AC-4."""
    # Given an existing directory `q` and a marked file `r/one.md` whose block
    # has no `id`
    # When `q/new.md` and `r/two.md` are checked
    # Then the first is accepted and the second says the directory holds a marked file
    raise NotImplementedError


def test_under_flat_a_path_may_be_at_the_top_or_beside_a_work() -> None:
    """Check a scenario of AC-4."""
    # Given `flat` and a Work at `p/README.md`
    # When `top.md` and `p/other.md` are checked
    # Then both are accepted
    raise NotImplementedError


def test_an_id_is_drawn_from_the_bytes_until_it_is_free() -> None:
    """Check a scenario of AC-5."""
    # Given an `Entropy` with fixed bytes, an empty tree and a tree that holds `012345`
    # When an id is drawn for each
    # Then they are `012345` and `6789ab`, all of the alphabet
    raise NotImplementedError


def test_only_the_low_five_bits_of_a_byte_make_a_character() -> None:
    """Check a scenario of AC-5."""
    # Given an `Entropy` that gives 255, 32, 33, 250, 128 and 31
    # When an id is drawn
    # Then it is `z01t0z`
    raise NotImplementedError


def test_a_shared_id_is_taken_and_the_draw_gives_up_after_100_tries() -> None:
    """Check a scenario of AC-5."""
    # Given a tree with a shared id, and one that holds `012345` with an
    # `Entropy` that repeats it
    # When an id is drawn for each
    # Then the first is `6789ab` and the second makes 100 calls and is an error
    raise NotImplementedError


def test_deciding_writes_nothing_and_the_guard_never_overwrites() -> None:
    """Check a scenario of AC-6."""
    # Given `flat`, a recording file system, a free path and one that exists
    # When the place is decided for each and the guard writes to each
    # Then deciding wrote nothing, the guard wrote the free path and refused the other
    raise NotImplementedError
