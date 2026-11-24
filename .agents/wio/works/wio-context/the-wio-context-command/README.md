<!-- wio
id = "b53rss"
template = "feature.leaf"
roots = ["wio"]
depends_on = []
-->

# The wio context command

## Purpose

`wio context` is a component name that nothing provides, so the command has no
place to be described, wired and reached from `wio`, and nothing maps its
failures to exit codes.

## Goals

- `wio context` is listed by `wio --help`, and its usage names the Work, the
  action and the stage.
- The command prints the bundle that the compiler returns to standard output
  and each warning that the compiler reports, and exits 0.
- A mistake that the user must fix exits 2, and a failure that is a bug in wio
  exits 70.
- Describing the command loads nothing but the package's `__init__`, and only a
  run wires the ports.

## Non-Goals

- Compiling the bundle, which the Works under Bundle composition do.
- The option `--output`, the checks of the inputs and the `context` event, which
  their own Works add to this command.

## Assumptions

### A-1

The command follows the pattern of `wio.contracts` and `wio.rules`: a package
that provides `describe()` and a command, and an entry of the table in
`wio.cli`, as `src/wio/cli/README.md` says.

### A-2

The compiler is a collaborator that the other Works provide, so the criteria
here run the command with a fake of it.

## Mechanisms

The names below are provisional, except the command and its three arguments.

- **`wio.context` package** — provides `describe()` and `ContextCommand`, and
  binds its implementation with a `lazy import` so that describing it stays
  light.
- **`Services`** — frozen, what the command reads the project and writes its
  results through, which the Works that add ports extend.
- **The compiler port** — one call that takes the Work's id, the action and the
  stage, and returns the text of the bundle and the warnings found on the way.
- **The entry** — `component_entry("context", wire)` in `wio.cli.table`, whose
  `wire` builds `Services` with the adapters of `wio.io` and `wio.env`.

## Acceptance criteria

### **AC-1** The command is listed and takes a Work, an action and a stage

`wio --help` lists `context` with its one-line description, and
`wio context <work> <action> <stage>` takes the three names in that order.

#### Usage

- **Given** the entry of `context` in the table.
- **When** `wio --help` and `wio context` with no argument run.
- **Then** the first lists `context` with its description, and the second
  prints `usage: wio context [-h] <work> <action> <stage>` on standard error
  and exits 2.

### **AC-2** The bundle goes to standard output and the warnings are reported

Standard output holds the bundle that the compiler returned and nothing else,
each warning is reported as `wio` reports a warning, and the exit code is 0.

#### A bundle with two warnings

- **Given** a fake compiler that returns a text and two warnings.
- **When** `wio context k3m9xq deliver architecture` runs.
- **Then** standard output holds exactly the text, each of the two warnings is
  reported, and the exit code is 0.

### **AC-3** Failures map to exit codes

A `WioError` is written as `error: <message>` with exit 2, and any other
exception is exit 70.

#### Two failures

- **Given** compilers that raise a `WioError` and a `ValueError`.
- **When** the command runs with each.
- **Then** the first prints `error: <message>` on standard error, nothing on
  standard output, and exits 2, and the second exits 70.

### **AC-4** Describing is light and a run wires once

Describing the command imports nothing under `wio.context` but its `__init__`,
and the wiring runs only when the command runs.

#### Import-light

- **Given** the entry of `context` in the table and a `wire` that records its
  calls.
- **When** `wio --help` runs and then `wio context k3m9xq deliver architecture`
  runs.
- **Then** `import_light_violations` of the tests lists no module for the
  entry, `wire` was not called for the help, and it was called once for the run.

## Additional context

- The Works of the checks, of the delivery and of the event depend on this Work
  and add to the command, so none of them builds the shell.
