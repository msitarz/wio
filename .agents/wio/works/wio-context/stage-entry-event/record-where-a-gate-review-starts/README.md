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
- A failure to read the start or the flag is a warning that drops only what
  failed, and the event is written without it.

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
`None` as its docstring says. This Work changes `first_parents` so that for the
revision `HEAD`, when `git log` has failed and `HEAD` is a symbolic reference to
a branch that does not exist, which is the case when `git symbolic-ref -q HEAD`
names a branch and `git show-ref --verify --quiet` of that branch exits 1, it
gives an empty sequence; the check runs only after `git log` fails, so the
success path makes no extra call. Every other revision that git rejects, an
option-like one and a `HEAD` that is corrupt included, whether it is detached at
a missing object or names a branch that points at one, so that `show-ref` exits
128, still raises `ValueError`. The docstrings of `src/wio/io/ports.pyi` and
`src/wio/io/adapters.py` and the `wio.io` README state the new case, and C-5 of
the top Work names it as its one exception.

### A-3

`Repository.is_dirty`, as the `wio.io` port declares it, gives true for a
tracked difference or an untracked file that is not ignored, and it works in a
repository with no commit, because it reads `git status`; no caller uses it yet.

### A-4

The check that a review has a reviewed commit is shared by
`wio trailers --result` and `wio log review` through `check_review_event`, so in
a repository with no commit both refuse with the error that the `wio trailers`
README promises, that no reviewed commit was found, and exit 1, where today a
`ValueError` escapes and the exit code is 70; the existing tests are unchanged,
because none uses a repository with no commit.

### A-5

A gate whose history has no start, a history of pure gate commits only or no
commit at all, is recorded with no start, which the concepts do not say, and a
later form of `wio trailers --result` must read an absent start as unknown.

### A-6

The reads of the history and of the repository raise `RuntimeError`,
`ValueError` or `OSError` when they fail, and those are the failures that become
warnings; anything else is a bug in wio and ends the run with exit 70.

## Mechanisms

- **`reviewed_commit`** — in `wio.trailers`, which finds the first commit from
  `HEAD` down that is not a pure gate commit of this gate's action and stage.
- **The reviewed-commit port** — in `src/wio/context/ports.pyi`, provisional,
  which `wio.cli` wires to that finder.
- **`GitHistory.first_parents`** — in `wio.io`, changed as A-2 says.
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

`first_parents("HEAD")` in a repository whose `HEAD` is a reference to a branch
that does not exist gives an empty sequence, and every other revision that git
rejects still raises `ValueError`.

#### The adapter

- **Given** a repository with no commit, one with commits, one whose `HEAD` is
  detached at a missing object, and one whose branch points at a missing object.
- **When** `first_parents` is called with `HEAD` in the first, then with
  `nosuch` and with `--all`, then with `HEAD` in the second, and with `HEAD` in
  the last two.
- **Then** the first call gives an empty sequence, the next two raise
  `ValueError`, the fourth gives the commits newest first as before, and the
  last two raise `ValueError`.

### **AC-5** A review with no reviewed commit is refused by both commands

In a repository with no commit, `wio trailers --result` and `wio log review`
each say that no reviewed commit was found, exit 1 and write no event.

#### An empty repository

- **Given** a repository with no commit and a Work in the working tree.
- **When** `wio trailers <work> define review-contract --result pass` runs, and
  `wio log review <work> define review-contract --result pass` runs.
- **Then** each exits 1 and says that no reviewed commit was found, and no
  `review` event is written.

### **AC-6** A failed read drops only what failed

When the history cannot be read, the event has no `start`; when the repository
cannot be read, it has no `dirty`; each case warns, writes the event, prints the
bundle and exits 0.

#### Each port failing on its own

- **Given** a gate, with a `History` whose reads raise `ValueError` and a
  `Repository` that reads, and the reverse.
- **When** `wio context` runs for each.
- **Then** the first event has no `start` and has `dirty`, the second has
  `start` and no `dirty`, each run reports a warning that names what could not
  be read, prints the bundle and exits 0.
