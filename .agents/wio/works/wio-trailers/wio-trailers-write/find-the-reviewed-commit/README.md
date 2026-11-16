<!-- wio
id = "92xps9"
template = "feature.leaf"
roots = ["wio"]
depends_on = ["pnf585"]
-->

# Find the reviewed commit

## Purpose

A gate's own commits sit on top of the artifact it judged, so the engine finds
the commit under them, and a later reader knows which artifact a review saw.

## Goals

- The commit a gate judged is found from the history, by skipping the pure gate
  commits above it.
- A history with no commit under the gate's own is reported as having none.

## Non-Goals

- The `--reviewed` override, and the warnings that compare the commit with the
  `context` event.
- Recording the result or writing the event; the gate leaf does that.

## Assumptions

None.

## Mechanisms

- **`reviewed_commit(works, action, stage, history, reader) -> str | None`** —
  walks `History.first_parents("HEAD")`, newest first, reads each message with
  the shape leaf's reader, and returns the sha of the first commit that is not a
  pure gate commit, or `None` when every commit is one.
- **Pure gate commit** — a commit with at least one record, all of which belong
  to the gate's action and stage once lists are expanded, for the Work or for
  others, as [concepts.md](../../../../../../docs/concepts.md#records) defines.

## Acceptance criteria

The examples use the gate `review-contract` of the action `define`, a Work
`k3m9xq`, and a history whose commits are named from the newest. A gate record
is the record of `k3m9xq` with `Wio-Action: define`, `Wio-Stage:
review-contract` and `Wio-Result: pass`, and the reader is `scan` unless a
scenario says otherwise.

### **AC-1** The gate's own commits are skipped

#### One or more pure gate commits above the work commit

- **Given** commits `c3` and `c2` that carry only a gate record, and `c1`, the
  work commit, that carries a record of `Wio-Action: define` and
  `Wio-Stage: define`.
- **When** `reviewed_commit` runs for `k3m9xq`, `define` and `review-contract`.
- **Then** it returns the sha of `c1`.

#### A commit that is pure for other Works

- **Given** a commit `c2` whose record is for `Wio-Work: a7b2c4, b8c9d0` with
  `Wio-Action: define` and `Wio-Stage: review-contract`, and `c1` as above.
- **When** `reviewed_commit` runs for `k3m9xq`.
- **Then** it returns the sha of `c1`.

### **AC-2** A commit that holds the artifact is not skipped

#### Another record beside the gate's

- **Given** `c2` that carries the gate record and also a record of
  `Wio-Stage: define`, and `c1` below it.
- **When** `reviewed_commit` runs.
- **Then** it returns the sha of `c2`.

#### No record, and a record of no Work

- **Given** `c2` with no record and `c3` that carries the gate record, and,
  in another history, `c2` whose only record is `Wio-Work: none`.
- **When** `reviewed_commit` runs on each.
- **Then** it returns the sha of `c2` for each.

### **AC-3** A history with no work commit has no reviewed commit

#### Only pure gate commits

- **Given** a history of commits that each carry only a gate record.
- **When** `reviewed_commit` runs.
- **Then** it returns `None`.

### **AC-4** The configured reader decides what a record is

#### A record outside the last paragraph, under `git`

- **Given** `c2` whose message holds a gate record, a blank line and then the
  paragraph `Co-authored-by: A <a@example.com>`, and `c1` below it, read with
  the `git` reader.
- **When** `reviewed_commit` runs.
- **Then** it returns the sha of `c2`, whose record the reader cannot see.
