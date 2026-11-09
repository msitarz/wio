# wio acceptance tests

How to write an acceptance test. It adds to the [test strategy](../README.md),
which says when a behaviour needs one, and covers the principles of acceptance
tests, their directory layout, the DSL and the channels. Examples are sketches.

## 1. Principles

- **Acceptance tests speak the domain's language.** A test says
  `wio.context(work_id=..., action=..., stage=...)`, never
  `subprocess.run(["wio", "context", ...])`. Only test drivers know how
  wio is reached.
- **One acceptance criterion = one scenario.** Contract ACs are independently
  assessable; each maps to one DSL scenario.
- **Test drivers return data and never assert.** Tests assert on the returned
  data with plain `assert`. That keeps test drivers identical across channels
  and lets pytest's assertion introspection work.
- **Fast by default.** `uv run pytest` runs the in-process channel. The CLI
  channel is the reference for acceptance and runs the same scenarios with
  `make slow`.
- **Start small.** One DSL facade and two test drivers, in-process and CLI.
  Add vocabulary only when a scenario needs it.

## 2. Directory layout

The scenarios live in one folder per v0.1 feature (`config`, `contracts`,
`rules`, `context`, `trailers`, `log`) and in `cli/` for the `wio` command line
itself, so coverage gaps are easy to see. The facade and its results are in
`dsl/`, the test drivers in `drivers/`, and the channel setup in `channels.py`
and `conftest.py`. The DSL lives inside `tests/acceptance/` because nothing else
uses it yet; promote it to its own package only when a second consumer (for
example `wio-eval`) needs it.

Wio does not lint Markdown, so a scenario never needs `rumdl` or a diagram
renderer. Where a scenario needs git (for example a commit message with
records), it creates a real repository in `tmp_path`.

## 3. The DSL

### 3.1 Layers

| Layer | Role |
|---|---|
| Scenario (test function) | States what happens, in domain terms |
| `Wio` facade | Domain verbs: `config`, `rules`, `work`, `context`, `trailers`, `check`, `contracts_new`. Applies defaults. |
| Builders | Produce a minimal valid repo state; tests override only what they are about |
| `WioDriver` (Protocol) | Narrow interface: run an operation against a prepared temp repo, return a result object |
| Test drivers | In-process and CLI implementations of the Protocol |

### 3.2 Builders matter most

The config, contract metadata, rule files, templates and roots are fixtures
that interact. Without builders every test hand-writes TOML and markdown, and
any format change breaks every test. The `Wio` facade starts from a minimal
valid repo (one root, one action, one stage, one kind with its entry template)
and each
scenario changes only the parts it tests.

```python
def test_reviewer_only_rules_never_reach_the_author_stage(wio):
    # Given an authoring stage and a rule that only the review stage includes
    wio.config(
        stages=[
            stage("architecture"),
            stage("architecture-review", rules_include=["py.ARC001"]),
        ]
    )
    wio.rules("py.ARC001")
    wio.work("feature", id="k3m9xq")

    # When the context for the authoring stage is compiled
    bundle = wio.context(work_id="k3m9xq", action="deliver", stage="architecture")

    # Then the review rule is not in it
    assert "ARC001" not in bundle
```

Until the builders exist, a scenario starts from a fixture:
`wio.fixture("config/rich")` copies the static sample repository
`tests/fixtures/config/rich` into the sandbox. A command runs through the one
generic verb, `wio.run(["config", "show"])`, so the facade has no method for
each `wio` command and the test drivers dispatch in one place.

A test that needs more than three builder overrides is a sign the builder
default is wrong or the scenario is testing two things.

### 3.3 Results and assertions

Results are frozen dataclasses. Keep dunder methods few and obvious:
`__contains__` for rule codes on `Bundle`, `__eq__` for golden comparisons.

