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

- A gate's event holds the full id of the commit the review starts from.
- A gate's event holds whether the tree had uncommitted changes, and both are
  read before the bundle is delivered.
- The commit is found by the rule that `wio trailers` uses for the reviewed
  commit.
- A repository with no commit gives no start, and the run goes on.
- A failure to read the start or the flag is a warning, and the event is written
  without them.

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

`GitHistory.first_parents` raises a `ValueError` for every revision that git
rejects, so for a repository with no commit `reviewed_commit` does not return
`None` as its docstring says; this Work changes `first_parents` so that for the
revision `HEAD`, when `HEAD` does not resolve to a commit, it gives an empty
sequence, while every other revision that git rejects, an option-like one
included, still raises `ValueError`, and the docstrings of
`src/wio/io/ports.pyi` and `src/wio/io/adapters.py` and the `wio.io` README
state the new case; this amends C-5 of the top Work for that one case.

### A-3

`Repository.is_dirty`, as the `wio.io` port declares it, gives true for a
tracked difference or an untracked file that is not ignored, and it works in a
repository with no commit, because it reads `git status`; no caller uses it yet.

### A-4

In a repository with no commit, `wio trailers --result` ends with the error that
its README promises, that no reviewed commit was found, where today a
`ValueError` escapes from `reviewed_commit`, and its existing tests are
unchanged.

## Mechanisms

- **`reviewed_commit`** — in `wio.trailers`, which finds the first commit from
  `HEAD` down that is not a pure gate commit of this gate's action and stage.
- **The reviewed-commit port** — in `src/wio/context/ports.pyi`, provisional,
  which `wio.cli` wires to that finder.
- **`GitHistory.first_parents`** — in `wio.io`, changed as A-2 says, with the
  unborn `HEAD` told from a rejected revision by `HEAD` failing to resolve to a
  commit.
- **The `Repository` and `History` ports** — in `wio.io`, read before the bundle
  is delivered, so that a bundle written inside the worktree is not counted.

## Acceptance criteria

### **AC-1** A gate records the commit its review starts from

The event of a gate stage holds the full id of the first commit from `HEAD` down
that is not a pure gate commit of this gate.

#### Under two gate commits

- **Given** a history whose newest two commits are the records of this gate and
  below them a commit of another stage.
- **When** `wio context` runs for the gate.
- **Then** the event's `start` is the full id of the commit of the other stage.

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

- **Given** a history whose commits all carry only this gate's records, with the
  Work's files committed in a commit that carries only this gate's record, and a
  repository with no commit, where the Work's files are untracked.
- **When** `wio context` runs for the gate in each.
- **Then** each event has no `start`, the event of the empty repository has
  `dirty` true, and the exit code is 0.

### **AC-4** An unborn `HEAD` gives an empty history, and nothing else changes

`first_parents("HEAD")` in a repository with no commit gives an empty sequence,
and every other revision that git rejects still raises `ValueError`.

#### The adapter

- **Given** a repository with no commit, and one with commits.
- **When** `first_parents` is called with `HEAD` in the first, then with
  `nosuch` and with `--all`, and with `HEAD` in the second.
- **Then** the first call gives an empty sequence, the next two raise
  `ValueError`, and the last gives the commits newest first as before.

### **AC-5** `wio trailers --result` ends with its promised error in an empty repository

In a repository with no commit, `wio trailers --result` says that no reviewed
commit was found and exits 2, and its other behaviour is unchanged.

#### An empty repository

- **Given** a repository with no commit and a Work in the working tree.
- **When** `wio trailers <work> define review-contract --result pass` runs.
- **Then** it exits 2 and says that no reviewed commit was found.

### **AC-6** A failed read of the start or the flag is a warning

When the commit or the flag cannot be read, the command warns, writes the event
without them, prints the bundle and exits 0.

#### Ports that fail

- **Given** a `History` and a `Repository` whose reads raise, for a gate.
- **When** `wio context` runs.
- **Then** a warning says that the start and the flag could not be read, the
  event has no `start` and no `dirty`, the bundle is printed, and the exit code
  is 0.
