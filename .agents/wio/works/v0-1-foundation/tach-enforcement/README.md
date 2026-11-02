<!-- wio
id = "1g7xnh"
template = "feature.leaf"
roots = ["repo"]
depends_on = ["jsk0yt"]
-->

# Tach enforcement

## Purpose

The dependency direction is only a statement until a check rejects a change that
breaks it, so the repository's own gates must run one.

## Goals

- `tach.toml` encodes the dependency direction between the `.py` code of the
  packages of `src/wio`.
- A change that breaks the dependency direction fails `make lint`, and so
  continuous integration.

## Non-Goals

- Turning on `exact`, which fails on declared dependencies that no code uses
  yet.
- Checking the imports inside `.pyi` files, which tach cannot read.
- Enabling the `--tach` pytest plugin, which skips tests and enforces nothing.
- Constraining `tests`, `scripts` or any directory other than `src/wio`.

## Assumptions

- **A-1**: The `tach` that `uv.lock` pins, 0.35.3 at the time of writing, keeps
  the behavior verified for this contract: it counts lazy imports, counts
  `TYPE_CHECKING` imports when `ignore_type_checking_imports = false`, and
  limits a nested module to the modules its `visibility` names.
- **A-2**: The stubs hold no `.py` code, so the skeleton gives tach few real
  edges to check, the table is exercised as components land, and `tach check`
  prints a warning about missing first-party imports on the bare skeleton.

## Mechanisms

- `tach.toml` at the repository root, with `source_roots = ["src"]`, a
  `[[modules]]` entry per package of `src/wio` and its `depends_on`, and
  `exact = false`.
- `ignore_type_checking_imports = false` in `tach.toml`, because ports are
  imported only under `TYPE_CHECKING`.
- The nested modules `wio.io.adapters` and `wio.env.adapters`, each with
  `visibility = ["wio.cli"]`, so only `wio.cli` can import an adapter.
- A local hook in `prek.toml` named `tach check`, running `uv run tach check`
  with `pass_filenames = false` on changes to `src/**/*.py`, `tach.toml` and
  `pyproject.toml`.

## Constraints

- A change of the locked `tach` version repeats the trials of AC-2 to AC-5
  before it merges, because the contract commits no test for them.

## Acceptance criteria

### **AC-1** Every module has the allowed dependencies

`tach.toml` encodes the parent's dependency direction as the table below, and a
clean tree passes the check.

| Module | May depend on |
| --- | --- |
| `wio.models`, `wio.env` | nothing |
| `wio.formats`, `wio.io` | `wio.models` |
| `wio.io.adapters` | `wio.io`, `wio.models` |
| `wio.env.adapters` | `wio.env` |
| `wio.config`, `wio.contract`, `wio.rule`, `wio.trailers`, `wio.log`, `wio.context` | `wio.models`, `wio.formats`, `wio.io`, `wio.env` |
| `wio.cli` | every other module |

#### The clean tree passes

- **Given** the delivered tree.
- **When** `uv run tach check` runs.
- **Then** it exits 0.

### **AC-2** A component importing another component fails the check

An import between two components, from `wio.rule` to `wio.config` for example,
fails `tach check` and names both modules.

#### A forbidden import

- **Given** a `.py` module in `wio.rule` that imports `wio.config`, added
  locally by the reviewer and not committed.
- **When** `uv run tach check` runs.
- **Then** it exits non-zero and its output names `wio.rule` and `wio.config`.

### **AC-3** An import under `TYPE_CHECKING` counts

A dependency that exists only under `TYPE_CHECKING` is checked like any other.

#### A forbidden type-only import

- **Given** a `.py` module in `wio.models` that imports `wio.io` under
  `TYPE_CHECKING`, added locally by the reviewer and not committed.
- **When** `uv run tach check` runs.
- **Then** it exits non-zero and its output names `wio.models` and `wio.io`.

### **AC-4** Only `wio.cli` imports an adapter

An import of `wio.io.adapters` or `wio.env.adapters` from any module but
`wio.cli` fails the check and names both modules.

#### A component importing an adapter

- **Given** a `.py` module in `wio.rule` that imports `wio.io.adapters`, added
  locally by the reviewer and not committed.
- **When** `uv run tach check` runs.
- **Then** it exits non-zero and its output names `wio.rule` and
  `wio.io.adapters`.

#### A component importing an environment adapter

- **Given** a `.py` module in `wio.log` that imports `wio.env.adapters`, added
  locally by the reviewer and not committed.
- **When** `uv run tach check` runs.
- **Then** it exits non-zero and its output names `wio.log` and
  `wio.env.adapters`.

### **AC-5** The repository's gates run the check

`make lint` runs the tach hook, so `make check` and continuous integration run
it, and a violation fails them.

#### The hook is part of lint

- **Given** the delivered tree.
- **When** `make lint` runs.
- **Then** the output lists the `tach check` hook as passed, and `make check`
  passes.

#### A violation fails lint

- **Given** the forbidden import of AC-2, added locally by the reviewer.
- **When** `make lint` runs.
- **Then** it exits non-zero and the `tach check` hook is reported as failed.

#### The command is documented

- **Given** the delivered tree.
- **When** the commands list of `AGENTS.md` is read.
- **Then** it lists `uv run tach check`.

## Additional context

- The [parent Work](../README.md) states the dependency direction that this Work
  implements, its first assumption is the gap with the stubs, and its Non-Goals
  say why the trials are not committed.
