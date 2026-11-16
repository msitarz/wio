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

- Every record of a message is judged for its form: its keys, the form of its
  ids, the value of a result and the ids of a list.
- A `Wio-` line that the configured reader cannot see is found.
- Each finding says what is wrong and where, and leaves its severity to the
  mode that uses it.

## Non-Goals

- Checking a name against the config or a Work against the tree; the commit-time
  mode does that.
- Deciding whether a finding fails the check or warns; each mode decides.

## Assumptions

### A-1

The forms of an id, a result and a list are those that
[concepts.md](../../../../../../docs/concepts.md#records) states for a record.

## Mechanisms

- **Shape check** — a function of a message and the configured reader that
  returns findings, each with a kind, the offending line and its position.
- **Configured reader** — `scan` or `git`, which decides what counts as a record
  and what is invisible.

## Acceptance criteria

### **AC-1** A malformed record is found

A record whose own form is wrong yields a finding of the kind `malformed` that
names the key and the line.

#### An id that is not valid

- **Given** a message whose record has a `Wio-Work` value that is not a valid
  id.
- **When** the shape check reads it.
- **Then** it returns one `malformed` finding naming `Wio-Work` and that line.

#### A result outside its form

- **Given** a message whose record has an empty `Wio-Result` value.
- **When** the shape check reads it.
- **Then** it returns one `malformed` finding naming `Wio-Result`.

### **AC-2** An unknown `Wio-` key is a finding of its own

#### A key the engine does not define

- **Given** a message whose record has a `Wio-Criteria` line.
- **When** the shape check reads it.
- **Then** it returns one `unknown-key` finding naming `Wio-Criteria` and no
  `malformed` finding.

### **AC-3** A `Wio-` line the reader cannot see is found

#### A line in a paragraph with prose, under `scan`

- **Given** a message with a `Wio-Work` line in a paragraph that also holds a
  prose line, and the `scan` reader.
- **When** the shape check reads it.
- **Then** it returns one `invisible` finding naming that line.

#### A record outside the last paragraph, under `git`

- **Given** a message with two record paragraphs, and the `git` reader.
- **When** the shape check reads it.
- **Then** it returns one `invisible` finding naming the record that is not in
  the last paragraph.

### **AC-4** A well-formed message has no findings

#### One valid record

- **Given** a message with one record whose fields are all well formed.
- **When** the shape check reads it.
- **Then** it returns no findings.
