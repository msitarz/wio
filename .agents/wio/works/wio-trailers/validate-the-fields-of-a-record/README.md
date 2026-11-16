<!-- wio
id = "hk3qt5"
template = "feature.leaf"
roots = ["wio"]
depends_on = ["pnf585"]
-->

# Validate the fields of a record

## Purpose

The write command and the commit-time check both judge a record's fields
against the config and the Works, and two copies of that judgment would
disagree, so that a record could pass one and fail the other.

## Goals

- Every field of a record is checked against the config and the Works it names.
- A Work that only `HEAD` has, because the commit being made deletes it, is
  checked from its contract at `HEAD`.
- A stage outside the Work's pipeline is warned about and not refused.

## Non-Goals

- The record's own form, which the shape leaf judges.
- Reading a message, printing a record or choosing an exit code; the commands
  do that.
- Deciding how the Works of the index are read, which the contract component
  settles.

## Assumptions

None.

## Mechanisms

- **`validate_record(record, contracts, config) -> list[Diagnostic]`** — the one
  validator, in `wio.trailers`, which the architecture stage may type further.
  `record` is one record of the shape leaf's `Reading`, or a mapping of keys to
  values with their lines when it has them. `Wio-Work: none` has no Work to
  check and yields no diagnostic. A list of Works is checked for each Work in
  the order written. The diagnostics come in the order of the record's fields,
  with the Works of a list in the order written and errors and warnings
  interleaved by field.
- **`Diagnostic`** — the existing `wio.models.diagnostics.Diagnostic`, a frozen
  value of `severity`, `where` and `message`, whose `where` here is the line of
  the field as a string when the record carries lines and the key of the field
  otherwise. A diagnostic about an absent field or about the whole record uses
  the record's first line, or the key of the field it concerns when there are no
  lines.
- **`Contracts` port** — the provisional port of `src/wio/trailers/ports.pyi`,
  which the validator reads with `items` and `pipeline`. It finds a Work in the
  working tree and otherwise in `HEAD`, through `History.list_files` and
  `show`; how it reads the index is for the contract component to settle.

## Acceptance criteria

The examples use a Work `k3m9xq` with the items `AC-1` and `AC-3`. It is a leaf,
so its `deliver` is the `typed-boundary` stage preset, which lists the stages
`architecture`, which is not a gate, and `architecture-review`, which is a gate.
The config also has the stage `integration`, which that preset does not list,
and its results are `pass`, `fail` and `unknown`. R is the record `Wio-Work:
k3m9xq`, `Wio-Action: deliver` and `Wio-Stage: architecture`.

### **AC-1** A valid record has no diagnostics

#### Valid records of every form

- **Given** R, R with `Wio-Items: AC-3, AC-1`, R with the gate stage
  `architecture-review` and `Wio-Result: pass`, and the record `Wio-Work: none`.
- **When** `validate_record` runs on each.
- **Then** it returns no diagnostic for any.

### **AC-2** The Work must exist

#### A Work that exists nowhere

- **Given** R with `Wio-Work: zz9zz9`, which is in neither the working tree
  nor `HEAD`.
- **When** `validate_record` runs.
- **Then** it returns one `error` naming `zz9zz9`.

#### A Work that only `HEAD` has

- **Given** R with `Wio-Work: d4e5f6`, a leaf Work that is in `HEAD` and not in
  the working tree, whose `deliver` lists `architecture`.
- **When** `validate_record` runs, and again with `Wio-Items: AC-99`, which its
  contract at `HEAD` does not have.
- **Then** it returns no diagnostic for the first and one `error` naming
  `AC-99` for the second.

### **AC-3** The names must be in the config

#### An action or a stage the config does not have

- **Given** R with `Wio-Action: nosuch`, and R with `Wio-Stage: nosuch`.
- **When** `validate_record` runs on each.
- **Then** it returns one `error` for each naming `nosuch`, and no `warning`.

### **AC-4** The items must be each Work's own

#### An item the Work does not have

- **Given** R with `Wio-Items: AC-99`, and R with `Wio-Work: k3m9xq, a7b2c4`
  and `Wio-Items: AC-3`, where `a7b2c4`, whose `deliver` lists `architecture`,
  has the item `AC-1` and not `AC-3`.
- **When** `validate_record` runs on each.
- **Then** it returns one `error` for each, naming `AC-99` and `AC-3`.

### **AC-5** A result is present exactly on a gate and is one the config lists

#### A gate without a result, and a result on a stage that is not a gate

- **Given** R with the stage `architecture-review` and no `Wio-Result`, and R
  with `Wio-Result: pass`.
- **When** `validate_record` runs on each.
- **Then** it returns one `error` for each, `result required` for the first and
  `not a gate` for the second.

#### A result the config does not list

- **Given** R with the stage `architecture-review` and `Wio-Result: maybe`.
- **When** `validate_record` runs.
- **Then** it returns one `error` naming `maybe`.

### **AC-6** A stage outside the Work's pipeline is a warning

#### A stage that the Work's actions do not list

- **Given** R with `Wio-Stage: integration`.
- **When** `validate_record` runs.
- **Then** it returns one `warning` naming `integration` and no `error`.

### **AC-7** The place follows the record

#### A present field

- **Given** R with `Wio-Stage: nosuch` whose fields carry the lines 3 to 5, and
  the same record whose fields carry no lines.
- **When** `validate_record` runs on each.
- **Then** the `error` has `where` `5` for the first and `Wio-Stage` for the
  second.

#### An absent field

- **Given** R with the stage `architecture-review` and no `Wio-Result`, with the
  lines 3 to 5 and without lines.
- **When** `validate_record` runs on each.
- **Then** the `error` has `where` `3`, the record's first line, for the first
  and `Wio-Result` for the second.

### **AC-8** The diagnostics come in the order of the fields

#### A record with two errors

- **Given** R with `Wio-Action: nosuch`, `Wio-Stage: nosuch` and
  `Wio-Items: AC-99`, in that order of fields.
- **When** `validate_record` runs.
- **Then** it returns the `error` for the action, then the one for the stage,
  then the one for `AC-99`.
