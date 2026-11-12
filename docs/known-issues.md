# Known issues

Problems in this repository's tooling that are known and not yet fixed. Each
entry says what fails, what it puts at risk and what is being done about it. How
an issue was found belongs in the commit that records it. Remove an entry in the
change that fixes it.

## `tach check` sometimes passes a forbidden import

**What fails.** `tach.toml` sets `source_roots = ["src", "."]`, and these roots
overlap: every file under `src` is under both. With tach 0.35.3, the latest
release, the module a file belongs to is then not fixed from run to run, so
`uv run tach check` passes a forbidden import in some runs. When it fails, it
reports each violation twice.

**What it puts at risk.** A change that breaks the dependency direction of
`src/wio` can pass `make lint` and continuous integration, so the review of each
Work must check the imports of the files it changes, and must not rely on a
green `tach check` alone. A clean tree is not affected: `tach check` passes it
every time.

**Why it is not fixed yet.** Both workarounds found so far lose part of what
tach checks:

- `source_roots = ["src", "scripts", "tests"]` makes tach name
  `tests/sandbox.py` `sandbox`, so the imports of `tests.sandbox` and the rest
  of `tests.*` count as external and are never checked.
- Two configs, `src/tach.toml` with the root `["."]` and the root `tach.toml`
  with `exclude = ["src/**"]`, are deterministic, but the root config no longer
  sees `wio`, so imports from `tests` and `scripts` into `wio`, such as a test
  driver importing an adapter, are never checked.

