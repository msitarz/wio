# Glossary of `src/wio/cli`

Terms of the `wio` command line. They bind to this directory and its
descendants, and the nearest `GLOSSARY.md` wins. The terms of the architecture
are in the [glossary of `src/wio`](../GLOSSARY.md).

| Term | Meaning |
| --- | --- |
| Command | The object that runs one subcommand once it has been chosen: its `run` takes the parsed arguments and the streams and returns an exit code. |
| Command spec | What the usage needs to know about a subcommand: its name, its help text and a function that configures its argparse subparser. Making and using it does no I/O, and it is described apart from wiring the command. |
| Entry | One row of the table of commands: the component that provides a subcommand, a function that describes its command spec and a function that wires its command. |
| Failed check | A command's finished answer "no", reported as its output and exit code 1, and never as an exception. |
| Bug | An exception that escapes a command and is not a `WioError`, or a command's exit code that is neither 0 nor 1. |
| Composition root | `wio.cli`: the one package that imports the commands of the components and, besides the unit tests, the adapters of `wio.io` and `wio.env`, and gives each component the implementations of the ports it consumes. It is not a component. |
