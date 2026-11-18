<!-- wio
id = "sk5wwq"
template = "feature.leaf"
roots = ["wio"]
depends_on = ["pnf585", "hk3qt5", "chqy1s"]
-->

# Check a body or range afterwards

## Purpose

A pull request body and the commits of a range are checked long after their
records were written, so the check must keep a record that was valid then from
failing now.

## Goals

- A pull request body, or the commits of a range, whose records are malformed
  fail the check and say where, with the line number and, for a range, the
  commit.
- A record that was valid when it was written passes after the config or the
  Works have changed, with a warning for a name the config no longer has.
- A record the reader cannot see, or a name the engine does not define, is
  reported without failing the check.

## Non-Goals

- Checking that a Work or an item id exists; Works are deleted later and the
  readers ignore unknown ids.
- Requiring a record; a body or commit of no Work has none.
- Checking a message as it is committed; the commit-time check does that.

## Assumptions

### A-1

`--ref-range` is the provisional name of the flag that selects a range of
commits, as the A-3 of the top parent `3jbrzz` says.

### A-2

A call that gives both a path and `--ref-range` is a usage error, since the two
read different inputs.

## Mechanisms

- **`wio trailers check [PATH]`** — reads a body from the file `PATH`, or from
  standard input when `PATH` is `-` or absent.
- **`wio trailers check --ref-range RANGE`** — reads the message of each commit
  of the range, with the reader that `[trailers] reader` names in the config.
- **Diagnostics** — each error and warning is printed on standard error as
  `<severity>: <where>: <message>`, sorted, where `<where>` is the 1-based line
  number in the body, or the full id of the commit and the line in its message
  as `<id>:<line>`; commits come oldest first.
- **Exit codes** — 1 when there is an error, 2 on a usage error, a file that
  cannot be read or a `ValueError` or `RuntimeError` of the `History` port, and
  otherwise 0; a warning never changes the exit code.
- **`check_shape(message, reader) -> list[Finding]`** — the shape leaf's check,
  whose `malformed` finding is an error and whose `invisible` and `unknown-key`
  findings are warnings.
- **`validate_names(record, config)`** — the validator leaf's name checks, whose
  errors this mode turns into warnings.
- **`History.history(revision_range) -> Sequence[Commit]`** — gives the commits
  of a range with their messages, oldest first.

## Acceptance criteria

The examples use a body B of the line `Fix the bug.`, a blank line and R, the
paragraph `Wio-Work: k3m9xq`, `Wio-Action: deliver` and
`Wio-Stage: architecture`, so that R's lines are 3 to 5. A range has the
commits `c1`, `c2` and `c3` from the oldest, each of the message B. The config's
results are `pass`, `fail` and `unknown`, and its reader is `scan` unless a
scenario says otherwise.

### **AC-1** The interface

#### A body from a file and from standard input

- **Given** B with `Wio-Work: k3 m9xq`, in a file and on standard input.
- **When** `wio trailers check <file>`, `wio trailers check -` and
  `wio trailers check` read it.
- **Then** each exits 1 and prints on standard error the same diagnostic, which
  begins `error: 3:`.

#### Inputs that cannot be read

- **Given** a path that does not exist, a call that gives a path and
  `--ref-range`, a range `nosuch..nosuch2`, and a directory that is not in a
  repository.
- **When** `wio trailers check <path>`, `wio trailers check <path> --ref-range
  main..HEAD`, `wio trailers check --ref-range nosuch..nosuch2` and
  `wio trailers check --ref-range main..HEAD` run in them.
- **Then** each exits 2.

### **AC-2** A malformed record fails the check

#### A body and a range with a malformed record

- **Given** B with `Wio-Work: k3 m9xq`, and a range whose `c2` has that message
  while `c1` and `c3` are valid and `c3` also has an unknown name.
- **When** `wio trailers check` reads the body and `--ref-range` reads the
  range.
- **Then** each exits 1, the body's diagnostic begins `error: 3:`, the range's
  begins `error:` followed by the full id of `c2` and `:3:`, and the commits
  `c1` and `c3` add no error.

### **AC-3** A record that was valid when written passes

#### A name the config no longer has

- **Given** B with `Wio-Stage: nosuch`, B with `Wio-Action: nosuch`, and B with
  the stage `architecture-review` and `Wio-Result: maybe`.
- **When** `wio trailers check` reads each.
- **Then** each exits 0 and prints a `warning:` that names `nosuch`, `nosuch`
  and `maybe`.

#### A Work that was deleted

- **Given** B with `Wio-Work: d4e5f6`, which is in no tree, and
  `Wio-Items: AC-99`.
- **When** `wio trailers check` reads it.
- **Then** it exits 0 and prints nothing.

### **AC-4** What the reader cannot see or does not define is a warning

#### A line the reader cannot see

- **Given** B whose paragraph also holds the prose line `Fixes the login bug`,
  with the `scan` reader, and the range commit `c2` of that message with the
  `git` reader and a blank line and a `Co-authored-by` paragraph after R.
- **When** `wio trailers check` reads the body and `--ref-range` reads the
  range.
- **Then** each exits 0 and prints a `warning:` for each `Wio-` line that the
  reader cannot see, at its line.

#### A name the engine does not define

- **Given** B with a `Wio-Criteria: AC-1` line as line 6 of R's paragraph.
- **When** `wio trailers check` reads it.
- **Then** it exits 0 and prints a `warning: 6:` that names `Wio-Criteria`.

### **AC-5** No record is not a failure

#### A body, a commit and an empty range

- **Given** a body of `Fix the bug.` alone, a range of one commit with that
  message, and a range of no commit.
- **When** `wio trailers check` reads the body and `--ref-range` reads each
  range.
- **Then** each exits 0 and prints nothing.
