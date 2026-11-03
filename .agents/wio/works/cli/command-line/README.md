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
  standard error, and without writing to the process's own streams.
- A subcommand is added with one entry in a table, whose component names the
  type checker enforces.
- A component's package can be imported to describe its command without loading
  its implementation, and a check says when it cannot.

## Non-Goals

- Any real subcommand: the table is empty until the Work of the first component
  adds its entry.
- The platform parameter of the wiring, which the first platform-dependent
  adapter adds.

## Assumptions

- **A-1**: `argparse` on Python 3.15 prints a usage error to `sys.stderr` and
  raises `SystemExit(2)`, and `--help` and `--version` print to `sys.stdout` and
  raise `SystemExit(0)` (checked on 3.15.2 on 2026-11-03).
- **A-2**: Importing a module that uses `lazy import` loads none of the modules
  it imports lazily (checked on 3.15.2 on 2026-11-03).

## Mechanisms

- `argparse` subparsers built from the descriptions of the entries, with
  `SystemExit` caught around parsing, and `contextlib.redirect_stdout` and
  `redirect_stderr` pointing `argparse`'s output at the streams of `stdio`.
- `importlib.import_module` of `wio.<component>` for each entry, then its
  `describe()`.
- `importlib.metadata` for the `Summary` and the version of `work-it-out`.
- `traceback` for the report of a bug.
- `wio.errors.WioError`, caught in `main`.
- `typing.Literal` for the names of the components.

## Acceptance criteria

### **AC-1** Bare `wio` and `--help` introduce the command

Bare `wio` and `wio --help` print the package's `Summary` and the usage, listing
each subcommand with its help text in order of name, to standard output, and
exit 0. `wio <subcommand> --help` prints that subcommand's help with its
options. The strict `xfail` of the bare scenario in `tests/acceptance/cli` is
removed and the scenario passes in both channels.

```python
def main(
    argv: Sequence[str],
    stdio: Stdio,
    commands: Sequence[Entry] = COMMANDS,
) -> int: ...
```

`main` and the names of `Entry`, `CommandSpec` and `Command` are required, with
the shapes of AC-3 and AC-10. `COMMANDS` and `component_entry` are provisional
names.

#### Bare, with two commands

- **Given** a table of commands `zeta` and `alpha` with help texts.
- **When** `main([], stdio)` and `main(["--help"], stdio)` run.
- **Then** both return 0 with the same standard output, which holds the
  `Summary`, then the help text of `alpha` before that of `zeta`; standard error
  is empty. Only the order and the presence of the texts are checked, not how
  `argparse` wraps them.

#### The help of a command

- **Given** a table with the command `ok`, which takes `--flag`.
- **When** `main(["ok", "--help"], stdio)` runs.
- **Then** it returns 0 and standard output names `--flag`.

### **AC-2** `--version` prints the version

`wio --version` prints `wio` and the version of the `work-it-out` distribution
to standard output and exits 0.

#### The version

- **Given** the synchronized environment.
- **When** `main(["--version"], stdio)` runs.
- **Then** it returns 0, standard output is `wio` and the version from
  `importlib.metadata` and a newline, and standard error is empty.

### **AC-3** Only the chosen command is wired, once

The `wire` of an entry runs once when its subcommand is chosen, and never for
bare `wio`, `--help` or `--version`.

```python
Component = Literal["config", "contracts", "rules", "trailers", "log", "context"]


@dataclass(frozen=True)
class Entry:
    component: str
    wire: Callable[[], Command]
```

`wio.cli` imports `wio.<component>` and calls its `describe() -> CommandSpec`.

#### One command is chosen

- **Given** a table of `ok` and `no`, each with a `wire` that records its call.
- **When** `main(["ok"], stdio)` runs, then bare, `--help` and `--version`.
- **Then** `ok` was wired exactly once, `no` never, and the last three called no
  `wire`.

### **AC-4** A command's exit code is the run's exit code

A command that returns 0 or 1 makes the run exit with that code, and receives
its parsed arguments.

#### Success and a failed check

- **Given** a table of `ok`, which returns 0, and `no`, which returns 1, with
  `ok` taking `--flag`.
- **When** `main(["ok", "--flag"], stdio)` and `main(["no"], stdio)` run.
- **Then** they return 0 and 1, and `ok` received `--flag` in its arguments.

### **AC-5** A usage mistake exits 2

An unknown subcommand, an unknown option, or a bad option of a known subcommand
exits 2 with `argparse`'s message on standard error, and `main` raises nothing.

