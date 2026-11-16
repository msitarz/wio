<!-- wio
id = "vy01kg"
template = "feature.leaf"
roots = ["wio"]
depends_on = ["pnf585"]
-->

# Check a message at commit time

## Purpose

A commit message is checked against the config and the Works it was written
for, so a wrong record is refused before it enters the history.

## Goals

- A commit message whose record names something the config does not have, a
  Work or item id that does not exist, or a result that does not fit its stage
  is refused.
- A commit message with no record is refused unless its subject is one that git
  writes for a merge, a revert or a squash.
- A problem of a record's own form, or a record the reader cannot see, is
  refused.
- A key the engine does not define, or a stage outside the Work's actions, is
  warned about and not refused.

## Non-Goals

- Checking a pull request body or a range of commits; the later check does
  that.
- Writing a record; `wio trailers <work> <action> <stage>` does that.

## Assumptions

### A-1

A finding of the kind `unknown-key` is a warning at commit time, as it is
afterwards, deliberately: a `Wio-` key that the engine no longer defines is not
a reason to refuse a commit, even though a typo of a key then passes with a
warning. The driver confirms this at the gate.

## Mechanisms

- **`wio trailers check --require [PATH]`** — reads the commit message in the
  file `PATH`, or on standard input when `PATH` is `-` or absent. It prints each
  error and warning on standard error, exits 1 when there is an error, 2 when
  `PATH` cannot be read and otherwise 0. A warning never changes the exit code.
- **`check_shape(message, reader) -> list[Finding]`** — the shape check of the
  shape leaf, with the reader that `[trailers] reader` names in the config. This
  mode turns a `malformed` or `invisible` finding into an error and an
  `unknown-key` finding into a warning.
- **`History` port** — gives the Works of `HEAD`, which finds a Work that the
  commit being made deletes. The Works of the index are read from the
  repository's index.

## Acceptance criteria

The examples use a Work `k3m9xq` that is in the index and has an item `AC-1`.
Its `deliver` action lists the stages `architecture`, which is not a gate, and
`architecture-review`, which is a gate. The config also has the stage `wiring`,
which `k3m9xq`'s `deliver` does not list. R is the paragraph `Wio-Work:
k3m9xq`, `Wio-Action: deliver` and `Wio-Stage: architecture`, and M is the
subject `feat: add x`, a blank line and R.

### **AC-1** The interface

#### A message from a file and from standard input

- **Given** M with `Wio-Stage: nosuch` in place of its stage, in a file and on
  standard input.
- **When** `wio trailers check --require <file>` and
  `wio trailers check --require -` read it.
- **Then** each exits 1 and prints on standard error the same finding naming the
  stage.

#### A file that cannot be read

- **Given** a path that does not exist.
- **When** `wio trailers check --require <path>` runs.
- **Then** the command exits 2.

### **AC-2** A valid message passes

#### A valid record, and a record of no Work

- **Given** M, and a message of the subject `feat: add x` and a paragraph
  `Wio-Work: none`.
- **When** `wio trailers check --require` reads each.
- **Then** each exits 0 and prints nothing.

#### A list of two valid Works

- **Given** a second Work `a7b2c4` in the index with an item `AC-1`, and M with
  `Wio-Work: k3m9xq, a7b2c4`.
- **When** `wio trailers check --require` reads it.
- **Then** the command exits 0 and prints nothing.

### **AC-3** Names are checked against the config

#### An action or a stage the config does not have

- **Given** M with `Wio-Action: nosuch`, and M with `Wio-Stage: nosuch`.
- **When** `wio trailers check --require` reads each.
- **Then** each exits 1 and names the unknown name.

### **AC-4** The Works and their items must exist

#### A Work that exists nowhere

- **Given** M with `Wio-Work: zz9zz9`, which is in neither the index nor
  `HEAD`.
- **When** `wio trailers check --require` reads it.
- **Then** the command exits 1 and names `zz9zz9`.

#### A Work that the commit deletes

- **Given** M for a Work `d4e5f6` that is in `HEAD` and not in the index, whose
  `deliver` action lists `architecture`.
- **When** `wio trailers check --require` reads it.
- **Then** the command exits 0.

#### An item id outside the Work

- **Given** M with `Wio-Items: AC-99`, which `k3m9xq` does not have, and the
  same for the Work `d4e5f6` that is only in `HEAD`.
- **When** `wio trailers check --require` reads each.
- **Then** each exits 1 and names `AC-99`.

#### A list with one Work that does not exist

- **Given** M with `Wio-Work: k3m9xq, zz9zz9`.
- **When** `wio trailers check --require` reads it.
- **Then** the command exits 1 and names `zz9zz9`.

### **AC-5** A result is present exactly on a gate

#### A gate without a result

- **Given** M with `Wio-Stage: architecture-review` and no `Wio-Result`.
- **When** `wio trailers check --require` reads it.
- **Then** the command exits 1 and reports that a result is required.

#### A result on a stage that is not a gate

- **Given** M with `Wio-Result: pass`.
- **When** `wio trailers check --require` reads it.
- **Then** the command exits 1 and reports that the stage is not a gate.

### **AC-6** A record is required unless git wrote the subject

#### A message with no record

- **Given** a message with the subject `feat: add x` and no record.
- **When** `wio trailers check --require` reads it.
- **Then** the command exits 1 and reports that no record was found.

#### A subject that git writes

- **Given** messages with no record whose subjects start with `Merge `,
  `Revert `, `Reapply `, `fixup!` and `squash! `, one of them after a `#`
  comment line.
- **When** `wio trailers check --require` reads each.
- **Then** each exits 0.

#### A subject that only looks like one

- **Given** messages with no record whose subjects are `amend! x`, `fixup!x`
  and `Merged x`.
- **When** `wio trailers check --require` reads each.
- **Then** each exits 1 and reports that no record was found.

#### An exempt subject with a malformed record

- **Given** a message with the subject `Merge branch x` and a record with
  `Wio-Work: k3 m9xq`.
- **When** `wio trailers check --require` reads it.
- **Then** the command exits 1 and names the line.

### **AC-7** The findings of the shape check are judged

#### A malformed or invisible record is an error

- **Given** M with `Wio-Work: k3 m9xq`, and M whose record paragraph also holds
  a prose line, read by the `scan` reader.
- **When** `wio trailers check --require` reads each.
- **Then** each exits 1 and names the line.

#### Any bad record of a message is an error

- **Given** a message holding R and then a second record with
  `Wio-Stage: nosuch`.
- **When** `wio trailers check --require` reads it.
- **Then** the command exits 1 and names the second record's line.

#### An unknown key is a warning

- **Given** M with a `Wio-Criteria: AC-1` line.
- **When** `wio trailers check --require` reads it.
- **Then** the command exits 0 and warns about `Wio-Criteria`.

### **AC-8** A stage outside the Work's pipeline is a warning

#### A stage that the Work's actions do not list

- **Given** M with `Wio-Stage: wiring`.
- **When** `wio trailers check --require` reads it.
- **Then** the command exits 0 and warns about `wiring`.
