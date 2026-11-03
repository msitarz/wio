<!-- wio
id = "9wbqyb"
template = "feature.parent"
roots = ["@descendants"]
depends_on = ["ew60gw"]
-->

# The wio command line

## Purpose

Every subcommand of wio needs one entry point that tells a person or an agent
what wio is, runs the subcommand chosen and reports every outcome the same way,
before the first subcommand can exist.

## Goals

- A person or an agent can run `wio` to see what it is and which subcommands it
  has, and ask which version is installed.
- Every run ends with one exit code and its message on one stream, so a caller
  can tell success, a failed check, its own mistake and a bug in wio apart.
- A subcommand joins the command line with one entry in a table, and a name
  that is not a component of wio is rejected before it runs.
- Every package can raise the errors that wio reports as the user's to fix, from
  one module that depends on nothing.

## Glossary

- **Failed check**: a command's finished answer "no", reported as its output and
  exit code 1, and never as an exception.
- **Bug**: an exception that escapes a command and is not a `WioError`, or a
  command's exit code that is neither 0 nor 1.

## Non-Goals

- Implementing any subcommand, which the Work of each component does.
- `wio init`, which comes in v0.2.
- Color, a pager and shell completion.
- Wiring adapters that differ by platform: the first Work that adds one gives
  the wiring the platform.
- A separate exit code for configuration errors.
- Running without the package metadata of an installed distribution: the
  version and the description come from it.
- Handling `KeyboardInterrupt`, or a `SystemExit` that a command raises.
- Deciding whether the exceptions that other ports declare (`ValueError`,
  `RuntimeError` for a directory outside a git repository, `OSError`,
  `UnicodeDecodeError`) become `WioError`s: the Work of each component maps its
  own.

## Assumptions

- **A-1**: The package metadata of this project, which names the distribution
  `work-it-out`, holds the `Summary` and the version that `wio` shows, equal to
  the `description` and `version` of `pyproject.toml`, in the synchronized
  environment and in an installed wheel (checked for the synchronized
  environment on 2026-11-03).

## Mechanisms

- `argparse`, with one subparser per subcommand, for the usage, the help and the
  usage errors.
- `importlib.metadata`, reading the `Summary` and the version of the
  `work-it-out` distribution.
- Python 3.15 `lazy import` in the package of every command, so that importing
  the package to describe the command loads none of its implementation.
- `wio.errors`, a module of exception classes that the command line catches.
- `tach check`, for the dependency direction of `wio.errors` and for the
  `visibility` that lets only `wio.cli` import an adapter.

## Constraints

- **Exit codes.** A run exits 0 on success, 1 on a failed check, 2 on a usage
  error or a `WioError`, and 70 on a bug. Notes and warnings never change the
  code.
- **A failed check is a result.** A command returns it and never raises for it;
  it raises a `WioError` only for what the user must fix before the command can
  answer.
- **Streams.** Standard output carries what the command was asked for, the
  findings of a check included. Standard error carries diagnostics about the run
  itself and error messages in plain text, also with `--json`. There is no color
  and no pager, also when `FORCE_COLOR` is set, and output is deterministic:
  sorted, and without timestamps except in `wio log`, whose purpose is to report
  when events happened.
- **`--json`.** It is an option of each command, declared by the command's
  `configure`. On exit 0 or 1, standard output holds one JSON document and
  nothing else; on exit 2 and 70 it is empty, and the message is plain text on
  standard error.
- **Import-light commands.** Importing the package of a command, and calling its
  `describe` and the `configure` of its description, loads no module under that
  package other than its `__init__`.
- **Dependency direction.** `wio.errors` imports nothing else from `wio`, and
  every package may import it. Only `wio.cli` and the unit tests import an
  adapter, so a component never learns which adapters implement its ports.
- **Verification.** The leaves verify the exit codes, the streams, the absence
  of color and the import-light rule with fake commands. `tach check` verifies
  that `wio.errors` depends on nothing and that only `wio.cli` and the unit
  tests import an adapter. The Work of each command verifies, in its own
  criteria, the `--json` rule, that notes and warnings leave the exit code
  alone, and that its output is sorted and free of timestamps, because only a
  real command has an output to check. The parent verifies the installed wheel.

## Visuals

The before state is drawn from `main` at commit
`16dbe2d636c984a42cb976ec50c272d790f10233` and checked against `src/wio/cli`,
`src/wio/ports.pyi` and `tach.toml` at that commit. The after state is
provisional: the packages and their edges are required, and the names inside
`wio.cli` are not.

Before: only `console_main` builds the adapter for the process's streams, `main`
ignores its arguments, and the `Command` protocol is implemented by nothing.

```mermaid
flowchart LR
    subgraph cli["wio.cli"]
        console["console_main()"]
        main["main(argv, stdio): ignores argv, returns 0"]
        command["Command: name, help, configure, run (stub only)"]
    end
    adapter["wio.io.adapters: SystemStdio"]
    console --> adapter
    console --> main
```

After: a table of commands, each described apart from its wiring, and errors
that the entry point catches. Bold boxes are added, and bold dashed boxes
change. The names inside `wio.cli` are the leaves' to settle.

```mermaid
flowchart LR
    subgraph cli["wio.cli"]
        console["console_main()"]
        main["main()"]:::changed
        table["table of commands"]:::new
    end
    adapter["wio.io.adapters: SystemStdio"]
    component["a component package"]
    errors["wio.errors"]:::new
    every["every package"]
    console --> adapter
    console --> main
    main --> table
    table -- "describe(), lightly" --> component
    table -- "wire() calls the factory" --> component
    table -- "wire() builds" --> adapter
    main -- "catches WioError, exits 2" --> errors
    every -- "may import" --> errors
    classDef new stroke-width: 3px
    classDef changed stroke-width: 3px,stroke-dasharray: 4 3
```

## Acceptance criteria

### **AC-1** The installed wheel carries the entry point and its metadata

A wheel built from the tree gives a working `wio` command that reads its
description and version from its own metadata, without the source tree.

#### The installed command

- **Given** the wheel built from the tree, run with
  `uv run --no-project --isolated --with <wheel>`.
- **When** `wio` and `wio --version` run there.
- **Then** `wio` prints the wheel's `Summary` to standard output and exits 0,
  and `wio --version` prints `wio` and the wheel's version and a newline, and
  exits 0.

## Additional context

- [v0.1 scope](../../../../docs/v0.1-scope.md) names the command line as a part
  and its outcome; the failures leaf adds this Work to its order of work.
- `test_wheel_imports_from_a_clean_environment` in `tests/packaging` already
  runs a built wheel in an isolated environment this way.
