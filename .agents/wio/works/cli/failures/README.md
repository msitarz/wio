<!-- wio
id = "5rzmp0"
template = "feature.leaf"
roots = ["wio", "repo"]
depends_on = ["sky395", "h4my0j"]
-->

# Failures on the command line

## Purpose

A run that goes wrong must end with the right exit code and a message on
standard error, whichever step failed, so that every component can raise its
errors knowing how the command line reports them.

## Goals

- A `WioError` at any step of a run exits 2 with its message.
- Any other failure exits 70 with its traceback, a command's exit code outside
  0 and 1 included.
- The core writes only to the streams it is given.
- The documents state the four exit codes and the new structure of the command
  line.

## Non-Goals

- Handling `KeyboardInterrupt`, or a `SystemExit` that a command raises: they
  propagate.
- Deciding whether the exceptions that other ports declare (`ValueError`,
  `RuntimeError` for a directory outside a git repository, `OSError`,
  `UnicodeDecodeError`) become `WioError`s: the Work of each component maps its
  own.
- Committing a test that proves `tach` or `pyrefly` rejects a violation.

## Assumptions

- **A-1**: A `describe` or a `configure` runs for every entry on every run, so
  an exception from one of them breaks every run until it is fixed.

## Mechanisms

- A `try`/`except` in `main` around building the parser, the wiring and the run,
  catching `WioError` first.
- `traceback.print_exc` to the stream of `stdio.stderr` for a bug.
- `contextlib.redirect_stdout` and `redirect_stderr`, as in the dispatch leaf.

## Constraints

- `describe` and `configure` do no I/O and raise nothing in a working
  installation, because they run on every invocation. The architecture review
  verifies it, and the import-light check of the command-table leaf covers
  their imports.

## Acceptance criteria

### **AC-1** A `WioError` exits 2 with its message

An error that a command raises as a `WioError` while it is described,
configured, wired or run is reported as `error:` and its message on standard
error, and the run exits 2.

#### A configuration error

- **Given** four commands, whose `describe`, `configure`, `wire` and `run` each
  raise `ConfigurationError("no config")`.
- **When** `main` runs each.
- **Then** each returns 2, standard error is `error: no config` and a newline,
  and standard output is empty.

### **AC-2** A bug exits 70

An exception that is not a `WioError`, at any of those steps, is reported with
its traceback on standard error and exits 70, and so does a `run` that returns a
code other than 0 or 1, with a message naming the command and the code.

#### A crashing command

- **Given** commands whose `describe`, `wire` and `run` each raise
  `RuntimeError("boom")`, and one whose `run` returns 3.
- **When** `main` runs each.
- **Then** each returns 70 with standard output empty, the last line of
  standard error is `RuntimeError: boom` for the first three, and standard error
  for the last names the command and the code 3.

### **AC-3** The core writes only to `stdio`

`main` leaves the process's own streams alone, including when `argparse` prints
and when a command fails.

#### Help, mistakes and failures

- **Given** in-memory `stdio` and the process's `sys.stdout` and `sys.stderr`
  captured.
- **When** `main(["--help"], stdio)`, `main(["--version"], stdio)`,
  `main(["nope"], stdio)` and a run of a command that raises a `WioError` run.
- **Then** the process's streams hold nothing, and the output is in `stdio`.

### **AC-4** The documents state the exit codes and the structure

The order of work in `docs/v0.1-scope.md` names the errors module and the
command line before `wio config`, and its overview lists `wio.errors` among the
internal packages. That document, `tests/README.md` and the docstrings of `main`
and `Command.run` state the four exit codes where they stated three.
`src/wio/GLOSSARY.md` lists `errors` among the packages that are not components,
and `tests/README.md` no longer says the `cli` scenarios wait for the package to
grow.

## Additional context

- [v0.1 scope](../../../../../docs/v0.1-scope.md) states the exit-code contract
  that this leaf makes four codes.
