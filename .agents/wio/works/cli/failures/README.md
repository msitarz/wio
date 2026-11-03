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

- What the parent's Non-Goals leave out, such as `KeyboardInterrupt` and the
  exceptions that other ports declare.
- Committing a test that proves `tach` or `pyrefly` rejects a violation.

## Mechanisms

- A `try`/`except` in `main` around building the parser, the wiring and the run,
  catching `WioError` first.
- `traceback.print_exc` to the stream of `stdio.stderr` for a bug.
- `contextlib.redirect_stdout` and `redirect_stderr`, as in the dispatch leaf.

## Acceptance criteria

### **AC-1** A `WioError` exits 2 with its message

An error that a command raises as a `WioError` while it is described,
configured, wired or run is reported as `error:` and its message on standard
error, and the run exits 2.

#### A configuration error

- **Given** four commands, whose `describe`, `configure`, `wire` and `run` each
  raise `ConfigurationError("no config")`, each in an entry with the `package`
  `"config"` and injected functions.
- **When** `main([name], stdio)` runs for each.
- **Then** each returns 2, standard error is `error: no config` and a newline,
  and standard output is empty.

### **AC-2** A bug exits 70 with its traceback

An exception that is not a `WioError`, at any of those steps, is reported with
its traceback on standard error and the run exits 70.

#### A crashing command

- **Given** four commands, whose `describe`, `configure`, `wire` and `run` each
  raise `RuntimeError("boom")`.
- **When** `main([name], stdio)` runs for each.
- **Then** each returns 70, standard output is empty, and the last line of
  standard error is `RuntimeError: boom`.

### **AC-3** An exit code outside 0 and 1 is a bug

A `run` that returns a code other than 0 or 1 is reported on standard error,
naming the command and the code, and the run exits 70.

#### A wrong code

- **Given** a command whose `run` returns 3.
- **When** `main` runs it.
- **Then** it returns 70, standard output is empty, and standard error names the
  command and the code 3.

### **AC-4** The core writes only to `stdio`

`main` leaves the process's own streams alone, including when `argparse` prints
and when a command fails.

#### Help, mistakes and failures

- **Given** in-memory `stdio` and the process's `sys.stdout` and `sys.stderr`
  captured.
- **When** `main(["--help"], stdio)`, `main(["--version"], stdio)`,
  `main(["nope"], stdio)` and a run of each of three commands run, one raising a
  `WioError`, one raising `RuntimeError` and one returning 3.
- **Then** the process's streams hold nothing, and the output is in `stdio`.

### **AC-5** The documents state the exit codes and the structure

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
