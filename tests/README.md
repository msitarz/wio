# wio test strategy

How wio is tested. Written for a coding agent or human starting work in the wio
repo. It covers the test layers, the acceptance-test DSL, the directory layout
and the conventions. Examples are sketches.

## 1. Principles

- **Acceptance tests speak the domain's language.** A test says
  `wio.context(work_id=..., action=..., stage=...)`, never
  `subprocess.run(["wio", "context", ...])`. Only drivers know how
  wio is reached.
- **One acceptance criterion = one scenario.** Contract ACs are independently
  assessable; each maps to one DSL scenario.
- **Drivers return data and never assert.** Tests assert on the returned data
  with plain `assert`. That keeps drivers identical across channels and lets
  pytest's assertion introspection work.
- **Fast by default.** `uv run pytest` runs the in-process channel. The CLI
  channel is opt-in per test.
- **Start small.** One DSL facade, one in-process driver, one CLI driver. Add
  vocabulary only when a scenario needs it. Delete tests and helpers that have
  no observed failure behind them.

## 2. Test layers

| Layer | Location | Use for | Do not use for |
|---|---|---|---|
| Unit | `tests/unit/` (mirrors `src/wio/`) | Internals: directive grammar (parametrized tables), the pure `compile(...)` core, id generation, parsers | Cross-module behaviour |
| Acceptance | `tests/acceptance/` (mirrors features) | Behaviour a user or skill relies on: rule selection, contract check results, config validation, record checks, exit codes | Exhaustive input tables, flag parsing details |
| Golden | `tests/golden/` (expected files only) | Byte-stable output (context bundles, rendered templates) | Anything with timestamps or ordering that is not deterministic |

Not covered here: LLM behaviour of skills (`wio-define`, and the review skills
that come later). That
belongs to `wio-eval`. Acceptance tests cover the deterministic engine under the
skills, for example the command sequence a skill runs.

## 3. Directory layout

```text
tests/
├── conftest.py             # register_assert_rewrite, shared options and markers
├── unit/                   # mirrors src/wio/
├── acceptance/
│   ├── conftest.py         # `wio` fixture, channel parametrization, assertrepr hook
│   ├── channels.py         # Channel enum
│   ├── dsl/
│   │   ├── wio.py          # Wio facade: config(), rule(), work(), context(), trailers(), check()
│   │   ├── builders.py     # minimal-valid config.toml, contract, rule, template
│   │   └── results.py      # Bundle, CheckResult, ...
│   ├── drivers/
│   │   ├── base.py         # WioDriver Protocol
│   │   ├── in_process.py   # calls the library
│   │   └── cli.py          # subprocess; parses --json; reads exit codes
│   └── config/ contract/ rule/ context/ trailers/ log/   # one folder per v0.1 feature
├── golden/                 # expected bundle bytes
├── packaging/              # build the wheel and sdist and inspect them (slow)
├── scripts/                # the repository's own scripts, such as records.py
└── fixtures/               # static sample repos, example templates, rulesets
```

Acceptance folders follow the feature tree (`config`, `contract`, `rule`,
`context`, `trailers`, `log`), so coverage gaps are easy to see. The DSL lives
inside `tests/acceptance/` because nothing else uses it yet; promote it to its
own package only when a second consumer (for example `wio-eval`) needs it.

## 4. The DSL

### 4.1 Layers

| Layer | Role |
|---|---|
| Scenario (test function) | States what happens, in domain terms |
| `Wio` facade | Domain verbs: `config`, `rule`, `work`, `context`, `trailers`, `check`, `contract_new`. Applies defaults. |
| Builders | Produce a minimal valid repo state; tests override only what they are about |
| `WioDriver` (Protocol) | Narrow interface: run an operation against a prepared temp repo, return a result object |
| Drivers | In-process and CLI implementations of the Protocol |

### 4.2 Builders matter most

The config, contract metadata, rule files, templates and roots are fixtures
that interact. Without builders every test hand-writes TOML and markdown, and
any format change breaks every test. The `Wio` facade starts from a minimal
valid repo (one root, one action, one stage, one type with its entry template)
and each
scenario changes only the parts it tests.

```python
def test_reviewer_only_rules_never_reach_the_author_stage(wio):
    wio.config(stages=[stage("architecture", tags=["architecture", "testing"])])
    wio.rule("ARC001", tags=["architecture", "review"])
    wio.work("feature", id="k3m9xq")

    bundle = wio.context(work_id="k3m9xq", action="deliver", stage="architecture")

    assert "ARC001" not in bundle
```

### 4.3 Results and assertions

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
`tests/acceptance/conftest.py`. The drivers fill `trace` by running
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

Exception: if a channel is asynchronous (a future MCP or HTTP driver), use a
polling helper such as `eventually(...)`, since a bare `assert` cannot wait.

## 5. Channels

wio already has the split needed: a pure function core
(`compile(rules, config, contract_metadata, action, stage) -> (bundle, trace)`)
with a thin shell for file IO.

