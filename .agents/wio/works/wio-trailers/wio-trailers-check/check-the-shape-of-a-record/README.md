<!-- wio
id = "pnf585"
template = "feature.leaf"
roots = ["wio"]
depends_on = []
-->

# Check the shape of a record

## Purpose

Both modes of `wio trailers check` need the same judgment of a record's own
form and of the lines a reader cannot see, and two copies of it would drift.

## Goals

- Every record of a message is judged for its own form: its keys, the value of
  each key and the ids a list holds.
- A `Wio-` line that the configured reader cannot see is found.
- Each finding says what is wrong and where, and leaves its severity to the
  mode that uses it.

## Non-Goals

- Checking a name or a result against the config, or a Work against the tree;
  the commit-time mode does that.
- Requiring a record, and the subjects that git writes for a merge, a revert or
  a squash; the modes do that.
- Deciding whether a finding fails the check or warns; each mode decides.

## Assumptions

### A-1

A Work id is any value that is not empty, holds no whitespace or comma and is
not `none`, as
[concepts.md](../../../../../../docs/concepts.md#identity-and-location) says of
an id a person writes; the stand-in script's stricter form is loosened.

### A-2

An action, a stage and a result are judged by their form, a lowercase name of
letters, digits and hyphens that starts with a letter or digit, and not by the
config's vocabulary, which the modes check.

## Mechanisms

- **`check_shape(message: str, reader: Literal["scan", "git"]) ->
  list[Finding]`** — the shape check, which reads the records with the
  configured reader and returns the findings in the order of the message.
- **`Finding`** — a kind that is exactly one of `malformed`, `unknown-key` and
  `invisible`, the key it concerns or `None`, the offending line, its 1-based
  line number in the message and a short sentence saying what is wrong. A
  problem of a whole record, such as a missing key, names the first line of the
  record.
- **Record parser** — the shared parser of `wio.formats`, which the shape check
  consumes to read a record.

## Acceptance criteria

The record in the examples below, called R, is the paragraph `Wio-Work:
k3m9xq`, `Wio-Action: deliver` and `Wio-Stage: architecture`.

### **AC-1** A valid message has no findings

#### Valid records of every form

- **Given** messages holding R; R with `Wio-Items: AC-1, AC-3`,
  `Wio-Result: pass` and `Wio-Judge: human`; the record `Wio-Work: none` alone;
  and R with `Wio-Work: k3m9xq, a7b2c4`.
- **When** `check_shape` reads each.
- **Then** it returns no finding for any.

#### No record and an example in a fenced block

- **Given** a message with no record, and one whose only `Wio-` lines are in a
  fenced code block.
- **When** `check_shape` reads each with the `scan` reader.
- **Then** it returns no finding for either.

### **AC-2** The `Wio-Work` value is judged

#### An id that is not valid

- **Given** R with the value `k3 m9xq` in place of `k3m9xq`.
- **When** `check_shape` reads it.
- **Then** it returns one `malformed` finding with the key `Wio-Work` and the
  line that holds the value.

#### A list that is not valid

- **Given** R with the value `none, k3m9xq`, and R with `k3m9xq, k3m9xq`.
- **When** `check_shape` reads each.
- **Then** it returns one `malformed` finding for each, with the key
  `Wio-Work`.

#### A record with no Work

- **Given** a paragraph of `Wio-Action: deliver` and `Wio-Stage: architecture`.
- **When** `check_shape` reads it.
- **Then** it returns one `malformed` finding with the key `Wio-Work` and the
  first line of the paragraph.

### **AC-3** The other keys are judged

#### A key that is missing or that must not appear

- **Given** R without `Wio-Stage`, and `Wio-Work: none` with `Wio-Stage:
  architecture`.
- **When** `check_shape` reads each.
- **Then** it returns one `malformed` finding for each, with the key
  `Wio-Stage`.

#### A key that is repeated

- **Given** R with a second `Wio-Stage: wiring` line.
- **When** `check_shape` reads it.
- **Then** it returns one `malformed` finding with the key `Wio-Stage` and the
  line of the second.

#### A judge without a result

- **Given** R with `Wio-Judge: human` and no `Wio-Result`.
- **When** `check_shape` reads it.
- **Then** it returns one `malformed` finding with the key `Wio-Judge`.

### **AC-4** The values are judged by their form

#### A name, a judge and items of the wrong form

- **Given** R with `Wio-Stage: Bad Stage`, R with `Wio-Result: pass` and
  `Wio-Judge: robot`, and R with `Wio-Items: AC-1,AC-3`.
- **When** `check_shape` reads each.
- **Then** it returns one `malformed` finding for each, with the keys
  `Wio-Stage`, `Wio-Judge` and `Wio-Items`.

### **AC-5** An unknown `Wio-` key is a finding of its own

#### A key the engine does not define

- **Given** R with a `Wio-Criteria: AC-1` line.
- **When** `check_shape` reads it.
- **Then** it returns one `unknown-key` finding with the key `Wio-Criteria` and
  no `malformed` finding.

### **AC-6** A `Wio-` line the reader cannot see is found

#### A line in a paragraph with prose, under `scan`

- **Given** a message whose paragraph holds R and the prose line `Fixes the
  login bug`.
- **When** `check_shape` reads it with the `scan` reader.
- **Then** it returns one `invisible` finding for each `Wio-` line of that
  paragraph.

#### A record outside the last paragraph, under `git`

- **Given** a message of R, then a blank line, then a record for `a7b2c4`.
- **When** `check_shape` reads it with the `git` reader.
- **Then** it returns one `invisible` finding for each `Wio-` line of the first
  record, and none for the last.
