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
disagree.

## Goals

- Every field of a record is checked against the config and the Works it names.
- A Work that only `HEAD` has, because the commit being made deletes it, is
  checked from its contract at `HEAD`.
- A stage outside the Work's pipeline is warned about and not refused.

## Non-Goals

- The record's own form, which the shape leaf judges.
- Reading a message, printing a record or choosing an exit code; the commands
  do that.
- Deciding where the Works of the working tree or the index are read from.

## Assumptions

### A-1

A source of Works hides where a Work's contract is read from, including the
fallback to `HEAD`, so the validator is a function of a record, a source and the
config, as the driver chose.

## Mechanisms

- **`validate_record(record, source, config) -> list[Diagnostic]`** — the one
  validator, in `wio.trailers`, which returns the diagnostics of a record in the
  order of its fields. The architecture stage fixes the exact types.
- **`Diagnostic`** — a frozen value of a severity, `error` or `warning`, a
  position and a message. The position is the line of the field when the record
  carries lines, and the key of the field otherwise.
- **Source of Works** — gives the contract of a Work by its id, from the working
  tree or the index and otherwise from `HEAD`, through the `History` port's
  `list_files` and `show`.

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

- **Given** R with `Wio-Work: zz9zz9`, which is in neither the source nor
  `HEAD`.
- **When** `validate_record` runs.
- **Then** it returns one `error` naming `zz9zz9`.

#### A Work that only `HEAD` has

- **Given** R with `Wio-Work: d4e5f6`, a leaf Work that is in `HEAD` and not in
  the source.
- **When** `validate_record` runs, and again with `Wio-Items: AC-99`, which its
  contract at `HEAD` does not have.
- **Then** it returns no diagnostic for the first and one `error` naming
  `AC-99` for the second.

### **AC-3** The names must be in the config

#### An action or a stage the config does not have

- **Given** R with `Wio-Action: nosuch`, and R with `Wio-Stage: nosuch`.
- **When** `validate_record` runs on each.
- **Then** it returns one `error` for each naming `nosuch`.

### **AC-4** The items must be each Work's own

#### An item the Work does not have

- **Given** R with `Wio-Items: AC-99`, and R with `Wio-Work: k3m9xq, a7b2c4`
  and `Wio-Items: AC-3`, where `a7b2c4` has the item `AC-1` and not `AC-3`.
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

### **AC-7** The position follows the record

#### A line or a key

- **Given** R with `Wio-Stage: nosuch` whose fields carry the lines 3 to 5, and
  the same record whose fields carry no lines.
- **When** `validate_record` runs on each.
- **Then** the `error` has the position `5` for the first and `Wio-Stage` for
  the second.
