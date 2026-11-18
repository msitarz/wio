<!-- wio
id = "jk2yz0"
template = "feature.leaf"
roots = ["wio"]
depends_on = []
-->

# Locate the log

## Purpose

The sink that writes events and the command that reads them must agree on where
a repository's log is, and a place keyed by the working directory would give
each worktree its own log and hide a session's events from the other worktrees
of the same clone; the engine needs one location for each clone.

## Goals

- The log of a repository has one location, shared by every worktree of its
  clone and by no other clone.
- A person who lists the Wio home can tell which repository a log is for.
- The files that hold a log's events are found from its location, whatever they
  are named, in a fixed order.
- Finding the location creates nothing.

## Non-Goals

- Writing or reading an event; the sink and `show` do that.
- Creating the directory, which the first write does.
- Moving a log when a clone moves, or removing the log of a clone that is gone.

## Assumptions

### A-1

The path that `Repository.identity()` returns contains no symlink, because git
prints the real path of its common directory, so a symlinked checkout and its
target are one clone.

## Mechanisms

- **`log_directory(identity: Path, home: Path) -> Path`** — in `wio.log`, gives
  `home / "log" / f"{name}-{digest}"`. `digest` is the first 12 lowercase
  hexadecimal characters of the SHA-256 of the identity's path as UTF-8 text,
  and is all that identifies the clone. `name` is for a person: the slug of the
  last component of the identity, or of the one before it when that is `.git`,
  without a trailing `.git`. A slug is lowercase, with each run of characters
  outside `a-z0-9` replaced by one `-`, no `-` at either end, and at most 40
  characters, and `repo` when nothing is left.
- **`EVENTS_FILE = "events.jsonl"`** — the one file the sink appends to.
- **`log_files(directory: Path, filesystem: FileSystem) -> Sequence[Path]`** —
  the files of the directory whose name ends in `.jsonl`, in order of name, and
  an empty sequence when the directory does not exist.
- **The `Repository` and `Directories` ports** — `Repository.identity()` gives
  the clone and `Directories.wio_home()` the home; neither is called by a
  function that is given their results.

## Acceptance criteria

### **AC-1** Worktrees of one clone share a location and clones do not

#### Two checkouts of one clone, and another clone

- **Given** the identity `/w/app/.git` for the main checkout and for a worktree
  of it, `/w/other/.git` for another clone, and the home `/h`.
- **When** `log_directory` runs for each.
- **Then** the first two give the same path under `/h/log/`, and the third a
  different one.

#### The same clone under two homes

- **Given** the identity `/w/app/.git` and the homes `/h1` and `/h2`.
- **When** `log_directory` runs for each.
- **Then** the last components of the two paths are equal, and they are
  `/h1/log/…` and `/h2/log/…`.

### **AC-2** The name tells a person which repository it is

#### Names of a clone

- **Given** the identities `/Users/x/Code/My App/.git`, `/srv/git/app.git`,
  `/w/.git` and `/w/日本/.git`, each with the home `/h`.
- **When** `log_directory` runs for each.
- **Then** the last components start with `my-app-`, `app-`, `w-` and `repo-`,
  and end in 12 lowercase hexadecimal characters.

#### The digest decides the identity

- **Given** the identities `/a/b/app/.git` and `/a/c/app/.git`.
- **When** `log_directory` runs for each.
- **Then** both names start with `app-`, and the digests differ.

### **AC-3** The files of a log are found in a fixed order

#### A directory with several files

- **Given** a directory that holds `events.jsonl`, `a.jsonl` and `notes.txt`.
- **When** `log_files` runs for it.
- **Then** it gives `a.jsonl` and `events.jsonl`, in that order.

#### A directory that is not there

- **Given** a directory that does not exist.
- **When** `log_files` runs for it.
- **Then** it gives no file and creates nothing.

### **AC-4** Finding a location creates nothing and fails like the port

#### No directory appears

- **Given** a real clone and an empty `$WIO_HOME`.
- **When** the location of its log is found.
- **Then** `$WIO_HOME` still holds nothing.

#### Outside a repository

- **Given** a working directory that is not in a repository.
- **When** the location is found with the `Repository` of git.
- **Then** the `RuntimeError` of the port is raised unchanged, so a caller can
  tell the person what it says.
