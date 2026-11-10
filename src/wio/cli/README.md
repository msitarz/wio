# `wio.cli`

The composition root of the `wio` command. The terms Command, Command spec,
Entry, Failed check and Bug are in the [glossary of `wio.cli`](GLOSSARY.md), and
the architecture it sits in is in the [overview of `src/wio`](../README.md).

## The table of commands

[`table.py`](table.py) holds one `Entry` for each subcommand of a component, and
its docstrings say what an entry guarantees. A subcommand joins the command line
by adding an entry made with `component_entry`, and nothing else.

- A new package under `src/wio` fails the unit test of the names until the
  driver decides whether it is a component.
- `Entry.wire` takes no platform parameter. The first adapter that differs by
  platform adds it.

An entry keeps describing and wiring apart, and
[`ports.pyi`](ports.pyi) splits a component's command the same way, into a
`CommandSpec` and a `Command`. The reason is speed: the usage lists every
command on every run, so every entry is described every time, while only the
chosen command is wired, and a command that runs often must not load the
implementation of the commands it does not run.

## Import-light packages

Importing the package of a command, and calling its `describe()` and the
`configure` of the spec that returns, loads no module under that package other
than its `__init__`. The package of a command binds its implementation with a
`lazy import` to keep it so. `import_light_violations` in
[`tests/support.py`](../../../tests/support.py) lists the modules that break the
rule, and the unit tests apply it to every entry of the table.

## The dispatch

[`dispatch.py`](dispatch.py) holds what a run does, and the docstring of `main`
in [`__init__.py`](__init__.py) says what it prints and which exit code it
returns.

- The help is colored by Python's own rules, so a terminal gets color and a pipe
  or a file does not. The program is named `wio`, and its output is the same in
  process and as the installed command.
- Argparse prints through `contextlib.redirect_stdout` and `redirect_stderr`,
  which are global to the process, so `main` is not meant to run on several
  threads at once.
- The program needs the `work-it-out` distribution installed, because the
  summary and the version come from its metadata, where they equal the
  `description` and the `version` of `pyproject.toml`, in a synchronized
  environment and in an installed wheel.

## Failures and exit codes

A run ends with exit code 0, 1, 2 or 70, and `main` never lets an `Exception`
out. A command returns a failed check and raises a `WioError` only for what the
user must fix, so the core never has to tell the two apart.

- Every `WioError` means exit 2, whatever its class: there is no exit code per
  error class and none for configuration errors.
- A `WioError` is written as `error: <message>`. A `DiagnosticsError`, such as
  a `ConfigurationError` or a `TemplatesError`, that carries diagnostics is
  written as they are, one `error: <where>: <message>`
  line each, because the message already holds those lines, and a second prefix
  would hide that the first is a finding.
- The exceptions that other ports declare, such as `ValueError`, `OSError` and
  `UnicodeDecodeError`, are bugs and exit 70, until the Work of the component
  that owns the port maps them to a `WioError`.
- `KeyboardInterrupt` and a `SystemExit` that a command raises are not handled.

## What every command follows

The command line gives every subcommand the same behavior, so a person or an
agent can rely on it. The core can enforce some of it, and a command's own
tests check the rest, because only a real command has output to check.

- Standard output carries what the command was asked for, the findings of a
  check included. Standard error carries diagnostics about the run itself and
  the error messages, in plain text.
- `--json` is an option of each command, declared by its `configure`. On exit 0
  or 1, standard output holds one JSON document and nothing else. On exit 2 and
  70 it is empty, and the message is plain text on standard error.
- Output is deterministic: sorted, and without timestamps, except in `wio log`,
  whose purpose is to report when events happened. Notes and warnings never
  change the exit code. There is no pager, and wio's own messages are never
  colored. Only the help and usage that argparse prints are, by Python's color
  rules.
