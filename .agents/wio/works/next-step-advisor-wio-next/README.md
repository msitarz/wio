<!-- wio
id = "45f1sa"
template = "feature.parent"
roots = ["@descendants"]
depends_on = []
-->

# Next step advisor (wio next)

## Purpose

Let agents and drivers ask wio which Work, action and stage to run next (and
which Works can proceed in parallel), computed deterministically from git
trailer history and contracts instead of manual guesswork.

## Goals

- Read `Wio-*` records from git history while ignoring records of reverted
  commits.
- Determine the next action and stage for each active Work from its resolved
  pipelines, gate results, `judge = "human"` requirements, `invalidated_by`
  staleness rules and dependency graph.
- Expose `wio next [<work>] [--json]` printing ready steps (including parallel
  Works) and the exact `wio context <work> <action> <stage>` command to run, or
  explaining why a requested Work is blocked or complete.
- Register `next` in `wio.cli.table` and `wio.describe` so agents can discover
  it offline.

## Non-Goals

- Executing stages, mutating contracts or creating commits.
- Enforcing or blocking a driver from choosing another action or stage.
- Reading non-git external issue trackers or CI status.

## Assumptions

None.

## Mechanisms

- `wio.next` (new package under `src/wio/next/`) owns the history record
  reader, state/staleness evaluator, text/JSON renderer and CLI command.
- `wio.io.History` provides the first-parent commit stream; `wio.formats`
  parses `Wio-*` trailers with the configured `trailers.reader`.
- `wio.cli.table` and `wio.describe` register `next` as a top-level subcommand.

## Constraints

- **C-1 Read-only.** `wio next` never writes to the working tree, git
  repository or event log (verified by acceptance tests).
- **C-2 Architecture boundary.** `wio.next` respects `tach.toml` dependency
  rules and imports `json` only through `wio.formats.encode_json` (verified by
  `tach check` and `ruff check`).
- **C-3 Deterministic output.** Identical repository history, contracts and
  config produce byte-for-byte identical text and JSON output (verified by unit
  and acceptance tests).

## Visuals

Baseline: `4a173b4` (`main`). Proposed addition of `wio.next` (provisional
module layout):

```mermaid
flowchart LR
    CLI[wio.cli.dispatch] --> TBL[wio.cli.table]
    TBL --> NXT[wio.next - new]
    NXT --> HIST[wio.io.History]
    NXT --> CTR[wio.contracts]
    NXT --> FMT[wio.formats]
```

## Acceptance criteria

### **AC-1** `wio next` proposes ready stages including parallel Works

Running `wio next` (text and `--json`) in a repository with active Works
outputs every ready Work's next action, stage and `wio context` command,
respecting `depends_on`, parent-after-children, gate passes and
`invalidated_by` staleness.

### **AC-2** Reverted commits do not advance or pass stages

If a commit carrying `Wio-*` trailers (including a gate `pass`) is reverted by
a later revert commit, `wio next` treats its records as absent.

### **AC-3** Single-Work query reports ready, blocked or done state

Running `wio next <work>` reports the next step when ready, names blocking
dependencies or incomplete children when blocked, reports complete when all
non-on-demand actions have passed, and exits 2 for an unknown Work id.
