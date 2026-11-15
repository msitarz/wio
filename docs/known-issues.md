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
