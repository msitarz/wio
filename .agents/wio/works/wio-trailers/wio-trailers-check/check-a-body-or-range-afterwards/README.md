<!-- wio
id = "sk5wwq"
template = "feature.leaf"
roots = ["wio"]
depends_on = ["pnf585"]
-->

# Check a body or range afterwards

## Purpose

A pull request body and the commits of a range are checked long after their
records were written, so the check must keep a record that was valid then from
failing now.

## Goals

- A pull request body, or the commits of a range, whose records are malformed
  fail the check and say where.
- A record that was valid when it was written passes after the config or the
  Works have changed.
- A record the reader cannot see, or a key the engine does not define, is
  reported without failing the check.

## Non-Goals

- Checking that a Work or an item id exists; Works are deleted later and the
  readers ignore unknown ids.
- Requiring a record; a body or commit of no Work has none.
- Checking a message as it is committed; the commit-time check does that.

## Assumptions

### A-1

`--ref-range` is the provisional name of the flag that selects a range of
commits, as the parent's A-3 says.

## Mechanisms

- **`wio trailers check`** — without `--require`, reads a body from a file or
  from standard input, or the commits of the range that `--ref-range` names, and
  exits 1 on an error.
- **Shape check** — the findings of the shape leaf, which this mode turns into
  errors and warnings.
- **`History` port** — gives the commits of a range with their messages.

## Acceptance criteria

### **AC-1** A malformed record fails the check

#### A body with a malformed record

- **Given** a body whose record has a `Wio-Work` value that is not a valid id.
- **When** `wio trailers check` reads it.
- **Then** the command exits 1 and names the value.

#### A range with one malformed commit

- **Given** a range of three commits, the second carrying a malformed record.
- **When** `wio trailers check --ref-range` reads the range.
- **Then** the command exits 1 and names the second commit.

### **AC-2** A record that was valid when written passes

#### A name the config no longer has

- **Given** a body whose well-formed record has `Wio-Stage: nosuch`.
- **When** `wio trailers check` reads it.
- **Then** the command exits 0 and warns about the stage.

#### A Work that was deleted

- **Given** a body whose record names a Work that no longer exists.
- **When** `wio trailers check` reads it.
- **Then** the command exits 0 and reports nothing about the Work.

### **AC-3** What the reader cannot see or does not define is a warning

#### A line the reader cannot see

- **Given** a body with a `Wio-` line in a paragraph that is not a record.
- **When** `wio trailers check` reads it.
- **Then** the command exits 0 and warns about that line.

#### A key the engine does not define

- **Given** a body with a valid record and a `Wio-Criteria` line.
- **When** `wio trailers check` reads it.
- **Then** the command exits 0 and warns about `Wio-Criteria`.

### **AC-4** No record is not a failure

#### A body and a commit with no record

- **Given** a body with no record, and a range with a commit with no record.
- **When** `wio trailers check` reads the body, and `--ref-range` reads the
  range.
- **Then** both commands exit 0.
