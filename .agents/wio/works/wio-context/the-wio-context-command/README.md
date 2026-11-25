<!-- wio
id = "b53rss"
template = "feature.leaf"
roots = ["wio"]
depends_on = []
-->

# The wio context command

## Purpose

`wio context` is a component name that nothing provides, so the command has no
place to be described, wired and reached from `wio`, and nothing declares its
ports.

## Goals

- `wio context` is listed by `wio --help`, and its usage names the Work, the
  action and the stage.
- The command prints the bundle that the compiler returns to standard output
  and each warning that the compiler reports, and exits 0.
- A mistake that the user must fix exits 2, and a failure that is a bug in wio
  exits 70, as `wio.cli` already maps them, so the command lets them reach it.
- Describing the command loads nothing but the package's `__init__`, and only a
  run wires the ports.

## Non-Goals

- Composing the bundle, which the Works under Bundle composition do, and wiring
  them to the compiler, which the integration stage of
  [wio context](../README.md) does.
- The option `--output`, the checks of the inputs and the `context` event, which
  their own Works add to this command.
- The option `--json`: the command prints raw text for a session to read, so it
  declares none, as `wio trailers` does, which departs from
  `src/wio/cli/README.md` and which the docs stage records.

## Assumptions

### A-1

The command follows the pattern of `wio.contracts` and `wio.rules`: a package
that provides `describe()` and a command, and an entry of the table in
`wio.cli`, as `src/wio/cli/README.md` says.

### A-2

The compiler is a collaborator, so the criteria of the command run it with a
fake of it, and its result carries what the Works
that deliver the bundle need: the text, the bundle id, the size of the body in
UTF-8 bytes as an integer, the qualified code and the `rule_hash` of each
included rule in the order of the bundle, and the warnings.

## Mechanisms

The names and signatures below are provisional, except the command and its
three arguments.

- **`wio.context` package** — provides `describe()` and `ContextCommand`, and
  binds its implementation with a `lazy import` so that describing it stays
  light.
- **`Services`** — frozen, what the command reads the project and writes its
  results through; this Work wires only the shell, with the adapters of `wio.io`
  and `wio.env`, and each Work that adds a port extends `Services` and `wire`
  for it.
- **`CompiledBundle`** — frozen, declared here in `wio.context`: `text: str`,
  `id: str`, `size: int` (the body in UTF-8 bytes) and `rules: Mapping[str,
  str]`, the qualified code of each printed rule mapped to its `rule_hash`, in
  the order printed. It is not the `Bundle` of `wio.models.config`, which holds
  the settings.
- **The composition port** — in `src/wio/context/ports.pyi`, declared here:
  `compose(work_id: str, action: str, stage: str) -> CompiledBundle`;
  [Compose the bundle](../bundle-composition/compose-the-bundle/README.md)
  satisfies it.
- **A check** — `Callable[[str, str, str], Sequence[str]]`, declared here: it
  takes the Work's id, the action and the stage, and returns the text of its
  warnings or raises a `WioError`.
- **The compiler** — provisional: the function
  `compile(work_id: str, action: str, stage: str) -> Compiled` that this Work
  builds, which runs the checks that the Works of Check the inputs add, in the
  order that [Check the inputs](../check-the-inputs/README.md) states, and then
  asks the composition port for the bundle. `Compiled` holds
  `bundle: CompiledBundle` and `warnings: tuple[str, ...]`, those of the checks
  in the order they ran; the Works that deliver the bundle and record the entry
  read the id, the size and the rules from `bundle`.
- **The criteria that need the real composition** — those of the checks that the
  rule selection judges build it in the test from the real adapters, as `wire`
  does, because no production wiring exists before the integration stage of
  [wio context](../README.md).
- **A warning** — one line on standard error that begins `warning: `, which the
  command writes through `Stdio` for the compiler's warnings and for those of
  the Works that deliver the bundle and record the entry. The order is the
  compiler's, the size, the worktree path, and then those of the entry, the
  start, the dirty flag and the event log, which are reported with the entry and
  so not when delivery fails; AC-3 of
  [Delivery of the bundle](../delivery-of-the-bundle/README.md) verifies the
  first three, AC-2 of [Check the inputs](../check-the-inputs/README.md) the
  compiler's, and AC-10 of [wio context](../README.md) the whole order.
- **The modules that a run must not import** — the architecture stage of this
  Work names them for the integration test that C-6 of
  [wio context](../README.md) describes.
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
  prints a usage line that names the Work, the action and the stage on standard
  error and exits 2.

### **AC-2** The bundle goes to standard output and the warnings are reported

Standard output holds the bundle that the compiler returned and nothing else,
each warning is reported as `wio` reports a warning, and the exit code is 0.

#### A bundle with two warnings

- **Given** a fake compiler that returns a text, an id, a body size, two rules
  and two warnings.
- **When** `wio context k3m9xq deliver architecture` runs.
- **Then** standard output holds exactly the text, each of the two warnings is
  a line `warning: <text>` on standard error, and the exit code is 0.

### **AC-3** Failures map to exit codes

A `WioError` is written as `error: <message>` with exit 2, and any other
exception is exit 70.

#### Two failures

- **Given** compilers that raise a `WioError` and a `ValueError`.
- **When** the command runs with each.
- **Then** the first prints `error: <message>` on standard error, nothing on
  standard output, and exits 2, and the second exits 70.

### **AC-4** The compiler runs the checks before it composes

The checks run in order, and the first that raises a `WioError` stops the run
before the composition is asked.

#### A failing check

- **Given** a composition that records its calls, and two checks, the first of
  which raises a `WioError`.
- **When** the compiler runs.
- **Then** the error reaches the caller, and neither the second check nor the
  composition was called.

#### Passing checks

- **Given** a composition that records its calls and returns a bundle, and two
  checks that return one warning each.
- **When** the compiler runs.
- **Then** the composition was called once, and the result holds its bundle and
  the two warnings in the order the checks ran.

### **AC-5** Describing is light and a run wires once

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
