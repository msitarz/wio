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
- Every lowercase `.jsonl` file of a log is found from its location, in a fixed
  order.
- Finding the location creates nothing.

## Non-Goals

- Writing or reading an event; the sink and `show` do that.
- Creating the directory, which the first write does.
- Moving a log when a clone moves, or removing the log of a clone that is gone.

## Assumptions

### A-1

The path that `Repository.identity()` returns contains no symlink and is spelled
the same by every worktree of one clone, because git prints the real path of its
common directory, so a symlinked checkout and its target are one clone.

## Mechanisms

- **`log_directory(identity: Path, home: Path) -> Path`** — in `wio.log`, gives
  `home / "log" / f"{name}-{digest}"`.
- **The digest** — the first 12 lowercase hexadecimal characters of the SHA-256
  of the identity's path as the file system encodes it (`os.fsencode`), which is
  all that identifies the clone.
- **The name** — for a person and not for identity: take the last component
  of the identity, or the one before it when that is `.git`, strip a trailing
  `.git` from it, and slug it; the component before `/.git` is the root, which
  has an empty name, so the slug is `repo`.
- **The slug** — lowercase, each run of characters outside `a-z0-9` replaced by
  one `-`, cut to 40 characters, then trimmed of `-` at both ends, and `repo`
  when nothing is left.
- **`locate_log(repository: Repository, directories: Directories) -> Path`** —
  in `wio.log`, gives `log_directory(repository.identity(),
  directories.wio_home())`, and raises what either port raises.
- **`EVENTS_FILE = "events.jsonl"`** — the one file the sink appends to.
- **`log_files(directory: Path, filesystem: FileSystem) -> Sequence[Path]`** —
  the entries of the directory whose name ends in a lowercase `.jsonl` and
  that `FileSystem.is_file` accepts, which follows a symlink to a file, in the
  order that `FileSystem.list_dir` gives. It gives an empty sequence when the
  directory does not exist, and raises the `NotADirectoryError` of the port when
  the path is a file.

## Acceptance criteria

### **AC-1** Worktrees of one clone share a location and clones do not

#### Two clones

- **Given** the identities `/w/app/.git` and `/w/other/.git`, and the home `/h`.
- **When** `log_directory` runs for each.
- **Then** they give `/h/log/app-6f8609bd196b` and
  `/h/log/other-58e6d3787679`.

#### Worktrees of one clone

- **Given** a real clone with a commit, a worktree of it made with `git worktree
  add`, and an empty `$WIO_HOME`.
- **When** `locate_log` runs with the `Repository` of git and the real
  `Directories`, once with the main checkout as the working directory and once
  with the worktree.
- **Then** both give the same path.

#### The same clone under two homes

- **Given** the identity `/w/app/.git` and the homes `/h1` and `/h2`.
- **When** `log_directory` runs for each.
- **Then** the results are `/h1/log/app-6f8609bd196b` and
  `/h2/log/app-6f8609bd196b`.

### **AC-2** The name tells a person which repository it is

#### Names of a clone

- **Given** the identities `/Users/x/Code/My App/.git`, `/srv/git/app.git`,
  `/w/.git`, `/w/日本/.git` and `/.git`, each with the home `/h`.
- **When** `log_directory` runs for each.
- **Then** the last components start with `my-app-`, `app-`, `w-`, `repo-` and
  `repo-`, and each ends in 12 lowercase hexadecimal characters.

#### A long name

- **Given** the identity
  `/w/aaaaaaaaa-aaaaaaaaa-aaaaaaaaa-aaaaaaaaa-aaaaaaaaa-aaaaaaaaa/.git`, whose
  repository name has 59 characters and a `-` as its 40th.
- **When** `log_directory` runs for it.
- **Then** the name is `aaaaaaaaa-aaaaaaaaa-aaaaaaaaa-aaaaaaaaa`, which is the
  first 40 characters without the `-` that ends them.

#### The digest decides the identity

- **Given** the identities `/a/b/app/.git` and `/a/c/app/.git`.
- **When** `log_directory` runs for each.
- **Then** both names start with `app-`, and the digests differ.

### **AC-3** The files of a log are found in a fixed order

#### A directory with several files

- **Given** a directory that holds `events.jsonl`, `a.jsonl`, `notes.txt`,
  `B.JSONL` and a directory named `c.jsonl`.
- **When** `log_files` runs for it.
- **Then** it gives `a.jsonl` and `events.jsonl`, in that order.

#### The file the sink appends to

- **Given** a directory that holds `events.jsonl`.
- **When** `log_files` runs for it.
- **Then** the result holds `EVENTS_FILE`, whose value is `events.jsonl`.

#### A directory that is not there

- **Given** a directory that does not exist.
- **When** `log_files` runs for it.
- **Then** it gives no file and creates nothing.

#### A path that is a file

- **Given** a path that is a file.
- **When** `log_files` runs for it.
- **Then** the `NotADirectoryError` of the port is raised unchanged.

#### A symlink to a file

- **Given** a directory that holds `link.jsonl`, a symlink to a file, and
  `dir.jsonl`, a symlink to a directory.
- **When** `log_files` runs for it.
- **Then** it gives `link.jsonl` and not `dir.jsonl`.

### **AC-4** Finding a location creates nothing and fails like the port

#### No directory appears

- **Given** a real clone and an empty `$WIO_HOME`.
- **When** `locate_log` runs with the `Repository` of git and the real
  `Directories`.
- **Then** it gives a path under `$WIO_HOME/log/`, and `$WIO_HOME` still holds
  nothing.

#### Outside a repository

- **Given** a working directory that is not in a repository.
- **When** `locate_log` runs with the `Repository` of git.
- **Then** the `RuntimeError` of the port is raised unchanged, so a caller can
  tell the person what it says.

#### A relative `$WIO_HOME`

- **Given** a real clone and `$WIO_HOME` set to `relative/dir`.
- **When** `locate_log` runs with the `Repository` of git and the real
  `Directories`.
- **Then** the `ValueError` of the port is raised unchanged.
