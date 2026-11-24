<!-- wio
id = "q6mf05"
template = "feature.leaf"
roots = ["wio"]
depends_on = ["b53rss"]
-->

# Write the bundle to a file

## Purpose

A harness may cut a bundle that is printed, so a session must be able to ask for
a file that holds it and be told where the file is.

## Goals

- `--output` without a path writes the bundle to a file in the temporary
  directory and prints its path.
- `--output <path>` writes the bundle where it is told.
- The file holds exactly the bundle's text, replaces a file already there, and
  has its parent directories created, and standard output holds only the path
  and a newline.
- A path inside the worktree gets a warning.
- The temporary directory is found as the concepts say.
- A temporary directory that cannot be used, and a file that cannot be written,
  are errors that say what to do, with exit 2 and no bundle on standard output.

## Non-Goals

- Deleting the file, which the session or the system does.
- Compiling the bundle, which the composition does.

## Assumptions

### A-1

The compiler result carries the bundle id that names the default file, as the
command Work's compiler port says, and the id names the header and the body, so
two runs that give the same id give the same file apart from its metadata line.

### A-2

The key `<repo>` of the default path is the `<name>-<digest>` that names the
clone's log directory, which comes from `Repository.identity()`; `wio.context`
may not import `wio.log`, so a function that gives that key is extracted from
`log_directory` of `wio.log`, reused unchanged, and moved to a place that both
may import, left to the architecture stage, and this Work changes `wio.log` by
that move only, with its tests unchanged.

### A-3

The concepts' `--output <path>` is read as `--output <path>` or
`--output=<path>`, with the three arguments before it or the form with `=`
anywhere, because a bare `--output` takes the next word as its path.

## Mechanisms

The names and the places below are provisional. The option and its forms, the
default path, the rules for the temporary directory and the errors' naming are
required.

- **`--output [path]`** — an option of the command that this Work adds. A bare
  `--output` before the three arguments takes the first of them as its path, so
  `wio context --output <work> <action> <stage>` fails as a usage error for want
  of the stage. An empty path, `--output=`, is a usage error, a repeated option
  keeps the last, so `--output=x --output` is a bare one, a leading `~` is not
  expanded, and a relative path is relative to the working directory.
