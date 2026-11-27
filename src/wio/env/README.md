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

## What only the adapters read

Only the adapters in [`adapters.py`](adapters.py) read the variables of the
process, the clock and the user's home directory, so a test can fix every one of
them with a fake of the port. A component outside `wio.env` gets them through
the ports, and `os.environ`, `os.getenv`, `time.time` and `Path.home` do not
appear outside this package. Ruff does not ban them, as it does the working
directory, so a reviewer's search verifies it.

Two choices are made for the callers' sake:

- `ProcessEnvironment.get` gives a variable as it is at the time of the call and
  reads nothing ahead, so a caller sees what the process has now. A variable set
  to an empty string comes back empty, and each caller decides what that means.
- `ProcessDirectories.wio_home` reads `WIO_HOME` through the `Environment` it is
  given, and asks for the user's home directory only when it needs the default,
  so a home that `WIO_HOME` names never depends on one existing. It neither
  creates nor tests the directory, because the first write creates it and a
  failure there is a warning, not an error of reading the path.

`ProcessDirectories.temp_dir` reads `$TMPDIR` without testing a non-empty
value; otherwise it probes the system directory by creating and removing a
small temporary file. Its [port](ports.pyi) states the selection and failure
rules, and the [adapter tests](../../../tests/integration/env/test_adapters.py)
cover the platform defaults and probe failures. This lets a harness name a
directory that it permits, even when that directory does not exist yet.

The terms are in the [glossary of `src/wio`](../GLOSSARY.md), and the rule for
the Wio home is in [the design](../../../docs/concepts.md#the-wio-home).
