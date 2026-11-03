<!-- wio
id = "sky395"
template = "feature.leaf"
roots = ["wio", "repo"]
depends_on = ["h4my0j"]
-->

# The command line dispatch

## Purpose

`wio.cli.main` ignores its arguments today, so no subcommand can run, report an
error or appear in the usage until `main` dispatches to commands and maps every
outcome to an exit code.

## Goals

- `wio`, `wio --help` and `wio --version` show what wio is, its subcommands and
  its version.
- Only the command that was chosen is wired to adapters and run.
- Every run ends with one of the exit codes of the parent, with its message on
  standard error.
- A subcommand is added with one entry in a table, which a test can replace.

## Non-Goals

- Any real subcommand: the table is empty until the Work of the first component
  adds its entry.
- The platform parameter of the wiring, which the first platform-dependent
  adapter adds.

## Assumptions

- **A-1**: `argparse` on Python 3.15 prints a usage error to standard error and
  raises `SystemExit(2)`, and `--help` and `--version` print to standard output
  and raise `SystemExit(0)` (checked on 3.15.2 on 2026-11-03).
- **A-2**: Importing a module that uses `lazy import` loads none of the modules
  it imports lazily (checked on 3.15.2 on 2026-11-03).

## Mechanisms

- `argparse` subparsers built from the descriptions of the entries, with
  `SystemExit` caught around parsing.
- `importlib.metadata` for the `Summary` and the version of `work-it-out`.
- `traceback` for the report of a bug.
- `wio.errors.WioError`, caught in `main`.

## Constraints

- The table of commands is a parameter of `main`, so a test passes fake commands
  and the default is the real table.
- The usage lists subcommands sorted by name.

## Acceptance criteria

### **AC-1** Bare `wio` and `--help` introduce the command

Bare `wio` and `wio --help` print the package's `Summary` and the usage, listing
each subcommand with its help text sorted by name, to standard output, and exit
0. The strict `xfail` of the bare scenario in `tests/acceptance/cli` is removed
and the scenario passes in both channels.

```python
def main(
    argv: Sequence[str],
    stdio: Stdio,
    commands: Sequence[Entry] = COMMANDS,
) -> int: ...
```

`main` is required as written. `Entry`, `COMMANDS` and the members of the
protocols below are provisional.

#### Bare, with two commands

- **Given** a table of commands `zeta` and `alpha` with help texts.
- **When** `main([], stdio)` and `main(["--help"], stdio)` run.
- **Then** both return 0 with the same standard output, which holds the
  `Summary`, then `alpha` before `zeta` with their help texts; standard error is
  empty.

### **AC-2** `--version` prints the version

`wio --version` prints `wio` and the version of the `work-it-out` distribution
to standard output and exits 0.

#### The version

- **Given** the synchronized environment.
- **When** `main(["--version"], stdio)` runs.
- **Then** it returns 0, standard output is `wio` and the version in
  `pyproject.toml` and a newline, and standard error is empty.

### **AC-3** Only the chosen command is wired and run

A command's exit code is the run's exit code, and bare `wio`, `--help` and
`--version` wire no command.

```python
@dataclass(frozen=True)
class Entry:
    describe: Callable[[], CommandSpec]
    wire: Callable[[], Command]


class CommandSpec(Protocol):
    name: str
    help: str

    def configure(self, parser: ArgumentParser) -> None: ...


class Command(Protocol):
    def run(self, args: Namespace, stdio: Stdio) -> int: ...
```

#### A command is chosen

- **Given** a table of `ok`, which returns 0, and `no`, which returns 1, each
  with a `wire` that records its call, and `ok` taking `--flag`.
- **When** `main(["ok", "--flag"], stdio)`, `main(["no"], stdio)`, then bare,
  `--help` and `--version` run.
- **Then** the first returns 0 with `--flag` in the arguments `ok` received, the
  second returns 1, only the chosen command's `wire` was called each time, and
  the last three called none.

### **AC-4** A usage mistake exits 2

An unknown subcommand or option exits 2 with `argparse`'s message on standard
error, and `main` raises nothing.

#### An unknown subcommand

- **Given** a table with the command `ok`.
- **When** `main(["nope"], stdio)` and `main(["--nope"], stdio)` run.
- **Then** each returns 2 without raising, standard output is empty and standard
  error names the unknown word.

### **AC-5** A `WioError` exits 2 with its message

An error that a command raises as a `WioError` is reported as `error:` and its
message on standard error, and the run exits 2.

#### A configuration error

- **Given** a command whose `run` raises `ConfigurationError("no config")`.
- **When** `main` runs it.
- **Then** it returns 2, standard error is `error: no config` and a newline, and
  standard output is empty.

### **AC-6** A bug exits 70 with its traceback

An exception that is not a `WioError` is reported with its traceback on standard
error, and the run exits 70.

#### A crashing command

- **Given** a command whose `run` raises `RuntimeError("boom")`.
- **When** `main` runs it.
- **Then** it returns 70, the last line of standard error is
  `RuntimeError: boom`, and standard output is empty.

### **AC-7** The import-light rule can fail

A check over a table of commands fails for an entry whose `describe` loads
modules of its implementation, and passes for an entry that does not, so the
rule has a guard that covers every real entry as it is added.

#### A fixture command

- **Given** two fixture packages under `tests`, one whose `describe` imports its
  implementation module eagerly and one that imports it lazily.
- **When** the check runs over an entry for each, in a fresh interpreter.
- **Then** it fails for the first, naming the implementation module, and passes
  for the second; over the real table it passes.

### **AC-8** The command port is split and documented

`src/wio/cli/ports.pyi` declares `CommandSpec` and `Command` as above, each with
a docstring, and the glossary of `src/wio/cli` defines Command, command spec and
entry in place of its single definition of Command.

### **AC-9** The scope document lists this Work

The order of work in `docs/v0.1-scope.md` names the command line and the errors
module before `wio config`, and its section on the command line matches the exit
codes of the parent.
