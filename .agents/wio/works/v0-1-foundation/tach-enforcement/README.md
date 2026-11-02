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

- `tach.toml` encodes the dependency direction between the packages of
  `src/wio`.
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
  the behavior verified for this contract: it counts lazy and `TYPE_CHECKING`
  imports when `ignore_type_checking_imports = false`.
- **A-2**: The stubs hold no `.py` code, so the skeleton gives tach few real
  edges to check, and the table is exercised as components land.

## Mechanisms

- `tach.toml` at the repository root, with `source_roots = ["src"]`, one
  `[[modules]]` entry per package of `src/wio` and its `depends_on`.
- `ignore_type_checking_imports = false`, because ports are imported only under
  `TYPE_CHECKING`.
- A local hook in `prek.toml` that runs `uv run tach check`, so `make lint` and
  `make check` run it.
- A tach interface for `wio.io` that exposes its ports to components and its
  adapters only to `wio.cli`, if tach can express it; otherwise a documented
  gap. This design is provisional.

## Acceptance criteria

### **AC-1** Every package is a module with the allowed dependencies

`tach.toml` has one module per package directly under `src/wio`, with these
`depends_on`:

| Module | May depend on |
| --- | --- |
| `wio.models` | nothing |
| `wio.formats`, `wio.io` | `wio.models` |
| `wio.config`, `wio.contract`, `wio.rule`, `wio.trailers`, `wio.log`, `wio.context` | `wio.models`, `wio.formats`, `wio.io` |
| `wio.cli` | every other module |

#### The clean tree passes

- **Given** the delivered tree.
- **When** `uv run tach check` runs.
- **Then** it exits 0.

### **AC-2** A component importing another component fails the check

An import between two components, from `wio.rule` to `wio.config` for example,
fails `tach check` and names both modules.

#### A forbidden import

- **Given** a `.py` module in `wio.rule` that imports `wio.config`.
- **When** `uv run tach check` runs.
- **Then** it exits non-zero and its output names `wio.rule` and `wio.config`.

### **AC-3** An import under `TYPE_CHECKING` counts

A dependency that exists only under `TYPE_CHECKING` is checked like any other.

#### A forbidden type-only import

- **Given** a `.py` module in `wio.models` that imports `wio.io` under
  `TYPE_CHECKING`.
- **When** `uv run tach check` runs.
- **Then** it exits non-zero and its output names `wio.models` and `wio.io`.

### **AC-4** The repository's gates run the check

`make lint` runs the tach hook, so `make check` and continuous integration run
it, and a violation fails them.

#### The hook is part of lint

- **Given** the delivered tree.
- **When** `make lint` runs.
- **Then** the output lists the `tach check` hook as passed, and `make check`
  passes.

#### A violation fails lint

- **Given** the forbidden import of AC-2.
- **When** `make lint` runs.
- **Then** it exits non-zero and the `tach check` hook is reported as failed.

## Additional context

- The [parent Work](../README.md) states the dependency direction and the gaps
  (A-1, A-5 and A-6) that this Work implements and accepts.
- The scenarios with a forbidden import are tried locally by the reviewer and
  are not committed (parent A-5).