#### Mistakes

- **Given** a table with the command `ok`.
- **When** `main(["nope"], stdio)`, `main(["--nope"], stdio)` and
  `main(["ok", "--bad"], stdio)` run.
- **Then** each returns 2 without raising, standard output is empty and standard
  error names the unknown word.

### **AC-6** A failure exits 2 or 70 with its message

A `WioError` raised while the command is described, configured, wired or run
exits 2 with `error:` and its message on standard error. Any other exception
exits 70 with its traceback on standard error, and so does a `run` that returns
a code other than 0 or 1, with a message naming the command and the code.

#### A configuration error

- **Given** a command whose `wire` raises `ConfigurationError("no config")`, and
  another whose `run` does.
- **When** `main` runs each.
- **Then** each returns 2, standard error is `error: no config` and a newline,
  and standard output is empty.

#### A bug

- **Given** a command whose `run` raises `RuntimeError("boom")`, another whose
  `wire` does, and one whose `run` returns 3.
- **When** `main` runs each.
- **Then** each returns 70 with standard output empty, the last line of
  standard error is `RuntimeError: boom` for the first two, and standard error
  for the third names the command and the code 3.

### **AC-7** The core writes only to `stdio`

`main` leaves the process's own streams alone, including when `argparse` prints.

#### Help and mistakes

- **Given** in-memory `stdio` and the process's `sys.stdout` and `sys.stderr`
  captured.
- **When** `main(["--help"], stdio)`, `main(["--version"], stdio)` and
  `main(["nope"], stdio)` run.
- **Then** the process's streams hold nothing, and the output is in `stdio`.

### **AC-8** The import-light rule can fail

A check over a table of entries fails for an entry whose package loads a module
under it, other than its `__init__`, when `describe()` and the `configure` of
its description run, and passes for an entry whose package loads none.

#### A fixture command

- **Given** two fixture packages under `tests`, one whose `__init__` imports an
  implementation module eagerly and one that imports it lazily, each with an
  entry.
- **When** the check runs over each entry, in a fresh interpreter.
- **Then** it fails for the first and names the implementation module, and
  passes for the second. Over the real table it passes, which is vacuous until
  the first component adds its entry.

### **AC-9** The real table names only real components

`component_entry` takes a `Component`, so a name that is not one fails the type
check, and the `Component` names equal the component packages of `wio`.

```python
def component_entry(name: Component, wire: Callable[[], Command]) -> Entry: ...
```

#### An unknown component

- **Given** a call `component_entry("nonexistent", wire)` added locally by the
  reviewer and not committed.
- **When** `uv run pyrefly check` runs.
- **Then** it exits non-zero and names the call.

#### The names match the packages

- **Given** the delivered tree.
- **When** a unit test compares the names in `Component` with the component
  packages in `tach.toml`.
- **Then** the two lists are equal.

### **AC-10** The command port is split and documented

`src/wio/cli/ports.pyi` declares `CommandSpec` and `Command`, each with a
docstring: `CommandSpec` has read-only `name` and `help` properties and
`configure(parser: ArgumentParser) -> None`, and `Command` has
`run(args: Namespace, stdio: Stdio) -> int`. The glossary of `src/wio/cli`
defines Command, command spec and entry in place of its single definition of
Command.

### **AC-11** The tests of the old behavior are replaced

No test pins the behavior of the silent placeholder: the rewrites keep what each
checked, now against the new behavior, and weaken nothing.

#### The five tests

- **Given** the tests that assert silence or an expected failure:
  `test_main_returns_zero_and_writes_nothing` and
  `test_console_main_builds_the_real_streams_and_returns_zero` in
  `tests/unit/cli/test_main.py`,
  `test_the_installed_command_exits_zero_without_output` in
  `tests/unit/cli/test_entry_point.py`, and
  `test_the_first_scenario_is_expected_to_fail_on_both_channels` and
  `test_the_first_scenario_fails_on_the_assertion` in
  `tests/unit/acceptance/test_channels.py`.
- **When** the delivered tree is searched for them.
- **Then** each is rewritten for the new behavior or removed with the behavior
  it covered, and `make check` and `make slow` pass.

### **AC-12** The documents match the exit codes

The order of work in `docs/v0.1-scope.md` names the command line and the errors
module before `wio config`, and that document, `tests/README.md` and the
docstrings of `main` and `Command.run` state the four exit codes of the parent
where they stated three.
