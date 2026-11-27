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
  dispatch.
- Render ready steps (including parallel Works) with their Work id, title,
  action, stage, reason and exact `wio context <work> <action> <stage>`
  command, plus `--json` output.
- Register `next` in `wio.describe.registry` so `wio describe` and
  `wio describe next` stay synchronized.

## Non-Goals

- History reading or state evaluation logic (owned by `cthw24` and `et1n2v`).

## Assumptions

None.

## Mechanisms

- `src/wio/next/render.py` (provisional) formats `NextStep` results as
  deterministic text or single-line JSON via `wio.formats.encode_json`.
- `src/wio/next/command.py` (provisional) implements `run(argv: Sequence[str],
  stdio: Stdio, ...) -> int` for `wio next [<work>] [--json]`.
- `src/wio/cli/table.py` and `src/wio/describe/registry.py` register `next`.
- `tests/acceptance/next/test_next.py` (provisional) verifies `wio next`
  end-to-end.

## Constraints

None beyond those inherited from `45f1sa`.

## Acceptance criteria

### **AC-1** `wio next` lists all ready steps or reports none

Running `wio next` with no `<work>` prints every ready Work's next step and
`wio context <work> <action> <stage>` command (or a clear message when no Work
is ready) and exits 0; `wio next --json` prints a JSON array of objects with
fields `work_id`, `title`, `status`, `action`, `stage`, `reason`, `blocked_by`,
and `command` (`[]` when no Work is ready).

### **AC-2** `wio next <work>` shows one Work's status or exits 2

Running `wio next <work>` prints that Work's ready step, blocking reasons, or
done status and exits 0 (`--json` prints a single JSON object with the same
fields as AC-1); an unknown `<work>` or invalid arguments print an error to
stderr and exit 2.

### **AC-3** Registered lazily in CLI and `wio describe`

`wio next --help`, `wio describe`, and `wio describe next` all include `next`,
`wio.cli.table` registers `next` via lazy module lookup, and
`tests/tooling/test_describe_sync.py` passes.
