<!-- wio
id = "vds425"
template = "feature.leaf"
roots = ["wio"]
depends_on = ["jsk0yt"]
-->

# Test DSL and first acceptance scenario

## Purpose

Every component's criteria become acceptance scenarios, so the vocabulary, the
channels and one working example must exist before the first component.

## Goals

- A scenario can reach `wio` through the same domain verbs on two channels.
- One scenario shows the shape of an acceptance test, and waits for the `cli`
  package.
- The test strategy document says what the channels are for.

## Non-Goals

- Facade verbs, builders and results for config, contract, rule, context,
  trailers or log, which come with the Works that need them.
- Golden tests, fixtures of sample repositories and the `--json` and `--explain`
  parsing.
- Promoting the DSL out of `tests/acceptance/`.

## Assumptions

- **A-1**: The console script that the skeleton installs is next to the Python
  executable in the environment, so the CLI driver can run it without a shell.
- **A-2**: Running the bare command writes no file, so the repository the
  drivers prepare can be an empty directory.
- **A-3**: Bare `wio` is meant to print the `description` of `pyproject.toml` on
  standard output and exit 0, which the scope document does not state, and the
  Work of the `cli` package may change the scenario to match what it decides.

## Mechanisms

- `tests/acceptance/dsl/wio.py`, the `Wio` facade, with the verb `help()`.
- `tests/acceptance/drivers/base.py`, the `WioDriver` Protocol, and the drivers
  `in_process.py` (calls `wio.cli.main` with in-memory streams) and `cli.py`
  (runs the `wio` command in a subprocess).
- A `Sandbox` that each driver is built from, holding the directory under
  `tmp_path` that `wio` runs in and the environment it sees.
- `tests/acceptance/channels.py`, the `Channel` enum with the members
  `IN_PROCESS = "in_process"` and `CLI = "cli"`, and the `pytest_generate_tests`
  hook in `tests/acceptance/conftest.py` that parametrizes the `channels` marker
  and marks the CLI case `slow`.
- `tests/acceptance/cli/test_help.py`, the file of the first scenario.
- `pytest.mark.xfail(strict=True, raises=AssertionError)` on the scenario.

## Acceptance criteria

### **AC-1** A scenario reaches wio through a facade and a driver

A scenario asks the facade for `help()` and gets a result, without naming a
subprocess or a function of `wio`.

```python
@dataclass(frozen=True)
class RunResult:
    stdout: str
    stderr: str
    exit_code: int


class WioDriver(Protocol):
    def run(self, args: Sequence[str]) -> RunResult: ...


@dataclass(frozen=True)
class Help:
    text: str
    exit_code: int
```

`Wio(driver).help() -> Help` runs the driver with no arguments. Drivers return
data and never assert.

#### Both drivers return the same data

- **Given** the in-process and the CLI driver on an empty prepared repository.
- **When** each runs `wio` with no arguments.
- **Then** each returns a `RunResult`, with `exit_code` 0 and an empty `stdout`
  and `stderr` while the command prints nothing.

#### The facade maps a result

- **Given** a fake driver that returns `RunResult("usage\n", "", 0)`.
- **When** `Wio(driver).help()` is called.
- **Then** it returns `Help(text="usage\n", exit_code=0)`.

### **AC-2** The channel of a scenario is chosen by a marker

A test marked `channels(Channel.IN_PROCESS, Channel.CLI)` runs once per channel,
the in-process case is fast and the CLI case is marked `slow`.

#### One case per channel

- **Given** a test marked with both channels.
- **When** `uv run pytest --collect-only -m "slow or not slow"` runs.
- **Then** it lists two cases, ids `in_process` and `cli`, and the CLI case
  carries the `slow` marker.

#### Without a marker

- **Given** a test with no `channels` marker.
- **When** it runs.
- **Then** it uses the in-process channel.

### **AC-3** The first scenario waits for the `cli` package

The scenario for bare `wio` states that standard output contains the
description from `pyproject.toml` and that the exit code is 0, and is expected
to fail until the Work of the `cli` package.

```python
@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
@pytest.mark.xfail(strict=True, raises=AssertionError, reason="...")
def test_bare_wio_displays_its_description(wio: Wio) -> None: ...
```

#### The scenario is expected to fail

- **Given** the delivered tree.
- **When** `uv run pytest` and then `uv run pytest -m slow` run.
- **Then** each reports the scenario as xfailed for its channel and exits 0.

#### It fails on the assertion

- **Given** the scenario on either channel.
- **When** it runs.
- **Then** it fails with an `AssertionError` about the missing description, not
  with an import error or a missing command.

### **AC-4** Scenarios cannot touch the developer's own state

Each driver is built from a `Sandbox` under `tmp_path`, whose environment has
`HOME` and `XDG_DATA_HOME` inside it.

#### The sandbox

- **Given** a `Sandbox` made from `tmp_path`.
- **When** its root and environment are read.
- **Then** the root is a directory under `tmp_path`, and `HOME` and
  `XDG_DATA_HOME` in its environment are under `tmp_path`.

#### Both drivers use it

- **Given** each driver built from a sandbox.
- **When** it runs `wio`.
- **Then** the CLI driver starts the subprocess with the sandbox's directory and
  environment, and the in-process driver runs with the working directory and
  `HOME` set to the sandbox's, restored afterwards.

### **AC-5** The test strategy says what the channels are for

`tests/README.md` states that the CLI channel is the reference for acceptance
and that the in-process channel is the fast copy of the same scenarios, and its
layout lists `tests/acceptance/cli/`.

#### The test strategy

- **Given** the delivered documents.
- **When** `tests/README.md` is read.
- **Then** no sentence calls the CLI channel opt-in per test or limits both
  channels to where the CLI wiring matters, a sentence gives each channel's
  role, the layout lists `tests/acceptance/cli/`, step 2 of its order of work
  names the bare `wio` scenario, and `rumdl check` passes.

## Additional context

- The [test strategy](../../../../../tests/README.md) describes the layers, the
  DSL and the conventions that this Work applies; the
  [skeleton Work](../architecture-skeleton/README.md) provides the entry point
  it drives.
