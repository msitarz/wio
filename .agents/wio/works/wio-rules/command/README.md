<!-- wio
id = "xs3dsj"
template = "feature.leaf"
roots = ["wio"]
depends_on = []
-->

# The wio rules command

## Purpose

`wio rules` is a component name in the table of commands that nothing provides,
so no subcommand of it has a place to be described, wired and reached from
`wio`.

## Goals

- `wio rules` is listed by `wio --help`, and `wio rules` alone prints its
  subcommands, as `wio contracts` does.
- A subcommand of `wio rules` is added by one entry of a table, with its name,
  its help, its arguments and its handler.
- The subcommands share one wiring of what they read the project through, one
  declaration of `--json` and one mapping of failures to exit codes.
- Describing the command loads nothing but the package's `__init__`, and only
  the chosen subcommand is wired.

## Non-Goals

- The subcommands themselves, which `check`, `list`, `new` and `show` build and
  add to the table.
- Any rule logic: reading, selecting and checking rules.

## Assumptions

### A-1

The command follows the pattern of `wio.contracts` and `wio.templates`: a
package that provides `describe()`, a `CommandSpec` and a `Command`, and an
`Entry` of the table in `wio.cli`, as `src/wio/cli/README.md` says.

## Mechanisms

The names of the types and the functions below are provisional, except that the
field set of `Subcommand` is required, because every subcommand Work adds one.

- **`wio.rules` package** — provides `describe()`, `RulesCommand`, `Services`
  and `SUBCOMMANDS`, and binds its implementation with a `lazy import` so that
  describing it stays light.
- **`Services`** — frozen, with `settings: Settings`, `repository: Repository`,
  `files: FileSystem` and `environment: Environment`, what a subcommand reads
  the project through; a subcommand Work that needs another port adds a field.
- **`Subcommand`** — frozen, with `name: str`, `help: str`,
  `configure: Callable[[ArgumentParser], None]` and
  `handler: Callable[[Services, Namespace, Stdio], int]`; the handler returns 0
  or 1 for a failed check, and a mistake the user must fix is a `WioError`.
- **`SUBCOMMANDS`** — the table of `Subcommand`s, which each subcommand Work
  extends.
- **The entry** — `component_entry("rules", wire)` in `wio.cli.table`, whose
  `wire` builds `Services` with the adapters of `wio.io` and `wio.env`.
- **`--json`** — one helper that declares the option for a subcommand.

## Acceptance criteria

### **AC-1** The component is listed and prints its subcommands

`wio --help` lists `rules` with its one-line description, and `wio rules` alone
prints the usage and the subcommands, with exit 0.

#### Usage

- **Given** a table with the subcommands `alpha` and `beta`, each with a help
  line.
- **When** `wio --help` and `wio rules` run.
- **Then** the first lists `rules` with its description, and the second prints
  `usage: wio rules [-h] <subcommand> ...`, lists `alpha` and `beta` with their
  help lines, and exits 0.

### **AC-2** A subcommand is added by one entry

A `Subcommand` in the table is parsed with its arguments and run with the
services, the parsed arguments and the streams, and its return is the exit code.

#### A test subcommand

- **Given** a subcommand `alpha` with the argument `--flag` whose handler
  returns 1 when the flag is set and 0 otherwise.
- **When** `wio rules alpha --flag` and `wio rules alpha` run.
- **Then** the first exits 1 and the second exits 0, and the handler received
  the `Services`, the `Namespace` with `flag` and the `Stdio`.

### **AC-3** Failures map to exit codes

A `WioError` is written as `error: <message>` with exit 2, a `DiagnosticsError`
is written as its lines with exit 2, and any other exception is exit 70.

#### Three failures

- **Given** subcommands whose handlers raise a `WioError`, a `DiagnosticsError`
  with two diagnostics, and a `ValueError`.
- **When** each runs.
- **Then** the first prints `error: <message>` on standard error and exits 2,
  the second prints its two lines on standard error and exits 2, and the third
  exits 70.

### **AC-4** Describing is light and only the chosen subcommand is wired

Describing the command and configuring its subcommands imports nothing under
`wio.rules` but its `__init__`, and the wiring runs only when a subcommand is
chosen.

#### Import-light

- **Given** the entry of `rules` in the table, and a `wire` that records its
  calls.
- **When** `wio --help` runs and then `wio rules alpha` runs.
- **Then** `import_light_violations` of the tests lists no module for the entry,
  `wire` was not called for the help, and it was called once for `alpha`.

### **AC-5** `--json` has one declaration and one behaviour

A subcommand declares `--json` with the shared helper, and with it standard
output holds one JSON document and nothing else on exit 0 or 1, and nothing on
exit 2.

#### The option

- **Given** a subcommand that declares `--json` with the helper and writes one
  object.
- **When** it runs with `--json` and returns 0, 1 and raises a `WioError`.
- **Then** standard output holds exactly one JSON document for the first two,
  and is empty for the third, whose error is on standard error.

## Additional context

- The subcommands `check`, `list`, `new` and `show` depend on this Work and each
  add one entry to `SUBCOMMANDS`, so none of them builds the shell.
