# `wio.env`

The ports for what the process knows about its surroundings: its environment
variables, its working directory, the clock, randomness and the well-known
directories. A component reads them only through these ports, so a test can fix
every input it sees. The terms Environment, Port and Adapter are defined in the
[glossary of `src/wio`](../GLOSSARY.md).

- `ProcessEnvironment` is the first adapter. It implements only
  `working_directory`, the absolute working directory of the process, and its
  other members raise `NotImplementedError` naming the member, until the Work
  that first needs them implements them.
- Only `ProcessEnvironment` reads the process's working directory. Ruff enforces
  it: `pathlib.Path.cwd`, `os.getcwd` and `os.getcwdb` are banned in
  [`pyproject.toml`](../../../pyproject.toml) everywhere but
  `src/wio/env/adapters.py`, so a component that needs the directory is given an
  `Environment` instead.
