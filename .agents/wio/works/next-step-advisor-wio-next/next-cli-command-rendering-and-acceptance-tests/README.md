<!-- wio
id = "rqms5z"
template = "feature.leaf"
roots = ["wio"]
depends_on = ["et1n2v"]
-->

# Next CLI command, rendering and acceptance tests

## Purpose

Expose `wio next [<work>] [--json]` on the command line with clear text and
JSON output and register it in `wio.cli.table` and `wio.describe`.

## Goals

- Parse `wio next [<work>] [--json]` and wire it into `wio.cli.table` with lazy
  loading.
- Render ready steps (including parallel Works) with their Work id, title,
  action, stage, reason and exact `wio context <work> <action> <stage>`
  command, plus `--json` output.
- Register `next` in `wio.describe.registry` so `wio describe` and
  `wio describe next` stay synchronized.
- Verify end-to-end behavior with unit and acceptance tests.

## Non-Goals

- History reading or state evaluation logic (owned by `cthw24` and `et1n2v`).

## Assumptions

None.

## Mechanisms

- `src/wio/next/render.py` (provisional) formats `NextStep` results as
  deterministic text or single-line JSON via `wio.formats.encode_json`.
- `src/wio/next/command.py` (provisional) implements `run(...)` for
  `wio next [<work>] [--json]`.
- `src/wio/cli/table.py` and `src/wio/describe/registry.py` register `next`.
- `tests/acceptance/next/test_next.py` (provisional) verifies `wio next`
  end-to-end.

## Constraints

None beyond those inherited from `45f1sa`.

## Acceptance criteria

### **AC-1** `wio next` lists all ready steps or reports none

Running `wio next` with no `<work>` prints every ready Work's next step and
`wio context` command (or a clear message when no Work is ready) and exits 0;
`--json` prints the structured JSON array.

### **AC-2** `wio next <work>` shows one Work's status or exits 2

Running `wio next <work>` prints that Work's ready step, blocking reasons, or
done status and exits 0; an unknown `<work>` prints an error to stderr and
exits 2.

### **AC-3** Registered in CLI and `wio describe`

`wio next --help`, `wio describe`, and `wio describe next` all include `next`
and pass `tests/tooling/test_describe_sync.py`.
