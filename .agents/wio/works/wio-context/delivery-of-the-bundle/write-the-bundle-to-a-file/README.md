<!-- wio
id = "q6mf05"
template = "feature.leaf"
roots = ["wio"]
depends_on = ["b53rss", "fadef4"]
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
command Work's compiler port says.

### A-2

The key `<repo>` of the default path is the `<name>-<digest>` that names the
clone's log directory, which comes from `Repository.identity()`; `wio.context`
may not import `wio.log`, so the function that makes the key is shared from a
place that both may import, and the place is left to the architecture stage.

## Mechanisms

The names and the places below are provisional, except the paths and the rules
for the temporary directory, which are required.

- **`--output [path]`** — an option of the command that this Work adds, written
  after the three arguments, as in
  `wio context <work> <action> <stage> --output [path]`, or as
  `--output=<path>` anywhere.
- **The default path** — `<tmp>/wio/<repo>/<bundle-id>.md`, where `<tmp>` is the
  temporary directory and `<repo>` is the clone's key of A-2, such as
  `wio-c4555ef0c89d`.
- **`Directories.temp_dir`** — implemented by this Work in `wio.env`: the
  directory `$TMPDIR` names when it is set to a non-empty value, used as it is
  without a test, and otherwise `/tmp` on Linux or `/private/tmp` on macOS when
  a small test file can be written there, and an `OSError` when neither is
  usable.
- **The error** — the delivery turns that `OSError`, and any `OSError` of
  writing the file, into a `WioError` whose message names `$TMPDIR` and
  `--output <path>`.
- **The key of the clone** — the function that `wio.log` uses for the last
  component of a clone's log directory, shared, which gives the slug of the
  clone's directory name and the first 12 hexadecimal digits of the SHA-256 of
  the identity path.

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

A path under the repository root, after it is resolved against the working
directory and its `..` are removed, gets a warning, the default path included.

#### Inside and outside

- **Given** a repository root `/r`, the paths `/r/out.md`, `out.md` run from
  `/r`, `/r/sub/../out.md` and `/elsewhere/out.md`, and `$TMPDIR` set to
  `/r/tmp`.
- **When** the command runs with each path, and with no path.
- **Then** the first three and the default path each report a warning that an
  uncommitted bundle can be committed by mistake, the fourth reports none, and
  every run writes its file and exits 0.

### **AC-4** The temporary directory follows the rule

A non-empty `$TMPDIR` is used as it is, and an empty or unset one is replaced by
`/tmp` on Linux or `/private/tmp` on macOS when a test file can be written
there.

#### Set, empty and unset

- **Given** `$TMPDIR` set to `/tmp/t`, set to the empty text, and unset, on a
  system whose directory can be written.
- **When** `wio.env` gives the temporary directory.
- **Then** it is `/tmp/t` for the first and the system directory for the other
  two.

### **AC-5** An unusable directory or file is an error

When no temporary directory can be used, or the file cannot be written, the
command exits 2, says what to do, writes no bundle on standard output and leaves
no file.

#### Three failures

- **Given** `$TMPDIR` unset and a system directory that cannot be written, a
  `$TMPDIR` that names an unwritable directory, and `--output` given a path that
  is a directory.
- **When** the command runs with each.
- **Then** each exits 2, the first two name `$TMPDIR` and `--output <path>`, the
  third names the path, and standard output holds no bundle.

### **AC-6** A path before the arguments is a usage error

`--output <path>` written before the three arguments takes the first of them as
the path and so fails as a usage error, and `--output=<path>` works anywhere.

#### Two orders

- **Given** the three arguments and a path `b.md`.
- **When** `wio context --output work deliver architecture` runs, and
  `wio context --output=b.md work deliver architecture` runs.
- **Then** the first exits 2 with a usage error and writes nothing, and the
  second writes `b.md`.
