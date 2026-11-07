# Glossary of `src/wio`

Terms of the architecture of wio's source. They bind to this directory and its
descendants, and the nearest `GLOSSARY.md` wins. The terms of the engine are in
the [repository glossary](../../GLOSSARY.md).

| Term | Meaning |
| --- | --- |
| Component | The package under `src/wio` of one v0.1 subcommand: `config`, `contracts`, `templates`, `rules`, `trailers`, `log` or `context`. `cli` is the composition root, `errors` holds the errors that packages share, and `models`, `formats`, `io`, `env` and `ports` are shared layers, so none of them is a component. |
| Port | A `typing.Protocol` declared in a `.pyi` stub, saying what a package needs from the outside. Its consumer owns it, in `<package>/ports.pyi`, except the ports of `wio.io` and `wio.env`, which those packages own, and the ports in `src/wio/ports.pyi`, which two or more components consume identically. |
| Adapter | The implementation of a port: one per port, or for a port of `wio.env` one for each supported platform where its behavior differs. Only `wio.cli` and the unit tests import adapters. |
| Environment | The `wio.env` port for what the process knows about its surroundings: its environment variables and its working directory. It is the only way `src/wio` learns the working directory, and `ProcessEnvironment` is the one place that reads it. It is not the `Environment` of a deployment or a virtual environment. |
