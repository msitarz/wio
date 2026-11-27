<!-- wio
id = "njzd0v"
template = "feature.leaf"
roots = ["wio"]
depends_on = []
-->

# Describe model, component descriptors and anti-drift checks

## Purpose

Provide typed, code-derived descriptor models and a verified registry for every
`wio` subcommand so `wio describe` cannot silently drift from the live
implementation.

## Goals

- Define immutable descriptor types for the top-level engine overview and for
  individual subcommands.
- Derive live facts directly from `wio.cli.table`, `wio.config.schema` and
  `wio.formats.directives` instead of duplicating them by hand.
- Provide concise, accurate per-command semantics for every registered
  subcommand (`config`, `context`, `contracts`, `describe`, `log`, `rules`,
  `templates`, `trailers`).
- Enforce descriptor completeness against `wio.cli.table` in `tests/tooling/`.

## Non-Goals

- CLI argument parsing, stdout/stderr writing or text/JSON formatting (owned by
  `pjm6ft`).

## Assumptions

None.

## Mechanisms

- `src/wio/describe/models.py` (provisional) defines frozen dataclasses
  `EngineDescription` and `CommandDescription`.
- `src/wio/describe/registry.py` (provisional) builds descriptions by combining
  live data from `wio.cli.table`, `wio.config.schema` and
  `wio.formats.directives` with concise per-command semantics.
- `tests/tooling/test_describe_sync.py` (provisional) verifies that the
  descriptor registry matches `wio.cli.table` one-to-one.

## Constraints

None beyond those inherited from `4t3yaf`.

## Acceptance criteria

### **AC-1** Engine overview derives version, exit codes and command list

Calling `describe_engine() -> EngineDescription` returns the package version,
the four exit codes (`0`, `1`, `2`, `70`) with their meanings, core concepts
and the sorted list of all commands registered in `wio.cli.table`.

### **AC-2** Per-command descriptors combine live tables with concise semantics

Calling `describe_command(name: str) -> CommandDescription` returns the
command's summary, subcommands/forms, key invariants and any code-derived
reference data (e.g. config schema keys for `config`, directive table for
`templates`), and raises `WioError` naming the valid commands when `name` is
unknown.

### **AC-3** Anti-drift tooling test catches missing or stale descriptors

The tooling test suite fails if a command is added to or removed from
`wio.cli.table` without a matching descriptor in `wio.describe`.
