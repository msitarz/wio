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
- A problem of the record's own form, or a record the reader cannot see, is
  refused.

## Non-Goals

- Checking a pull request body or a range of commits; the later check does
  that.
- Writing a record; `wio trailers <work> <action> <stage>` does that.

## Assumptions

### A-1

A finding of the kind `unknown-key` is a warning at commit time, as it is
afterwards, because a `Wio-` key that the engine no longer defines is not a
reason to refuse a commit.

## Mechanisms

- **`wio trailers check --require`** — reads a commit message from a file or
  from standard input, and exits 1 on an error.
- **Shape check** — the findings of the shape leaf, which this mode turns into
  errors and warnings.
- **`History` port** — finds a Work that the commit being made deletes, which is
  in `HEAD` and no longer in the index.

## Acceptance criteria

### **AC-1** Names are checked against the config

#### An action the config does not have

- **Given** a commit message whose record has `Wio-Action: nosuch`.
- **When** `wio trailers check --require` reads it.
- **Then** the command exits 1 and names the action.

#### A stage the config does not have

- **Given** a commit message whose record has `Wio-Stage: nosuch`.
- **When** `wio trailers check --require` reads it.
- **Then** the command exits 1 and names the stage.

### **AC-2** The Works and their items must exist

#### A Work that exists nowhere

- **Given** a record whose `Wio-Work` is in neither the index nor `HEAD`.
- **When** `wio trailers check --require` reads the message.
- **Then** the command exits 1 and names the Work.

#### A Work that the commit deletes

- **Given** a record whose `Wio-Work` is in `HEAD` and not in the index.
- **When** `wio trailers check --require` reads the message.
- **Then** the command exits 0.

#### An item id outside the Work

- **Given** a record that cites `AC-99`, which its Work does not have.
- **When** `wio trailers check --require` reads the message.
- **Then** the command exits 1 and names `AC-99`.

### **AC-3** A result is present exactly on a gate

#### A gate without a result

- **Given** a record of a gate stage with no `Wio-Result`.
- **When** `wio trailers check --require` reads the message.
- **Then** the command exits 1 and reports that a result is required.

#### A result on a stage that is not a gate

- **Given** a record of a stage that is not a gate, with `Wio-Result: pass`.
- **When** `wio trailers check --require` reads the message.
- **Then** the command exits 1 and reports that the stage is not a gate.

### **AC-4** A record is required unless git wrote the subject

#### A message with no record

- **Given** a message with no record and the subject `feat: add x`.
- **When** `wio trailers check --require` reads it.
- **Then** the command exits 1 and reports that no record was found.

#### A merge, revert, reapply, fixup or squash subject

- **Given** messages with no record whose subjects start with `Merge `,
  `Revert `, `Reapply `, `fixup!` and `squash! `.
- **When** `wio trailers check --require` reads each.
- **Then** each command exits 0.

#### An amend subject

- **Given** a message with no record whose subject starts with `amend! `.
- **When** `wio trailers check --require` reads it.
- **Then** the command exits 1 and reports that no record was found.

### **AC-5** The findings of the shape check are judged

#### A malformed or invisible record is an error

- **Given** a message with a `Wio-Work` value that is not a valid id, and
  another with a `Wio-` line the reader cannot see.
- **When** `wio trailers check --require` reads each.
- **Then** each command exits 1 and names the line.

#### An unknown key is a warning

- **Given** a message with a valid record and a `Wio-Criteria` line.
- **When** `wio trailers check --require` reads it.
- **Then** the command exits 0 and warns about `Wio-Criteria`.

### **AC-6** A stage outside the Work's pipeline is a warning

#### A stage that is not in the Work's actions

- **Given** a record whose stage the config has but its Work's actions do not
  list.
- **When** `wio trailers check --require` reads the message.
- **Then** the command exits 0 and warns about the stage.
