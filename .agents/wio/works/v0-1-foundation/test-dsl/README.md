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
- A scenario cannot touch the developer's own state.
- The test strategy document says what the channels are for.
- The terms of the test setup are defined where the tests use them, apart from
  the engine's Driver.

## Glossary

These definitions are the source until this Work moves them to
`tests/GLOSSARY.md`, which binds them to `tests/` and its descendants.

- **Channel**: a way a scenario reaches `wio`, either in the same process or
  through the installed command.
- **Test driver**: the object that reaches `wio` for a scenario, on one channel;
  it is not the engine's Driver, which advances a Work.
- **Facade**: the `Wio` object whose verbs a scenario calls, in domain terms.
- **Sandbox**: the directory under `tmp_path` and the environment that a test
  driver gives `wio`.

## Non-Goals

- Facade verbs, builders and results for config, contract, rule, context,
  trailers or log, which come with the Works that need them.
- Golden tests, fixtures of sample repositories and the `--json` and `--explain`
  parsing.
- Promoting the DSL out of `tests/acceptance/`.

## Assumptions

- **A-1**: The console script that the skeleton installs is next to the Python
  executable in the environment, so the CLI test driver can run it without a
  shell.
- **A-2**: Running the bare command writes no file, so the repository the test
  drivers prepare can be an empty directory.
- **A-3**: Bare `wio` is meant to print the `description` of `pyproject.toml` on
  standard output and exit 0, which the scope document does not state, and the
  Work of the `cli` package may change the scenario to match what it decides.

## Mechanisms

Provisional: the names and shapes of the verb, the results and the test driver
Protocol below, which later Works extend. `tests/README.md` describes drivers
that run an operation, and operation-shaped verbs are layered on `run(args)` as
scenarios need them.

- `tests/acceptance/dsl/wio.py`, the `Wio` facade, with the verb `bare()`.
- `tests/acceptance/drivers/base.py`, the `WioDriver` Protocol, and the test
  drivers `in_process.py` (calls `wio.cli.main` with in-memory streams) and
  `cli.py` (runs the `wio` command in a subprocess).
- `tests/acceptance/sandbox.py`, the `Sandbox` that each test driver is built
  from, holding the directory under `tmp_path` that `wio` runs in and the
  environment it sees.
- `tests/acceptance/channels.py`, the `Channel` enum with the members
  `IN_PROCESS = "in_process"` and `CLI = "cli"`, and the `pytest_generate_tests`
  hook in `tests/acceptance/conftest.py` that parametrizes the `channels` marker
  and marks the CLI case `slow`.
- `tests/acceptance/cli/test_bare.py`, the file of the first scenario.
- `pytest.mark.xfail(strict=True, raises=AssertionError)` on the scenario.
- `tests/GLOSSARY.md`, which holds the terms of the test setup.

## Acceptance criteria

### **AC-1** A scenario reaches wio through a facade and a test driver

A scenario asks the facade for `bare()` and gets a result, without naming a
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
class Output:
    stdout: str
    stderr: str
    exit_code: int
```

`Wio(driver).bare() -> Output` runs the test driver with no arguments. Test
drivers return data and never assert.

#### Both test drivers return the same data

- **Given** the in-process and the CLI test driver on an empty prepared
  repository.
- **When** each runs `wio` with no arguments.
- **Then** each returns a `RunResult`, and the two results are equal.

#### The facade maps a result

- **Given** a fake test driver that returns
  `RunResult("usage\n", "warning\n", 3)`.
- **When** `Wio(driver).bare()` is called.
- **Then** it returns
  `Output(stdout="usage\n", stderr="warning\n", exit_code=3)`.

### **AC-2** The channel of a scenario is chosen by a marker

A test marked `channels(Channel.IN_PROCESS, Channel.CLI)` runs once per channel,
the in-process case is fast and the CLI case is marked `slow`.

#### One case per channel

- **Given** the first scenario, which is marked with both channels.
- **When** `uv run pytest --collect-only -q -m "slow or not slow"`, then the
  same with `-m slow`, and then with no `-m`, run.
- **Then** the first lists the cases with ids `in_process` and `cli`, the second
  lists only the `cli` case, and the third lists only the `in_process` case.

#### Without a marker

- **Given** a test with no `channels` marker.
- **When** it runs.
- **Then** it uses the in-process channel.

### **AC-3** The first scenario waits for the `cli` package

The scenario for bare `wio` states that standard output contains the
description from `pyproject.toml`, that standard error is empty and that the
exit code is 0, and is expected
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
- **When** it runs with `--runxfail`.
- **Then** it fails with an `AssertionError` about the missing description, not
  with an import error or a missing command.

### **AC-4** Scenarios cannot touch the developer's own state

Each test driver is built from a `Sandbox` under `tmp_path`. Its environment has
`WIO_HOME` inside it, and git in it uses no config, repository or identity of
the developer's.

#### The sandbox

- **Given** a `Sandbox` made from `tmp_path`.
- **When** its root and environment are read.
- **Then** the root is a directory under `tmp_path`, and `WIO_HOME` in its
  environment is under `tmp_path`.

#### Git in the sandbox

- **Given** a global git config and ignore file in the process's home, a
  repository above `tmp_path`, and `GIT_DIR` set in the process.
- **When** git runs in the sandbox's directory and environment.
- **Then** it has no `user.name`, finds no repository above, and lists a new
  file as untracked.

#### The CLI test driver

- **Given** the CLI test driver built from a sandbox, with `subprocess.run`
  replaced by a spy.
- **When** it runs `wio`.
- **Then** the spy received the sandbox's root as the working directory and the
  sandbox's environment.

#### The in-process test driver

- **Given** the in-process test driver built from a sandbox, with `wio.cli.main`
  replaced by a function that records the working directory and the environment.
- **When** it runs `wio`.
- **Then** the recorded working directory is the sandbox's root, the recorded
  environment is the sandbox's, and both are restored afterwards.

### **AC-5** The strategy document says what the channels are for

`tests/README.md` states that the CLI channel is the reference for acceptance
and that the in-process channel is the fast copy of the same scenarios, and its
layout lists `tests/acceptance/cli/`.

#### The strategy document

- **Given** the delivered documents.
- **When** `tests/README.md` is read.
- **Then** no sentence calls the CLI channel opt-in per scenario or limits both
  channels to where the CLI wiring matters, a sentence gives each channel's
  role, a note says that operation-shaped verbs are layered on the test driver's
  `run(args)` as scenarios need them, the layout lists `tests/acceptance/cli/`,
  and step 2 of its order of work names the bare `wio` scenario.

### **AC-6** The terms of the test setup are defined where they are used

`tests/GLOSSARY.md` defines the terms of the glossary above, binds them to
`tests/` and its descendants, and says that its test driver narrows the root
`GLOSSARY.md`'s Driver; `tests/README.md` uses "test driver" for it.

#### The glossary

- **Given** the delivered tree.
- **When** `tests/GLOSSARY.md` is read.
- **Then** it defines Channel, Test driver, Facade and Sandbox, and the entry
  for Test driver says how it differs from the root Driver.

#### The README

- **Given** the delivered documents.
- **When** `tests/README.md` is read for the word "driver".
- **Then** it is always preceded by "test", except in code identifiers and paths
  such as `WioDriver` and `drivers/`.

## Additional context

- The [test strategy](../../../../../tests/README.md) describes the layers, the
  DSL and the conventions that this Work applies; the
  [skeleton Work](../architecture-skeleton/README.md) provides the entry point
  it drives.
