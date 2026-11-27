<!-- wio
id = "pjm6ft"
template = "feature.leaf"
roots = ["wio"]
depends_on = ["njzd0v"]
-->

# Describe CLI command, rendering and acceptance tests

## Purpose

Expose `wio describe [<command>] [--json]` on the command line with concise
one-screen text and structured JSON output so agents can inspect wio directly.

## Goals

- Wire `describe` into `wio.cli.table` with lazy loading so other commands pay
  no startup cost.
- Render `EngineDescription` and `CommandDescription` as concise, deterministic
  one-screen text or single-line JSON (`--json`).
- Verify end-to-end CLI behavior (valid commands, `--json`, unknown command
  exit 2, outside-repo execution) with unit and acceptance tests.

## Non-Goals

- Defining descriptor models or anti-drift registry checks (owned by `njzd0v`).

## Assumptions

None.

## Mechanisms

- `src/wio/describe/render.py` (provisional) formats `EngineDescription` and
  `CommandDescription` as deterministic text or JSON via
  `wio.formats.encode_json`.
- `src/wio/describe/command.py` (provisional) parses `[<command>] [--json]` and
  writes to `Stdio`.
- `src/wio/cli/table.py` adds the `describe` entry pointing to
  `wio.describe:run`.
- `tests/acceptance/describe/test_describe.py` (provisional) verifies the
  command through the CLI acceptance driver.

## Constraints

None beyond those inherited from `4t3yaf`.

## Acceptance criteria

### **AC-1** `wio describe` renders a concise engine overview

Running `wio describe` prints the version, exit codes, core concepts and
subcommand list as deterministic text ending in one newline and exits 0;
`--json` prints the equivalent JSON object.

### **AC-2** `wio describe <command>` renders one command's semantics

Running `wio describe <command>` prints that command's summary, forms/options,
invariants and code-derived tables as deterministic text ending in one newline
and exits 0; `--json` prints the equivalent JSON object.

### **AC-3** Unknown command exits 2 with valid choices

Running `wio describe nosuch` (with or without `--json`) prints an error naming
the valid command names to stderr and exits 2.

### **AC-4** Works outside any repository without config

Running `wio describe` and `wio describe config` in an empty temporary
directory with no `.git` and no `.agents/wio/config.toml` exits 0.
