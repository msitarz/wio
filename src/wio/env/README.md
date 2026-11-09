# `wio.env`

The ports for what the process knows about its surroundings: its environment
variables, its working directory, the clock, randomness and the well-known
directories. A component reads them only through these ports, so a test can fix
every input it sees. The terms Environment, Port and Adapter are defined in the
[glossary of `src/wio`](../GLOSSARY.md).

Only `ProcessEnvironment` in [`adapters.py`](adapters.py) reads the process's
working directory. Ruff enforces it: the three direct calls `pathlib.Path.cwd`,
`os.getcwd` and `os.getcwdb` are banned in
[`pyproject.toml`](../../../pyproject.toml) in `src/wio` outside that module, so
a component that needs the directory is given an `Environment` instead. The ban
does not cover every way to find the working directory, such as `Path().cwd()`.
