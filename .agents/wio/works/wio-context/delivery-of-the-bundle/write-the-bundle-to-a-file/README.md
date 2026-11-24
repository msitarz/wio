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
- A path inside the worktree gets a warning.
- A temporary directory that cannot be used is an error that says what to do.

## Non-Goals

- Choosing the temporary directory, which `wio.env` does.
- Deleting the file, which the session or the system does.

## Assumptions

### A-1

The temporary directory is the one that `Directories` of `wio.env` gives:
`$TMPDIR` when it is set to a non-empty value, used as it is, and otherwise
`/tmp` on Linux or `/private/tmp` on macOS when a small test file can be written
there.

## Mechanisms

- **`--output [path]`** — an option of the command that this Work adds.
- **The default path** — `wio/<repo>/<bundle-id>.md` in the temporary directory,
  where `<repo>` names the repository.
- **`Directories`** — in `wio.env`, which gives the temporary directory.

## Acceptance criteria

### **AC-1** The default path is in the temporary directory

`--output` without a path writes `wio/<repo>/<bundle-id>.md` in the temporary
directory, prints that path and nothing else on standard output, and the file
holds the bundle.

#### A set `$TMPDIR`

- **Given** `$TMPDIR` set to a directory and a bundle with the id
  `4f3a9c01b2d7`.
- **When** `wio context <work> <action> <stage> --output` runs.
- **Then** standard output is the path `<tmp>/wio/<repo>/4f3a9c01b2d7.md`, and
  the file holds the bundle.

### **AC-2** A given path is used as it is

`--output <path>` writes the bundle at that path and prints it, and a path
inside the worktree gets a warning.

#### Inside and outside the worktree

- **Given** a path outside the worktree and a path inside it.
- **When** the command runs with each.
- **Then** each writes the bundle at its path and prints the path, and the
  second also reports a warning that an uncommitted bundle can be committed by
  mistake.

### **AC-3** A temporary directory that cannot be used is an error

When `$TMPDIR` is unset and the system directory cannot be written, the command
exits 2 and says to set `$TMPDIR` or to pass a path, and it writes no bundle.

#### No usable directory

- **Given** `$TMPDIR` unset and a system directory that cannot be written.
- **When** `wio context <work> <action> <stage> --output` runs.
- **Then** it exits 2, the message names `$TMPDIR` and `--output <path>`, and no
  file is written.