```python
@dataclass(frozen=True)
class Bundle:
    header: Header
    rules: frozenset[str]  # rule codes
    trace: Mapping[str, str]  # rule code -> why included/excluded (from --explain)

    def __contains__(self, rule_id: str) -> bool:
        return rule_id in self.rules
```

If `in` would be ambiguous (rule code vs text in the rendered output), assert on
an explicit field instead: `assert "x" not in bundle.rules`.

Make failures explain themselves with `pytest_assertrepr_compare` in
`tests/acceptance/conftest.py`. The test drivers fill `trace` by running
`wio context --explain`, so a failing assert shows why a rule was or was not
included.

```python
def pytest_assertrepr_compare(config, op, left, right):
    if op in ("in", "not in") and isinstance(right, Bundle):
        return [
            f"rule {left!r} {'unexpectedly in' if op == 'not in' else 'missing from'} "
            f"bundle {right.header.bundle_id}",
            f"stage={right.header.stage}  rules={sorted(right.rules)}",
            f"why: {right.trace.get(left, 'no trace entry')}",
        ]
```

Assertion rewriting only applies to test modules. If assert helpers live in DSL
modules, register them in `tests/conftest.py`:

```python
pytest.register_assert_rewrite("tests.acceptance.dsl")
```

Exception: if a channel is asynchronous (a future MCP or HTTP test driver), use
a polling helper such as `eventually(...)`, since a bare `assert` cannot wait.

## 4. Channels

wio already has the split needed: a pure function core
(`compile(rules, config, work, action, stage) -> (bundle, trace)`, where `work`
holds the parsed contract with its ancestors and their templates, for the
inherited sections, its descendants, for `@descendants`, and the stage's skill
files, for the bundle id) with a thin shell for file IO.

| Channel | What it does | Used for |
|---|---|---|
| `IN_PROCESS` (default) | Copies a fixture into the sandbox and calls the library with the git adapter replaced by the sandbox directory, so no process starts | Scenarios that read files and print, fast |
| `CLI` | Same temp repo, runs `wio` via `subprocess` | Error scenarios (exit 2 and the message on standard error), running outside a repository, exit codes (0 ok, 1 check failed, 2 usage mistake or `WioError`, 70 bug), `--json`, finding the config, `--output`, the `uvx` entry point, byte-stable output, environment-dependent behaviour such as session-id detection |

The CLI channel is the reference for acceptance: it is the command users and
skills run. The in-process channel is the fast copy of the same scenarios, so a
scenario that passes on one should pass on the other. Operation-shaped verbs of
the facade are layered on the test driver's `run(args)` as scenarios need them.

A test chooses channels with a marker, the pytest equivalent of an
annotation-based channel selector:

```python
@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
def test_check_fails_on_unknown_rule_reference(wio):
    # Given a stage that names a rule no ruleset has
    wio.config(stages=[stage("architecture", rules_include=["py.ARC999"])])
    wio.rules("py.ARC001")

    # When the rules are checked
    result = wio.rules_check()

    # Then the check fails and names the reference
    assert not result.ok
    assert "py.ARC999" in result.errors[0]
```

`conftest.py` parametrizes `channel` from the marker and falls back to a
`channel` fixture that returns `IN_PROCESS`. It marks the `CLI` case `slow`,
because it spawns the real command, so `make test` runs the in-process case and
`make slow` the CLI case of the same scenario. Future channels (MCP, a skill's
command sequence) are new test drivers; scenarios do not change.

`conftest.py` and `channels.py` hold the working version of this. Define
`channel` as a regular fixture with a default rather than relying on
`metafunc.fixturenames` alone. If BDD-style steps are ever added with
pytest-bdd, their fixtures are not visible when tests are generated.

## 5. Later: a DSL ruleset for users

The "Test DSL skill" in the wio design (ATDD/BDD, Dave Farley style, ports and
adapters) is a separate deliverable: an opt-in ruleset for users' projects.
wio's own acceptance tests are the reference implementation for it, so build
them well and extract the ruleset from what worked.
