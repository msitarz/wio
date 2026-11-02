# Glossary of `src/wio/cli`

Terms of the `wio` command line. They bind to this directory and its
descendants, and the nearest `GLOSSARY.md` wins. The terms of the architecture
are in the [glossary of `src/wio`](../GLOSSARY.md).

| Term | Meaning |
| --- | --- |
| Command | The object a component exposes to the command line, with a name, a help text, a function that configures its argparse subparser and a function that runs it. |
| Composition root | `wio.cli`: the one package that imports the commands of the components and the adapters of `wio.io` and `wio.env`, and gives each component the implementations of the ports it consumes. It is not a component. |