| Channel | What it does | Used for |
|---|---|---|
| `IN_PROCESS` (default) | Builds a temp repo, calls the library | Most scenarios, fast |
| `CLI` | Same temp repo, runs `wio` via `subprocess` | Exit codes (0 ok, 1 check failed, 2 usage/config error), `--json`, finding the config, `--output`, the `uvx` entry point, byte-stable output, environment-dependent behaviour such as session-id detection |

A test chooses channels with a marker, the pytest equivalent of an
annotation-based channel selector:

```python
@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
def test_check_fails_on_unknown_tag(wio):
    wio.config(tags=["architecture"])
    wio.rule("ARC001", tags=["nonexistent"])

    result = wio.rule_check()

    assert not result.ok
    assert "nonexistent" in result.errors[0]
```

`conftest.py` parametrizes `channel` from the marker and falls back to a
`channel` fixture that returns `IN_PROCESS`. Run the shared scenarios against
both channels only where the CLI wiring matters. Future channels (MCP, a skill's
command sequence) are new drivers; scenarios do not change.

```python
def pytest_generate_tests(metafunc):
    marker = metafunc.definition.get_closest_marker("channels")
    if marker:
        metafunc.parametrize("channel", marker.args, ids=[c.value for c in marker.args])


@pytest.fixture
def channel() -> Channel:
    return Channel.IN_PROCESS
```

Define `channel` as a regular fixture with a default rather than relying on
`metafunc.fixturenames` alone. If BDD-style steps are ever added with
pytest-bdd, their fixtures are not visible when tests are generated.

## 6. What is not tested through the DSL

- **Directive grammar** (`required`, `items`, `pattern`, `inherit`):
  parametrized unit tables, many small inputs with expected errors.
- **Bundle bytes**: golden tests. Identical inputs must give identical bytes.
  Reviewer and author bundles must differ. Update goldens deliberately and
  review the diff.
- **External tools**: wio does not lint Markdown, so its tests never need
  `rumdl` or a diagram renderer. Where a scenario needs git (for example a
  commit message with records), create a real repository in `tmp_path`.
- **Flag parsing details**: ordinary unit tests.
- **Skill behaviour**: `wio-eval`.

## 7. pyproject configuration

```toml
[tool.pytest]
testpaths = ["tests"]
pythonpath = ["."]
addopts = ["--import-mode=importlib"]
markers = [
    "channels(*channels): run once per listed Channel",
    "slow: spawns the real CLI",
]
```

`pythonpath = ["."]` allows `from tests.acceptance.dsl.wio import Wio` without
`__init__.py` files everywhere. Run `uv run pytest` for the fast set,
`uv run pytest -m "not slow"` if CLI runs become slow.

## 8. Conventions

- Test names state the behaviour:
  `test_reviewer_only_rules_never_reach_the_author_stage`.
- Every test has `# Given`, `# When` and `# Then` comments, in that order. Each
  comment describes its section in the domain's terms ("When its problems are
  computed"), not the code ("When calling `message_problems`"), so it stays
  true when names change. Assign the result in the When section and assert on
  it in the Then section, rather than computing inside the `assert`. A section
  may be empty only when there is nothing to put in it, and its comment stays
  (`# Given no setup`).

  ```python
  def test_a_message_without_a_record_is_reported() -> None:
      # Given a commit message with prose and no record
      message = _message("docs: x", "Body.")

      # When its problems are computed
      problems = records.message_problems(message)

      # Then the only problem says how to add a record
      assert problems == ["no Wio-* record; add one, or `Wio-Work: none`"]
  ```

- A test that spawns a subprocess (git, the CLI) or builds the package is
  marked `slow`. `make slow` runs those tests, and CI runs that target.
- Use `tmp_path` for every repo; never write outside it. Set `HOME` and the
  XDG data dir inside `tmp_path` so tests never touch the real
  log or config.
- Event log is disabled or redirected per test (the log must never block a
  command).
- No sleeps. No timestamps in compared output.
- A test that needs more than three builder overrides is a sign the builder
  default is wrong or the scenario is testing two things.

## 9. Order of work

1. Dataclass models with explicit validation, and the config loader (unit
   tests).
2. `tests/acceptance/` skeleton: `Wio` facade, builders, in-process driver, CLI
   driver, targeting `wio config check`.
3. `wio contract new / list / check`, developed against the DSL.
4. `wio trailers` and `wio trailers check`.
5. `wio rule check` and `wio context`, with golden tests.
6. `wio log`, with the `context` and `review` events.
7. Add the CLI channel to the scenarios where exit codes, `--json` or
   environment matter.

## 10. Later: a DSL ruleset for users

The "Test DSL skill" in the wio design (ATDD/BDD, Dave Farley style, ports and
adapters) is a separate deliverable: an opt-in ruleset for users' projects.
wio's own acceptance tests are the reference implementation for it, so build
them well and extract the ruleset from what worked.
