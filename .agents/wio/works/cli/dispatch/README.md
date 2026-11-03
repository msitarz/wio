<!-- wio
id = "sky395"
template = "feature.leaf"
roots = ["wio", "repo"]
depends_on = ["41wfqk"]
-->

# The command line dispatch

## Purpose

`wio.cli.main` ignores its arguments today, so no subcommand can run or appear
in the usage until `main` dispatches to the entries of the table and passes on
the exit code of the command chosen.

## Goals

- `wio`, `wio --help`, `wio <subcommand> --help` and `wio --version` show what
  wio is, its subcommands and its version.
- Every command is described on every run, so the usage lists them all, and
  only the command that was chosen is wired and its exit code is the run's.
- A usage mistake exits 2 with `argparse`'s message on standard error.
- The help is colored only where Python's color rules allow it, and the output
  is the same on every channel.
- No test still pins the behavior of the silent placeholder.

## Non-Goals

- Reporting the failures of commands, which the failures leaf does.
- Any real subcommand: the table is empty until the Work of the first component
  adds its entry.

## Assumptions

- **A-1**: `argparse` on Python 3.15 prints a usage error to `sys.stderr` and
  raises `SystemExit(2)`, and `--help` and `--version` print to `sys.stdout` and
  raise `SystemExit(0)` (checked on 3.15.2 on 2026-11-03).
- **A-2**: With its default `color=True`, `ArgumentParser` on Python 3.15 asks
  `_colorize.can_colorize` about the stream it prints to, which decides in this
  order: `PYTHON_COLORS`, `NO_COLOR`, `FORCE_COLOR`, `TERM=dumb`, then whether
  the stream is a terminal (read in the 3.15.2 source and checked on
  3.15.2 on 2026-11-03).

## Mechanisms

- `argparse` with `prog="wio"`, its default color rule and one subparser per
  entry, with `SystemExit` caught around parsing.
- `contextlib.redirect_stdout` and `redirect_stderr` pointing `argparse`'s
  output at the streams of `stdio`.
- `importlib.metadata` for the `Summary` and the version of `work-it-out`.

## Acceptance criteria

### **AC-1** Bare `wio` and `--help` introduce the command

Bare `wio` and `wio --help` print the package's `Summary` and the usage, listing
each subcommand with its help text in order of name, to standard output, and
exit 0.

```python
def main(
    argv: Sequence[str],
    stdio: Stdio,
    commands: Sequence[Entry] = COMMANDS,
) -> int: ...
```

`main` is required as written, with the `Entry` of the command-table leaf; its
default is the table, whose name is provisional. Fake entries in the scenarios
carry any `Component` name, such as `"config"`, with injected `describe` and
`wire` functions.

#### Bare, with two commands

- **Given** a table of entries `zeta` and `alpha`, built with injected
  `describe` and `wire` functions, with help texts.
- **When** `main([], stdio)` and `main(["--help"], stdio)` run.
- **Then** both return 0 with the same standard output, which holds the
  `Summary`, then the help text of `alpha` before that of `zeta`; standard error
  is empty. Only the order and the presence of the texts are checked, not how
  `argparse` wraps them.

### **AC-2** `wio <subcommand> --help` wires nothing

The help of a subcommand lists its options and exits 0 without wiring the
command, so it works where the command could not run.

#### The help of a command

- **Given** a table with the entry `ok`, which takes `--flag`, and a `wire` that
  records its call.
- **When** `main(["ok", "--help"], stdio)` runs.
- **Then** it returns 0, standard output names `--flag`, and `wire` was not
  called.

### **AC-3** `--version` prints the version

`wio --version` prints `wio <version>` and a newline to standard output, with
the version of the `work-it-out` distribution, such as `wio 0.0.1`, and exits
0.

#### The version

- **Given** the synchronized environment.
- **When** `main(["--version"], stdio)` runs.
- **Then** it returns 0, standard output is `wio`, a space, the version from
  `importlib.metadata` and a newline, and standard error is empty.

### **AC-4** Only the chosen command is wired, once

The `wire` of an entry runs once when its subcommand is chosen, and never for
bare `wio`, `--help` or `--version`.

#### One command is chosen

- **Given** a table of `ok` and `no`, each with a `wire` that records its call.
- **When** `main(["ok"], stdio)` runs, then bare, `--help` and `--version`.
- **Then** `ok` was wired exactly once, `no` never, the last three called no
  `wire`, and the `describe` of both entries ran every time.

### **AC-5** A command's exit code is the run's exit code

A command that returns 0 or 1 makes the run exit with that code, and receives
its parsed arguments.

#### Success and a failed check

- **Given** a table of `ok`, which returns 0, and `no`, which returns 1, with
  `ok` taking `--flag`.
- **When** `main(["ok", "--flag"], stdio)` and `main(["no"], stdio)` run.
- **Then** they return 0 and 1, and `ok` received `--flag` in its arguments.

### **AC-6** A usage mistake exits 2

An unknown subcommand, an unknown option, or a bad option of a known subcommand
exits 2 with `argparse`'s message on standard error, and `main` raises nothing.

#### Mistakes

- **Given** a table with the entry `ok`.
- **When** `main(["nope"], stdio)`, `main(["--nope"], stdio)` and
  `main(["ok", "--bad"], stdio)` run.
- **Then** each returns 2 without raising, standard output is empty and standard
  error names the unknown word.

### **AC-7** Color follows Python's rules and the channels agree

The usage names the program `wio`, and its color follows Python's color rules,
so a person on a terminal sees color while a pipe, a file or an in-memory
stream gets plain text, and a bare run gives the same output in process and as
the installed command.

#### Not a terminal

- **Given** in-memory `stdio` and an environment without `PYTHON_COLORS`,
  `NO_COLOR` or `FORCE_COLOR`.
- **When** `main([], stdio)` and `main(["nope"], stdio)` run.
- **Then** neither stream holds an escape character (`\x1b`), and the usage
  lines begin with `usage: wio`.

#### A terminal

- **Given** standard output on a pseudo-terminal from `os.openpty`, and the same
  environment.
- **When** `main(["--help"], stdio)` runs, then again with `NO_COLOR=1`.
- **Then** the first output holds an escape character and the second holds
  none.

#### The two channels agree

- **Given** the in-process test driver and the CLI test driver of the
  acceptance setup, each on its own prepared repository.
- **When** each runs `wio` with no arguments.
- **Then** their results are equal, which
  `test_both_test_drivers_return_the_same_data` in
  `tests/unit/acceptance/test_drivers.py` keeps asserting.

### **AC-8** No test pins the placeholder

No remaining test asserts empty output or an expected failure for bare `wio`,
and the tests rewritten for the new behavior assert the output the criteria
above state.

#### The tests of the old behavior

- **Given** the tests that assert silence or an expected failure:
  `test_main_returns_zero_and_writes_nothing` and
  `test_console_main_builds_the_real_streams_and_returns_zero` in
  `tests/unit/cli/test_main.py`,
  `test_the_installed_command_exits_zero_without_output` in
  `tests/unit/cli/test_entry_point.py`,
  `test_the_first_scenario_is_expected_to_fail_on_both_channels` and
  `test_the_first_scenario_fails_on_the_assertion` in
  `tests/unit/acceptance/test_channels.py`, the strict `xfail` of the bare
  scenario in `tests/acceptance/cli/test_bare.py`.
- **When** the delivered tree is searched for them.
- **Then** each is rewritten for the new behavior or removed with the behavior
  it covered, the bare scenario passes in both channels, and `make check` and
  `make slow` pass.
