<!-- wio
id = "x4vs3k"
template = "feature.leaf"
roots = ["wio"]
depends_on = ["pnf585", "chqy1s", "eh62g6"]
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

- Checking the records it folds; the check commands do that.
- Editing the pull request or calling CI; the adopt leaf wires the command in.

## Assumptions

### A-1

The records of a commit are read with the reader that the config names.

### A-2

The range was accepted by `wio trailers check`, so a fold of a malformed record
is not defined.

### A-3

`<range>`, a git revision range such as `main..HEAD`, is the provisional way to
name the commits, as the parent's A-3 says of the other names.

## Mechanisms

- **`wio trailers fold block <range>`** — prints the revert lines of commits
  that revert work outside the range, then the folded records.
- **`wio trailers fold body <range>`** — reads a pull request body on standard
  input and prints it with those paragraphs at its end, or nothing when it
  already ends with them.
- **`History` port** — gives the commits of the range with their messages,
  oldest first.
- **Record parser and renderer** — the shared parser and renderer of `Wio-*`
  records.

## Acceptance criteria

### **AC-1** Consecutive records of one Work and stage become one

#### Two commits of one stage

- **Given** two consecutive commits with no other record between them, whose
  records are for Work `a`, action `deliver` and stage `implementation`, the
  first with items `AC-1` and result `fail`, the second with items `AC-2` and
  result `pass`.
- **When** `wio trailers fold block` runs on the range.
- **Then** it prints one record for `a` with items `AC-1, AC-2` and the result
  `pass`.

### **AC-2** Neighbors that differ only in the Work become one list

#### The same record for two Works

- **Given** consecutive commits whose records for Works `a` and `b` have the
  same action, stage, items, result and judge.
- **When** `wio trailers fold block` runs on the range.
- **Then** it prints one record whose `Wio-Work` is `a, b` and whose other
  fields are those of the two records.

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
- **Then** the record of the reverted commit is not printed, and no record is
  printed for the revert.

#### A revert of a revert

- **Given** a commit with a record, a revert of it, and a revert of that revert,
  all in the range.
- **When** `wio trailers fold block` runs on the range.
- **Then** the record of the first commit is printed.

### **AC-5** A revert of work outside the range stays visible

#### In a body

- **Given** the body `Fix the bug.` and a commit in the range that reverts a
  commit `1234567` outside it.
- **When** `wio trailers fold body <range>` runs on that body.
- **Then** the printed body is `Fix the bug.`, a paragraph
  `This reverts commit 1234567.`, and then the folded records, each as its own
  paragraph.

#### In a block

- **Given** the same range.
- **When** `wio trailers fold block <range>` runs.
- **Then** it prints the paragraph `This reverts commit 1234567.` and then the
  folded records.

### **AC-6** The body ends with the folded records

#### A body without them

- **Given** a body of prose and a range with records.
- **When** `wio trailers fold body` runs on the body and the range.
- **Then** it prints the prose, a blank line and the folded records, and the
  prose is unchanged.

#### A body that ends with older records

- **Given** a body of prose that holds a record paragraph, and that ends with a
  record of the range's earlier state.
- **When** `wio trailers fold body` runs on it.
- **Then** the printed body ends with the current folded records, holds the
  trailing older one no longer, and keeps the record paragraph inside the prose.

### **AC-7** A body that already has them is left alone

#### Folding twice

- **Given** the body that `wio trailers fold body` printed for a range.
- **When** `wio trailers fold body` runs on that body and the same range.
- **Then** it prints nothing.

### **AC-8** A listed or absent Work folds like a single one

#### A record for two Works and a record for none

- **Given** a commit whose record has `Wio-Work: a, b`, and a commit whose
  record has `Wio-Work: none`.
- **When** `wio trailers fold block` runs on the range.
- **Then** the first prints as it would for one record of `a` and then one of
  `b`, in that order, and the second prints nothing.

### **AC-9** A range that does not resolve prints nothing

#### An unknown revision

- **Given** a range whose revision does not exist.
- **When** `wio trailers fold block <range>` and `wio trailers fold body
  <range>` run.
- **Then** each exits 2 and prints nothing.
