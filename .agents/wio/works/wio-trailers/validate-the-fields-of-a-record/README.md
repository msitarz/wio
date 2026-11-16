<!-- wio
id = "hk3qt5"
template = "feature.leaf"
roots = ["wio"]
depends_on = ["pnf585", "jzvrtx"]
-->

# Validate the fields of a record

## Purpose

The write command and the commit-time check both judge a record's fields
against the config and the Works, and two copies of that judgment would
disagree, so that a record could pass one and fail the other.

## Goals

- Every field of a record except the judge is checked against the config and
  the Works it names.
- A stage outside the Work's pipeline is warned about and not refused.

## Non-Goals

- The record's own form, which the shape leaf judges.
- Judging the judge against its gate; the gate leaf does that.
- A stray `Wio-Items` or `Wio-Result` on a `Wio-Work: none` record, which the
  shape leaf judges.
- Finding a Work in the working tree, the index or `HEAD`, which the lookup leaf
  does.
- Reading a message, printing a record or choosing an exit code; the commands
  do that.

## Assumptions

### A-1

The messages `result required` and `not a gate`, which the criteria and the
commands report, are fixed wording.

## Mechanisms

- **`validate_record(record, contracts, config) -> list[Diagnostic]`** — the one
  validator, in `wio.trailers`, which takes a record that passed the shape
  check, the `Contracts` port of the lookup leaf and the config's action names,
  stage names, gate stages and `gates.results`, and which the architecture stage
  may type further.
- **Checks** — a Work that is absent gets its own error and no check of its
  items or pipeline, a name the config lacks gets an error and no pipeline
  warning, a stage the config lacks gets no result check, and every other field
  is still checked.
- **`Record`** — the ordered fields `(key, value, line or None)` of one record
  of the shape leaf's `Reading`, which the write command builds without lines.
- **`Diagnostic`** — the existing `wio.models.diagnostics.Diagnostic`, whose
  `where` here is the line of the field as a string, or the key of the field
  when the record has no lines, and, for an absent field, the record's first
  line or the key of the field concerned; the diagnostics come in the canonical
  order of the fields, `Wio-Work`, `Wio-Action`, `Wio-Stage`, `Wio-Items` and
  `Wio-Result`, an absent field at the place it would have, with one diagnostic
  per Work and per item, in the order written, and an item error naming the item
  and the Work.

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

- **Given** R with `Wio-Work: zz9zz9`, for which the `Contracts` port returns
  `None`.
- **When** `validate_record` runs.
- **Then** it returns one `error` naming `zz9zz9` and no other diagnostic.

#### Other fields are still checked

- **Given** R with `Wio-Work: zz9zz9` and `Wio-Stage: nosuch`.
- **When** `validate_record` runs.
- **Then** it returns the one `error` for `zz9zz9` and the one for `nosuch`, and
  no `warning`.

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
- **Then** it returns one `error` for each, the first naming `AC-99` and
  `k3m9xq` and the second naming `AC-3` and `a7b2c4`.

### **AC-5** A result is present exactly on a gate

#### A gate without a result, and a result on a stage that is not a gate

- **Given** R with the stage `architecture-review` and no `Wio-Result`, and R
  with `Wio-Result: pass`.
- **When** `validate_record` runs on each.
- **Then** it returns one `error` for each, `result required` for the first and
  `not a gate` for the second.

#### A result on a stage the config lacks

- **Given** R with `Wio-Stage: nosuch` and `Wio-Result: pass`.
- **When** `validate_record` runs.
- **Then** it returns the one `error` for `nosuch` and none for the result.

### **AC-6** A result is one the config lists

#### A result the config does not list

- **Given** R with the stage `architecture-review` and `Wio-Result: maybe`.
- **When** `validate_record` runs.
- **Then** it returns one `error` naming `maybe`.

### **AC-7** A stage outside the Work's pipeline is a warning

#### A stage that the Work's actions do not list

- **Given** R with `Wio-Stage: integration`.
- **When** `validate_record` runs.
- **Then** it returns one `warning` naming `integration` and no `error`.

#### An action that the Work does not have

- **Given** a record of `k3m9xq` with `Wio-Action: define`, which the config has
  and `k3m9xq` lacks.
- **When** `validate_record` runs.
- **Then** it returns one `warning` naming `define` and no `error`.

### **AC-8** The place follows the record

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

#### Each diagnostic points at its own field

- **Given** R with `Wio-Stage: integration` on line 5 and `Wio-Items: AC-99` on
  line 6.
- **When** `validate_record` runs.
- **Then** the `error` for `AC-99` has `where` `6` and the `warning` for
  `integration` has `where` `5`.

### **AC-9** The diagnostics come in the order of the fields

#### A record with two errors

- **Given** R with `Wio-Action: nosuch`, `Wio-Stage: nosuch` and
  `Wio-Items: AC-99`, in that order of fields.
- **When** `validate_record` runs.
- **Then** it returns the `error` for the action, then the one for the stage,
  then the one for `AC-99`.

#### A list of Works

- **Given** R with `Wio-Work: b8c9d0, a7b2c4` and `Wio-Items: AC-3`, where both
  lack `AC-3` and their `deliver` lists `architecture`.
- **When** `validate_record` runs.
- **Then** it returns the `error` for `b8c9d0` and then the one for `a7b2c4`.

#### A warning before an error

- **Given** R with `Wio-Stage: integration` and `Wio-Items: AC-99`.
- **When** `validate_record` runs.
- **Then** it returns the `warning` for the stage, then the `error` for
  `AC-99`.

#### An absent field at its place

- **Given** R with the stage `architecture-review`, `Wio-Items: AC-99` and no
  `Wio-Result`.
- **When** `validate_record` runs.
- **Then** it returns the `error` for `AC-99` and then `result required`.
