<!-- wio
id = "cthw24"
template = "feature.leaf"
roots = ["wio"]
depends_on = []
-->

# History record reader and revert dropping

## Purpose

Read `Wio-*` records from git history in chronological order while dropping the
records of any commit that was later reverted, giving `wio.next` a clean
history of effective records.

## Goals

- Walk first-parent commits via `wio.io.History` and parse `Wio-*` records with
  the configured `trailers.reader` (`scan` or `git`).
- Detect standard git revert commits (`This reverts commit <sha>.`) and drop
  the reverted commit's records (with a revert-of-a-revert restoring the
  original commit).
- Return effective records in oldest-to-newest order with commit SHA and parsed
  fields.

## Non-Goals

- Evaluating Work state, gate passes or staleness (owned by `et1n2v`).
- CLI argument parsing or output rendering (owned by `rqms5z`).

## Assumptions

None.

## Mechanisms

- `src/wio/next/history.py` (provisional) defines `EffectiveRecord` and
  `read_effective_records(history, reader) -> tuple[EffectiveRecord, ...]`.
- `wio.formats.records` parses commit messages using the configured reader.

## Constraints

None beyond those inherited from `45f1sa`.

## Acceptance criteria

### **AC-1** Effective records are returned oldest-to-newest

`read_effective_records` walks `History`, parses every `Wio-*` record with the
configured reader, skips commits without records and `Wio-Work: none`, and
returns records in oldest-to-newest commit order.

### **AC-2** Reverted commits have their records dropped

When a later commit contains `This reverts commit <sha>.`, all records from
`<sha>` are omitted from the returned tuple; a second revert of the revert
commit restores `<sha>`'s records.
