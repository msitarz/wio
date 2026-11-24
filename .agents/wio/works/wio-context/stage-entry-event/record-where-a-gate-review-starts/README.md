<!-- wio
id = "sw1pa9"
template = "feature.leaf"
roots = ["wio"]
depends_on = ["fy51ae"]
-->

# Record where a gate review starts

## Purpose

A gate's review judges a commit, and `wio trailers --result` can warn that it
judged another only if the session recorded the commit it started from and
whether the tree had uncommitted changes.

## Goals

- A gate's event holds the commit the review starts from.
- A gate's event holds whether the tree had uncommitted changes.
- The commit is found by the rule that `wio trailers` uses for the reviewed
  commit.

## Non-Goals

- Comparing the start with the reviewed commit, which `wio trailers --result`
  does.
- The fields of the event that every stage has, which the sibling records.

## Assumptions

### A-1

The reviewed-commit finder `reviewed_commit` of `wio.trailers` can be shared by
changing only who may call it, so that the two commands cannot find different
commits.

### A-2

Whether the tree has uncommitted changes is available through the `Repository`
port of `wio.io`, as it is for `wio trailers --result`.

## Mechanisms

- **`reviewed_commit`** — in `wio.trailers`, which finds the first commit from
  `HEAD` down that is not a pure gate commit of this gate's action and stage.
- **The reviewed-commit port** — in `src/wio/context/ports.pyi`, provisional,
  which `wio.cli` wires to that finder.
- **The `Repository` and `History` ports** — in `wio.io`.

## Acceptance criteria

### **AC-1** A gate records the commit its review starts from

The event of a gate stage holds the commit that is the first one from `HEAD`
down that is not a pure gate commit of this gate.

#### Under two gate commits

- **Given** a history whose newest two commits are the records of this gate and
  below them a commit of another stage.
- **When** `wio context` runs for the gate.
- **Then** the event's `start` is the commit of the other stage.

### **AC-2** A gate records whether the tree is dirty

The event holds `dirty` true when the tree has uncommitted changes and false
otherwise.

#### Clean and dirty

- **Given** a clean tree and a tree with an uncommitted change.
- **When** `wio context` runs for the gate in each.
- **Then** the first event holds `dirty` false and the second `dirty` true.

### **AC-3** A history with nothing to review records no start

When every commit is a gate commit or there is none, the event holds no start
and the run goes on.

#### An empty history

- **Given** a repository with no commit.
- **When** `wio context` runs for a gate.
- **Then** the event's `start` is absent, `dirty` is recorded, and the exit code
  is 0.