**What is being done.** The bug is
[tach issue #962](https://github.com/tach-org/tach/issues/962), where a
maintainer said overlapping source roots are not supported. A
[comment on it](https://github.com/tach-org/tach/issues/962#issuecomment-6612308279)
asks for this layout to be supported, mapping each file to its nearest root as
the tach FAQ describes, or else rejected with a configuration error. The config
stays as it is until the maintainers answer.

## `uv sync --locked` fetches the Intel macOS wheel on every platform

**What fails.** `quickjs-ng` has a direct URL source in `pyproject.toml`, a
wheel built in a fork, for Intel macOS only. `uv sync --locked` checks that
`uv.lock` is current, and for a direct URL it fetches the wheel's metadata
whatever the `marker` says. Every job that runs it, on Linux too, therefore
requests the release URL, and a GitHub 504 fails the job with "Failed to
generate package metadata for `quickjs-ng`".

**What it puts at risk.** A GitHub outage or timeout fails `ci.yml`,
`records.yml` and `pr-title.yml` on a change that has nothing to do with it. A
re-run passes when the host answers. The wheel is never installed on those
platforms, only fetched.

**Why it is not fixed yet.** Replacing `--locked` with `--frozen` in the
workflows stops the fetch, but then no job checks that `uv.lock` matches
`pyproject.toml` except one that runs on Intel macOS or locally. Hosting the
wheel elsewhere only moves the dependency.

**What is being done.** Nothing yet: re-run a failed job. If the failures
repeat, the workflows move to `uv sync --frozen` and a single `uv lock --check`
step keeps the lock honest.

## `pyrefly` rejects building a `frozendict` from a mapping

**What fails.** Python 3.15 has a built-in `frozendict`, which `Config` uses for
its open tables. With pyrefly 1.4.0, the latest release, the bundled stub gives
`frozendict.__init__` no positional parameter, so `frozendict({"a": 1})` is
reported as `bad-argument-count`, though it is valid and the checker still
catches a value of the wrong type once the call is accepted.

**What it puts at risk.** Without a workaround no code can build a
`frozendict` from a mapping and pass `make check`.

**Why it is not fixed yet.** The stub is bundled with pyrefly, and no newer
release is available. Loosening the rule for the whole project would hide real
mistakes.

**What is being done.** One helper in `wio.models` builds every `frozendict`,
with a single narrow `# pyrefly: ignore[bad-argument-count]` that names this
entry. Delete the suppression, and this entry, when a release accepts the call.

## `tomlkit` cannot add a key or a table without moving or adding lines

**What fails.** `tomlkit` keeps the text of a document it parsed, but with
0.15.2, the locked version, it has no public way to put a new key or table at a
chosen place, and the ways it does offer change more than they say:

- `doc[key] = value` and `doc.add` replace an existing key in place, comment
  included, but put a new plain key after the comment lines and the empty lines
  that follow the last plain key, directly above the first table. Nothing puts
  the `id` first: `Container` has no public `insert`, only the private
  `_insert_at`.
- A table that is added with `doc[name] = table` gets one empty line before it
  only when the document does not already end with one, but the same table
  added with `Container.append` doubles an empty line that is there.
- `Container.append` also gives an empty line to any table whose predecessor is
  not an empty line, one that was parsed included, so building a document again
  from `doc.body` adds a line before `[x]` in `template = "t"` then `[x]`.
- Building a document again moves an empty line that stands before a plain key
  to after it: `a=1`, an empty line, `b=2` becomes `a=1`, `b=2`, an empty line,
  and a leading empty line is dropped.
- Added items are written with `\n` whatever the document used, so a CRLF
  document comes out with mixed endings.
- A mapping assigned as a value becomes a table, and a list of mappings an array
  of tables. An inline table needs `tomlkit.inline_table()`.
- A dotted key such as `a.b = 1` is parsed as a table.
- Adding a key or a table whose name is already used raises
  `tomlkit.exceptions.KeyAlreadyPresent`, which is not a `ValueError`, while
  `doc["x"] = 1` over a table replaces it without an error. A key added to an
  existing table lands after the table's trailing comment lines.

**What it puts at risk.** Setting keys in the metadata block of a contract,
which a person has written and reviewed, would reorder or add lines, or leave
the line endings mixed, in a file that `wio contracts new` and
`wio contracts skeleton` are meant to change only where they say.

**Why it is not fixed yet.** The behaviours above are the library's own, and the
version is the latest. Using the private `_insert_at` would tie the block writer
to an internal that can change with any release, and `encode_toml`, which writes
a whole document, cannot edit one.

**What is being done.** `set_block_keys` in `wio.formats` uses `tomlkit` only to
read the block, to replace a value where it stands and to write a value, and
places the lines that it adds itself, as text, after normalizing the line
endings. Its tests pin each case above. Remove this entry, and that workaround
if the library allows, when a release lets a key or a table be inserted at a
chosen place without changing the rest.

**The two ways of using it that were measured.** Both give the expected text for
a block with `template`, `roots = []`, an empty line and a table `[x]` when
`roots` is replaced, `depends_on` is added and the table `[actions]` is added,
and both replace a key or a whole table in place, keep an empty line that stands
before a plain key, and add no empty line to a table added after a block that
ends with one or two. They differ here:

| Case | `doc[key] = value` and `doc[name] = table` | Text edit |
| --- | --- | --- |
| An existing table directly after a key or a comment | Gains an empty line before it | Unchanged |
| A new key, with comment lines after the last plain key | Goes after the comment lines | Goes before them |
| A block with no final line ending, and a table added | No empty line before the table | One empty line |
| A table named like an inline plain key, or the reverse | Replaces it without an error | `ValueError` |
| `id` first, a CRLF block, a mapping as an inline table | Extra code | Extra code |

Replacing the value where it stands is the same in both. The first two rows are
the only ones that change a file that a person wrote, and a block that
`encode_toml` wrote already has an empty line before each table, so they matter
only for a hand-written contract. Using the assignment alone takes about half
the code of the text edit and accepts those two rows.

**Cases that were run on the text edit.** The expected output is for adding the
plain key `c = 3`, unless the case says otherwise.

| Block between the delimiters | Result |
| --- | --- |
| `a=1`, empty line, `b=2` | `c = 3` after `b=2` |
| `a=1`, `# c`, empty line, `b=2` | `c = 3` after `b=2` |
| an empty line, then `a = 1` | the empty line stays first |
| `template = "t"`, then `[x]` | `c = 3` after `template`, no empty line added |
| `# about x`, then `[x]` | `c = 3` first, the comment stays above `[x]` |
| `a = 1`, `# tail`, empty line, `[x]` | `c = 3` after `a = 1`, before `# tail` |
| `id = "a" # why`, setting `id` | `id = "b" # why` |
| a multi-line array, then a key | the key follows the closing bracket |
| `a = 1`, one or two empty lines, a table added | no empty line added |
| `a = 1` with no empty line, a table added | one empty line added |
| an empty block, a table added | the table first, no empty line |
| a CRLF block, keys and a table added | every line of the block ends with CRLF |
| `+++` front matter, setting `id` | `id` after the line `wio = 1` |
| `actions = { a = 1 }`, the table `actions` added | `ValueError` |
| `[x]`, the plain key `x` added | `ValueError` |
| a list of mappings as a value | `ValueError` |
