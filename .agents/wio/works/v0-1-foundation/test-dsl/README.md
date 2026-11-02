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
  component.
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

## Mechanisms

- `tests/acceptance/dsl/wio.py`, the `Wio` facade, with the verb `help()`.
- `tests/acceptance/drivers/base.py`, the `WioDriver` Protocol, and the drivers
  `in_process.py` (calls `wio.cli.main` with in-memory streams) and `cli.py`
  (runs the `wio` command in a subprocess).
- `tests/acceptance/channels.py`, the `Channel` enum, and the
  `pytest_generate_tests` hook in `tests/acceptance/conftest.py` that
  parametrizes the `channels` marker and marks the CLI case `slow`.
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
```

`Wio.help() -> Help`, where `Help` is a frozen dataclass of `text: str` and
`exit_code: int`. Drivers return data and never assert.

#### Both drivers return the same data

- **Given** the in-process and the CLI driver on an empty prepared repository.
- **When** each runs `wio` with no arguments.
- **Then** each returns a `RunResult`, with `exit_code` 0 and an empty `stdout`
  and `stderr` while the command prints nothing.

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

### **AC-3** The first scenario waits for the `cli` component

The scenario for bare `wio` states that the command displays its description and
exits 0, and is expected to fail until the `cli` component's Work.

```python
@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
@pytest.mark.xfail(strict=True, raises=AssertionError, reason="...")
def test_bare_wio_displays_its_description(wio: Wio) -> None: ...
```

The description it expects is the `description` in `pyproject.toml`.

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

Each scenario runs in a directory under `tmp_path`, with `HOME` and the XDG data
directory inside it, on both channels.

#### Isolated environment

- **Given** a scenario on either channel.
- **When** the driver starts `wio`.
- **Then** the environment `wio` sees has `HOME` and `XDG_DATA_HOME` under
  `tmp_path`, and the working directory is a directory under `tmp_path`.

### **AC-5** The test strategy says what the channels are for

`tests/README.md` states that the CLI channel is the reference for acceptance
and that the in-process channel is the fast copy of the same scenarios, and its
layout lists `tests/acceptance/cli/`.

#### The test strategy

- **Given** the delivered documents.
- **When** `tests/README.md` is read.
- **Then** it has a sentence on each channel's role, its directory layout lists
  `tests/acceptance/cli/`, and `rumdl check` passes.

## Additional context

- The [test strategy](../../../../../tests/README.md) describes the layers, the
  DSL and the conventions that this Work applies; the
  [skeleton Work](../architecture-skeleton/README.md) provides the entry point
  it drives.
