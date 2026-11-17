<!-- wio
id = "chqy1s"
template = "feature.leaf"
roots = ["wio"]
depends_on = []
-->

# Read the history with git

## Purpose

The `wio trailers` commands that check or find records read revisions, the
staged index or the state of the working tree through ports, and the git
adapters behind them do not exist, so none of those commands can run on a real
repository.

## Goals

- The commits of a range or along first parents are read from git, with their
  full ids and their full messages.
- A file is read as it was at a revision and as it is staged in the index.
- The working tree is reported as dirty or clean.

## Non-Goals

- Deciding what a command does with a commit; the commands do that.
- Finding Works in a tree; the lookup leaf does that on top of these reads.
- Changing a repository; every read leaves it as it was, which AC-8 judges.

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
  field, to which this leaf adds `id: str`, the full hash of the commit, and
  `message: str`, the full message as git stores it, subject, body and trailers,
  without its trailing newline.
- **`GitRepository.show_index` and `is_dirty`** — the two members that the
  adapter leaves to the trailers Work, which this leaf implements.

## Acceptance criteria

The examples use a temporary repository. `c1` adds `a.txt` and `sub/d.txt`. A
branch `side` forks from `c1` with one commit `s1` that adds `s.txt`. On the
main branch `c2` adds `b.txt`, and `c3` merges `side` and deletes `b.txt`. Each
commit has a message of its own with a subject, a body and a trailer paragraph.

### **AC-1** The commits of a range come oldest first

#### A range, an empty range and a rejected range

- **Given** the repository.
- **When** `history("c1..c3")`, `history("c3..c3")` and `history("nosuch..c3")`
  run.
- **Then** the first returns `s1` and `c2` in either order and then `c3`, the
  merge included, each with its full 40-character id and its message exactly as
  committed, subject, body and trailer paragraph, without the trailing newline;
  the second returns no commit and the third raises `ValueError`.

### **AC-2** First parents come newest first

#### A walk over a merge

- **Given** the repository with the merge commit `c3`.
- **When** `first_parents("HEAD")` and `first_parents("nosuch")` run.
- **Then** the first returns `c3`, `c2` and `c1` in that order, so `s1` is not
  in it, and the second raises `ValueError`.

### **AC-3** A revision resolves to a full id

#### A name and an unknown name

- **Given** the repository.
- **When** `rev_parse("HEAD")` and `rev_parse("nosuch")` run.
- **Then** the first returns the full id of `c3` and the second raises
  `ValueError`.

### **AC-4** A file is read as it was at a revision

#### The files and the content at a revision

- **Given** the repository, whose `b.txt` was added by `c2` and deleted by
  `c3`.
- **When** `list_files("c2")`, `show("c2", "b.txt")` and `show("c3", "b.txt")`
  run, and then `list_files("c2")` runs again with the working directory set to
  `sub`, and `list_files("nosuch")` and `show("nosuch", "b.txt")` run.
- **Then** the first returns `a.txt`, `b.txt` and `sub/d.txt` sorted, the
  second returns the content `b.txt` had, the third returns `None`, the fourth
  returns the same paths as the first, relative to the root and not to `sub`,
  and the last two raise `ValueError`.

### **AC-5** A file is read as it is staged

#### A staged file that differs from the tree and from `HEAD`

- **Given** a file `a.txt` that is staged with one content, changed in the
  working tree and different in `HEAD`, and a file `new.txt` that is not staged.
- **When** `show_index("a.txt")` and `show_index("new.txt")` run, and then
  `show_index("a.txt")` runs again with the working directory set to `sub`.
- **Then** the first returns the staged content, the second returns `None` and
  the third returns the same content as the first, because the path is relative
  to the root.

### **AC-6** The working tree is reported as dirty or clean

#### Changes of every kind

- **Given** a clean repository, then in turn a modified tracked file, a newly
  added staged file, an untracked file and an untracked file that is ignored.
- **When** `is_dirty()` runs on each.
- **Then** it returns false for the clean one and for the ignored file, and true
  for the others.

### **AC-7** A directory outside a repository is refused

#### Every member

- **Given** a working directory that is not in a repository.
- **When** each member of the adapter and `show_index` and `is_dirty` run.
- **Then** each raises `RuntimeError` that names the working directory.

### **AC-8** A read leaves the repository as it was

#### Every member

- **Given** the repository with a staged file and a modified tracked file.
- **When** every member of the adapter, `show_index` and `is_dirty` run.
- **Then** the bytes of `.git/index`, the refs and the working-tree files are
  the same as before.
