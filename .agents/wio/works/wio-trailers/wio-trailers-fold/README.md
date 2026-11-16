<!-- wio
id = "x4vs3k"
template = "feature.leaf"
roots = ["wio"]
depends_on = []
-->

# wio trailers fold

## Purpose

A squash merge keeps only a pull request's body, so the records of its commits
must be copied there, folded to what a reader needs, by the engine and not by a
script outside it.

## Goals

- The records of a range of commits are folded into the paragraphs a pull
  request body needs.
- A pull request body ends with those paragraphs, and is left alone when it
  already does.
- Work that a commit reverted leaves no record, and a revert of work outside the
  range stays visible.

## Non-Goals

- Checking the records it folds; the check commands do that, and fold assumes
  the range was accepted.
- Editing the pull request or calling CI; the adopt leaf wires the command in.

## Assumptions

### A-1

The records of a commit are read with the reader that the config names, and the
commits of the range are those from the oldest to the newest, in the order of
the history.

## Mechanisms

- **`wio trailers fold block`** — prints the folded paragraphs for a range.
- **`wio trailers fold body`** — reads a pull request body on standard input and
  prints it with the folded paragraphs at its end, or nothing when it already
  ends with them.
- **`History` port** — gives the commits of the range with their messages.
- **Record parser and renderer** — the shared parser and renderer of `Wio-*`
  records.

## Acceptance criteria

### **AC-1** Consecutive records of one Work and stage become one

#### Two commits of one stage

- **Given** two consecutive commits whose records are for Work `a`, action
  `deliver` and stage `implementation`, the first with items `AC-1` and result
  `fail`, the second with items `AC-2` and result `pass`.
- **When** `wio trailers fold block` runs on the range.
- **Then** it prints one record for `a` with items `AC-1, AC-2` and the result
  `pass`.

### **AC-2** Neighbors that differ only in the Work become one list

#### The same record for two Works

- **Given** consecutive commits whose records for Works `a` and `b` have the
  same action, stage, items, result and judge.
- **When** `wio trailers fold block` runs on the range.
- **Then** it prints one record whose `Wio-Work` is `a, b`.

### **AC-3** A record between two others keeps them apart

#### A re-delivered child after its parent's integration

- **Given** a range whose records are, in order, child `a` delivering
  `implementation`, parent `p` integrating, and `a` delivering `implementation`
  again.
- **When** `wio trailers fold block` runs on the range.
- **Then** it prints three records in that order.

### **AC-4** Reverted work leaves no record

#### A commit reverted in the range

- **Given** a commit with a record and a later commit in the range that reverts
  it.
- **When** `wio trailers fold block` runs on the range.
- **Then** the record of the reverted commit is not printed.

#### A revert of a revert

- **Given** a commit with a record, a revert of it, and a revert of that revert,
  all in the range.
- **When** `wio trailers fold block` runs on the range.
- **Then** the record of the first commit is printed.

### **AC-5** A revert of work outside the range stays visible

#### A revert of an earlier commit

- **Given** a commit in the range that reverts a commit outside it.
- **When** `wio trailers fold body` runs on a body and the range.
- **Then** the printed body has a `This reverts commit <sha>.` line before the
  records.

### **AC-6** The body ends with the folded records

#### A body without them

- **Given** a body of prose and a range with records.
- **When** `wio trailers fold body` runs on the body and the range.
- **Then** it prints the prose, a blank line and the folded records, and the
  prose is unchanged.

#### A body that ends with older records

- **Given** a body that already ends with records of the range's earlier state.
- **When** `wio trailers fold body` runs on it.
- **Then** the printed body ends with the current folded records and holds the
  older ones no longer.

### **AC-7** A body that already has them is left alone

#### Folding twice

- **Given** the body that `wio trailers fold body` printed for a range.
- **When** `wio trailers fold body` runs on that body and the same range.
- **Then** it prints nothing.
