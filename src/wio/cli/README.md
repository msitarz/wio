# `wio.cli`

The composition root of the `wio` command. The terms Command, Command spec and
Entry are in the [glossary of `wio.cli`](GLOSSARY.md), and the architecture it
sits in is in the [overview of `src/wio`](../README.md).

## The table of commands

[`table.py`](table.py) holds one `Entry` for each subcommand of a component. A
subcommand joins the command line by adding an entry made with
`component_entry`, and nothing else.

- `Entry.package` is typed `Component`, a `Literal` of the six components, so
  the type checker rejects a package name that is not a component. A new package
  under `src/wio` fails the unit test of the names until the driver decides
  whether it is a component.
- An entry keeps describing and wiring apart. `Entry.describe` returns the
  command spec, and `Entry.wire` builds the command with the adapters its
  component needs. The usage lists every command on every run, so every entry is
  described every time, while only the chosen command is wired.
- `component_entry` makes `describe` import `wio.<package>` and call the
  `describe()` that the package of every component provides.

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
