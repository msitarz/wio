# `wio.cli`

The composition root of the `wio` command. The terms Command, Command spec,
Entry, Failed check and Bug are in the [glossary of `wio.cli`](GLOSSARY.md), and
the architecture it sits in is in the [overview of `src/wio`](../README.md).

## The table of commands

[`table.py`](table.py) holds one `Entry` for each subcommand of a component. A
subcommand joins the command line by adding an entry made with
`component_entry`, and nothing else.

- `Entry.package` is typed `Component`, a `Literal` of the seven components, so
  the type checker rejects a package name that is not a component. A new package
  under `src/wio` fails the unit test of the names until the driver decides
  whether it is a component.
- An entry keeps describing and wiring apart. `Entry.describe` returns the
  command spec, and `Entry.wire` builds the command with the adapters its
  component needs. The usage lists every command on every run, so every entry is
  described every time, while only the chosen command is wired.
- `Entry.wire` takes no platform parameter. The first adapter that differs by
  platform adds it.
- `component_entry` makes `describe` import `wio.<package>` and call the
  `describe()` that the package of every component provides.

A component's `wire` binds its command with a `lazy` import and builds the
adapters it needs there, so only the chosen command imports them. `config` is
the first entry; it reads the config file through the local disk and the git
repository.

The reason for the split is speed: a command that runs often must not load the
implementation of the commands it does not run.

## The command port

[`ports.pyi`](ports.pyi) splits a component's command in two, so that the part
the usage needs can be made without the part that runs:

- `CommandSpec` has a name, a help text and `configure`, which adds the
  arguments to the command's argparse subparser.
- `Command` has `run`, which takes the parsed arguments and the streams.

Making and using a command spec does no I/O and raises nothing in a working
installation, because it happens for every command on every run.

## Import-light packages

Importing the package of a command, and calling its `describe()` and the
`configure` of the spec that returns, loads no module under that package other
than its `__init__`. The package of a command binds its implementation with a
`lazy import` to keep it so. `import_light_violations` in
[`tests/support.py`](../../../tests/support.py) lists the modules that break the
rule, and the unit tests apply it to every entry of the table.

## The dispatch

[`main`](__init__.py) is the testable core of the command: it takes the
arguments, the streams and the table, and `console_main` runs it on the
process's own streams. [`dispatch.py`](dispatch.py) holds what it does.

- Every entry is described on every run, in order of name, so the usage lists
  every subcommand. Only the entry that was chosen is wired, once, and its exit
  code is the run's. Each subcommand's one-line help is also its description, so
  the text is written once.
- Bare `wio` and `--help` print the package's `Summary` and the subcommands.
  `wio <subcommand> --help` lists that command's options without wiring it.
  `--version` prints `wio <version>`. Both come from the metadata of the
  `work-it-out` distribution, so the program needs it installed.
- A usage mistake exits 2 with argparse's message on standard error.
- Argparse prints through `contextlib.redirect_stdout` and `redirect_stderr`
  pointed at the streams of `stdio`, so the help and the errors go where the
  caller wants. The redirect is global to the process, so `main` is not meant to
  run on several threads at once.
- The help is colored by Python's own rules, which look at `PYTHON_COLORS`,
  `NO_COLOR`, `FORCE_COLOR`, `TERM=dumb` and the stream, so a terminal gets
  color and a pipe or a file does not. The
  program is named `wio`, and its output is the same in process and as the
  installed command.

## Failures and exit codes

A run ends with one of four exit codes, and `main` never lets an `Exception`
out:

| Code | Meaning |
| --- | --- |
| 0 | Success, including the summary, the help and the version. |
| 1 | A command's failed check: its finished answer "no". |
| 2 | A usage mistake, or a `WioError`: something the user must fix. |
| 70 | A bug: any other exception, or a command's code other than 0 and 1. |

- A failed check is a result that the command returns, never an exception. A
  command raises a `WioError`, from [`wio.errors`](../errors.py), only for what
  the user must fix before it can answer.
- Any step can raise: describing and configuring the commands, wiring the chosen
  one, and running it. A `WioError` at any of them is written as `error:` and
  its message in plain text to standard error, whatever the color rules say.
- A bug is written to standard error with its traceback, and a wrong exit code
  with the command's name and the code.
- Everything, the failures included, is written to the streams of `stdio`, so
  the process's own streams stay untouched.
- Every `WioError` means exit 2, whatever its class: there is no exit code per
  error class and none for configuration errors.
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
- A command returns a failed check and raises a `WioError` only for what the
  user must fix, so the core never has to tell the two apart.
- The program needs the `work-it-out` distribution installed, because the
  summary and the version come from its metadata, where they equal the
  `description` and the `version` of `pyproject.toml`, in a synchronized
  environment and in an installed wheel.
