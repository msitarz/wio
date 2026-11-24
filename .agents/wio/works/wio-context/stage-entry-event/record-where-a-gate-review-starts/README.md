<!-- wio
id = "sw1pa9"
template = "feature.leaf"
roots = ["wio"]
depends_on = ["fy51ae"]
-->

# Record where a gate review starts

## Purpose

A gate's review judges a commit, and a later form of `wio trailers --result` can
warn that it judged another only if the session recorded the commit it started
from and whether the tree had uncommitted changes.

## Goals

- A gate's event holds the commit the review starts from.
- A gate's event holds whether the tree had uncommitted changes, read before the
  bundle is delivered.
- The commit is found by the rule that `wio trailers` uses for the reviewed
  commit.
- A repository with no commit gives no start, and the run goes on.

## Non-Goals

- Comparing the start with the reviewed commit, and warning about a dirty start,
  which `wio trailers --result` does in a later form.
- The fields of the event that every stage has, which the sibling records.

## Assumptions

### A-1

The finder `reviewed_commit` of `wio.trailers` is reached through a port of
`wio.context`, provisional, in `src/wio/context/ports.pyi`, that `wio.cli` wires
to it and that closes over the history and the reader, because `wio.context` may
not import `wio.trailers`, as A-3 of [wio context](../../README.md) says.

### A-2

`GitHistory.first_parents` raises a `ValueError` for a repository with no commit
today, so `reviewed_commit` does not return `None` there as its docstring says;
this Work changes `GitHistory.first_parents` to give an empty sequence for an
unborn `HEAD`, adds one case to its tests and leaves the others unchanged, which
amends C-5 of the top Work for that one case.

### A-3

`Repository.is_dirty`, as the `wio.io` port declares it, gives true for a
tracked difference or an untracked file that is not ignored, and it works in a
repository with no commit, because it reads `git status`; no caller uses it yet.

## Mechanisms

- **`reviewed_commit`** — in `wio.trailers`, which finds the first commit from
  `HEAD` down that is not a pure gate commit of this gate's action and stage.
- **The reviewed-commit port** — in `src/wio/context/ports.pyi`, provisional,
  which `wio.cli` wires to that finder.
- **The `Repository` and `History` ports** — in `wio.io`; the state is read
  before the bundle is delivered, as the sibling's order of the run says.

## Acceptance criteria

### **AC-1** A gate records the commit its review starts from

The event of a gate stage holds the first commit from `HEAD` down that is not a
pure gate commit of this gate.

#### Under two gate commits

- **Given** a history whose newest two commits are the records of this gate and
  below them a commit of another stage.
- **When** `wio context` runs for the gate.
- **Then** the event's `start` is the commit of the other stage.

#### Commits that are not pure gate commits

- **Given** a history whose newest commit holds a record of another stage beside
  the gate's, and another history whose newest commit has `Wio-Work: none`.
- **When** `wio context` runs for the gate in each.
- **Then** the event's `start` is that newest commit.

### **AC-2** A gate records whether the tree is dirty

The event holds `dirty` true when the tree has uncommitted changes and false
otherwise, read before the bundle is delivered.

#### Clean, dirty, and a bundle written inside the worktree

- **Given** a clean tree, a tree with an uncommitted change, and a clean tree
  with `--output` given a path inside the worktree.
- **When** `wio context` runs for the gate in each.
- **Then** the first event holds `dirty` false, the second `dirty` true, and the
  third `dirty` false, though the bundle's file is then untracked.

### **AC-3** A history with nothing to review records no start

When every commit is a pure gate commit, or there is none, the event holds no
start and the run goes on.

#### Only gate commits, and an empty repository

- **Given** a history of pure gate commits of this gate only, and a repository
  with no commit whose tree is clean and one with an untracked file.
- **When** `wio context` runs for the gate in each.
- **Then** each event has no `start`, the event of the clean empty repository
  has `dirty` false and the other has `dirty` true, and the exit code is 0.
