# wio acceptance tests

How to write an acceptance test. It adds to the [test strategy](../README.md),
which says when a behaviour needs one, and covers the principles of acceptance
tests and what the DSL and the channels are for. For a working scenario, read
[`config/test_show.py`](config/test_show.py).

## 1. Principles

- **Acceptance tests speak the domain's language.** A test says
  `wio.run(["config", "show"])`, never `subprocess.run(["wio", "config", ...])`.
  Only test drivers know how wio is reached.
- **One acceptance criterion = one scenario.** Contract ACs are independently
  assessable; each maps to one scenario.
- **Test drivers return data and never assert.** Tests assert on the returned
  data with plain `assert`. That keeps test drivers identical across channels
  and lets pytest's assertion introspection work.
- **Fast by default.** `uv run pytest` runs the in-process channel. The CLI
  channel is the reference for acceptance and runs the same scenarios with
  `make slow`.
- **Start small.** Add vocabulary to the facade only when a scenario needs it.

## 2. Layout

Scenarios live in one folder per feature, and in `cli/` for the `wio` command
line itself, so coverage gaps are easy to see. The DSL lives inside
`tests/acceptance/` because nothing else uses it yet; promote it to its own
package only when a second consumer (for example `wio-eval`) needs it.

Wio does not lint Markdown, so a scenario never needs `rumdl` or a diagram
renderer. Where a scenario needs git (for example a commit message with
records), it creates a real repository in `tmp_path`.

## 3. The DSL

The `Wio` facade in [`dsl/wio.py`](dsl/wio.py) is what a scenario sees, and a
`WioDriver` in [`drivers/base.py`](drivers/base.py) is how a channel reaches
`wio`.

- **One generic verb.** A command runs through `wio.run(args)`, so the facade
  has no method for each `wio` command and the test drivers dispatch in one
  place. An operation-shaped verb is layered on it only when a scenario needs
  it.
- **Builders, when a scenario needs them.** The config, contract metadata, rule
  files, templates and roots are fixtures that interact. Without builders every
  test hand-writes TOML and Markdown, and any format change breaks every test. A
  builder starts from a minimal valid repo, and each scenario changes only the
  parts it tests. A test that needs more than three overrides is a sign that the
  builder default is wrong or that the scenario tests two things.
- **Fixtures.** `wio.fixture(name)` starts from a static sample repository under
  `tests/fixtures`. A scenario that needs no repository, such as running outside
  one, installs nothing and runs on the CLI channel. The in-process driver only
  copies the fixture, and the CLI driver also runs `git init`, so the command
  finds a repository as it does for a user.
- **Results** are frozen dataclasses with few, obvious dunder methods. Where
  `in` would be ambiguous, such as a rule code against text in the output,
  assert on an explicit field. Assertion rewriting applies only to test modules,
  so register a DSL module that holds assert helpers with
  `pytest.register_assert_rewrite` in `tests/conftest.py`.
- **A channel that is asynchronous,** such as a future MCP or HTTP driver, needs
  a polling helper, since a bare `assert` cannot wait.

## 4. Channels

The channels are in [`channels.py`](channels.py), and a test chooses them with
the `channels` marker, as [`config/test_show.py`](config/test_show.py) does.
`IN_PROCESS` is the fast default: no process starts. `CLI` runs the real
command, and is for what only a process shows:

- error scenarios (exit 2 and the message on standard error) and running
  outside a repository;
- exit codes, `--json`, finding the config and byte-stable output;
- the `uvx` entry point and behavior that depends on the environment, such as
  session-id detection.

The CLI channel is the reference for acceptance: it is the command users and
skills run. The in-process channel is the fast copy of the same scenarios, so a
scenario that passes on one should pass on the other. A future channel, such as
MCP or a skill's command sequence, is a new test driver, and the scenarios do
not change.
