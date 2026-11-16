<!-- wio
id = "chqy1s"
template = "feature.leaf"
roots = ["wio"]
depends_on = []
-->

# Read the history with git

## Purpose

Every `wio trailers` command reads revisions, the staged index or the state of
the working tree through ports, and the git adapters behind them do not exist,
so none of the commands can run on a real repository.

## Goals

- The commits of a range or along first parents are read from git, with their
  ids and messages.
- A file is read as it was at a revision and as it is staged in the index.
- The working tree is reported as dirty or clean.

## Non-Goals

- Deciding what a command does with a commit; the commands do that.
- Finding Works in a tree; the lookup leaf does that on top of these reads.
- Changing a repository; every read leaves it as it was.

## Assumptions

### A-1

Git is installed and on `PATH` wherever wio runs, as the `git` trailer reader
already needs.

## Mechanisms

- **The adapter of the `History` port** — in `wio.io.adapters`, given the
  `Environment` as `GitRepository` is, runs git in the working directory that
  the environment reports and implements `rev_parse`, `history`,
  `first_parents`, `list_files` and `show` of `src/wio/io/ports.pyi`.
- **`Commit`** — the model of `wio.models.commits`, whose stub declares no
  field, to which this leaf adds the `id` and the `message` that every command
  reads.
- **`GitRepository.show_index` and `is_dirty`** — the two members that the
  adapter leaves to the trailers Work, which this leaf implements.

## Acceptance criteria

The examples use a temporary repository with the commits `c1`, `c2` and `c3`
from the oldest, each adding a file with a message of its own, and a branch
`side` that forked from `c1` and was merged into `c3` as a merge commit.

### **AC-1** The commits of a range come oldest first

#### A range, an empty range and a rejected range

- **Given** the repository.
- **When** `history("c1..c3")`, `history("c3..c3")` and `history("nosuch..c3")`
  run.
- **Then** the first returns the commits after `c1` oldest first, parents
  before children, each with its full id and its message, the second returns no
  commit and the third raises `ValueError`.

### **AC-2** First parents come newest first

#### A walk over a merge

- **Given** the repository with the merge commit `c3`.
- **When** `first_parents("HEAD")` runs.
- **Then** it returns `c3` first, and then only the commits along the first
  parent of each, so the commits of `side` are not in it.

### **AC-3** A revision resolves to a full id

#### A name and an unknown name

- **Given** the repository.
- **When** `rev_parse("HEAD")` and `rev_parse("nosuch")` run.
- **Then** the first returns the full id of `c3` and the second raises
  `ValueError`.

### **AC-4** A file is read as it was at a revision

#### The files and the content at a revision

- **Given** the repository, where a file `b.txt` was added by `c2` and deleted
  by `c3`.
- **When** `list_files("c2")`, `show("c2", "b.txt")` and `show("c3", "b.txt")`
  run.
- **Then** the first returns the paths of that tree relative to the root,
  sorted, the second returns the content `b.txt` had and the third returns
  `None`.

### **AC-5** A file is read as it is staged

#### A staged file that differs from the tree and from `HEAD`

- **Given** a file `a.txt` that is staged with one content, changed in the
  working tree and different in `HEAD`, and a file `new.txt` that is not staged.
- **When** `show_index("a.txt")` and `show_index("new.txt")` run.
- **Then** the first returns the staged content and the second returns `None`.

### **AC-6** The working tree is reported as dirty or clean

#### Changes of every kind

- **Given** a clean repository, then in turn a modified tracked file, a staged
  change, an untracked file and an untracked file that is ignored.
- **When** `is_dirty()` runs on each.
- **Then** it returns false for the clean one and for the ignored file, and true
  for the others.

### **AC-7** A directory outside a repository is refused

#### Every member

- **Given** a working directory that is not in a repository.
- **When** each member of the adapter and `show_index` and `is_dirty` run.
- **Then** each raises `RuntimeError` that names the working directory.