- **The default path** — `<tmp>/wio/<repo>/<bundle-id>.md`, as
  [the concepts](../../../../../../docs/concepts.md#11-the-context-compiler)
  give it, where `<tmp>` is the temporary directory and `<repo>` is the clone's
  key of A-2, such as `wio-c4555ef0c89d`.
- **`Directories.temp_dir`** — implemented by this Work in `wio.env`, by the
  rule of the concepts: `$TMPDIR` when it is set to a non-empty value, used as
  it is, also when it is relative and also when it does not exist, without a
  test, and otherwise the system directory of the platform, `/private/tmp` on
  macOS or `/tmp` elsewhere, which is usable when a small test file can be
  created in it and removed, and any `OSError` means that it is not, and then
  the call raises an `OSError`. The adapter takes the platform's name and the
  two system directories as inputs of its wiring, which is the platform
  parameter that the `wio.env` README anticipates, so that a test points them at
  a scratch directory.
- **The real path** — `resolve(path) -> Path` added to the `FileSystem` port of
  `wio.io` by this Work: the absolute path with its symbolic links followed, for
  a path that need not exist.
- **The errors** — the delivery turns the `OSError` of `temp_dir`, and any
  `OSError` of writing the file, into a `WioError`: for no usable temporary
  directory it names `$TMPDIR` and `--output <path>`, for a failure to write the
  default file it names the file, `$TMPDIR` and `--output <path>`, and for a
  failure to write a given path it names the path alone.
- **The writes** — the test file of `temp_dir` and the directories created under
  `<tmp>` are the writes that this Work adds to the bundle's own, and they are
  outside the worktree unless `$TMPDIR` is inside it.

## Acceptance criteria

### **AC-1** The default path is in the temporary directory

`--output` without a path writes `<tmp>/wio/<repo>/<bundle-id>.md`, prints that
path and a newline and nothing else, and the file holds the bundle's text.

#### A set `$TMPDIR`

- **Given** `$TMPDIR` set to `/tmp/t`, a clone whose identity is
  `/home/u/src/wio/.git`, and a bundle with the id `4f3a9c01b2d7`.
- **When** `wio context <work> <action> <stage> --output` runs.
- **Then** standard output is `/tmp/t/wio/wio-c4555ef0c89d/4f3a9c01b2d7.md` and
  a newline, the file holds the bundle's text, and the bundle is not on standard
  output.

### **AC-2** A given path is used as it is

`--output <path>` writes the bundle at that path, prints the path as it was
given and a newline, replaces a file that is there, and creates the parent
directories.

#### A new path, and an existing file

- **Given** a path `out/b.md` whose directory does not exist, and a file at
  another path that holds other text.
- **When** the command runs with each.
- **Then** each file holds the bundle's text and nothing of the old text, each
  printed path is the one given, and the first directory was created.

### **AC-3** A path inside the worktree is warned about

A path under the repository root, once it is resolved to a real path, which need
not exist, gets a warning, the default path included.

#### Inside and outside

- **Given** a repository whose root is the real path `/r`, the paths
  `/r/out.md`, `out.md` run from `/r`, `/r/sub/../out.md`, a link
  `/elsewhere/link.md` to `/r/out.md`, and `/elsewhere/out.md`, and `$TMPDIR`
  set to `/r/tmp`.
- **When** the command runs with each path, and with no path.
- **Then** the first four and the default path each report a warning that an
  uncommitted bundle can be committed by mistake, the last path reports none,
  and every run writes its file and exits 0.

### **AC-4** The temporary directory follows the rule

A non-empty `$TMPDIR` is used as it is, and an empty or unset one is replaced by
the system directory of the platform when a test file can be created and removed
there.

#### Set, empty and unset, on two platforms

- **Given** `$TMPDIR` set to `/tmp/t`, set to the empty text, and unset, and the
  platform names `darwin` and `linux` with scratch directories standing for
  `/private/tmp` and `/tmp`.
- **When** `wio.env` gives the temporary directory.
- **Then** it is `/tmp/t` for the first, and for the other two it is the scratch
  directory of the platform, and the test file is gone.

### **AC-5** An unusable directory or file is an error

When no temporary directory can be used, or the file cannot be written, the
command exits 2, says what to do, and writes no bundle on standard output and no
file.

#### Four failures

- **Given** `$TMPDIR` unset and a system directory that cannot be written, a
  `$TMPDIR` that names an unwritable directory, and `--output` given a path that
  is a directory, and `--output=` with no path.
- **When** the command runs with each.
- **Then** the first exits 2 and names `$TMPDIR` and `--output <path>`, the
  second exits 2 and names the file, `$TMPDIR` and `--output <path>`, the third
  exits 2 and names the path alone, and the fourth is a usage error, and none
  writes a file or a bundle on standard output.

### **AC-6** A bare `--output` before the arguments is a usage error

A bare `--output` written before the three arguments takes the first of them as
its path and so fails as a usage error, while a path after it, or the form with
`=`, works.

#### Three orders

- **Given** the three arguments and a path `b.md`.
- **When** `wio context --output work deliver architecture` runs, then
  `wio context --output b.md work deliver architecture`, then
  `wio context --output=b.md work deliver architecture`.
- **Then** the first exits 2 with a usage error and writes nothing, and the
  other two write `b.md`.

### **AC-7** The details of the option and the directory

A repeated option keeps the last, a leading `~` is not expanded, and a relative
or a missing `$TMPDIR` is used as it is.

#### Four details

- **Given** the three arguments.
- **When** `wio context ... --output=x.md --output` runs, then
  `... --output ~/b.md`, then with `$TMPDIR` set to `rel/tmp`, and then with
  `$TMPDIR` set to a directory that does not exist.
- **Then** the first writes the default path, the second writes `~/b.md` under
  the working directory, the third writes under `rel/tmp` relative to the
  working directory, and the fourth creates the missing directory under it.
