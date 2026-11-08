# wio test strategy

How wio is tested. Written for a coding agent or human starting work in the wio
repo. It covers the test layers, the directory layout and the conventions.
Examples are sketches.

## 1. Principles

- **Fast by default.** `uv run pytest` runs the fast tests, and `make slow`
  runs the slow ones.
- **Start small.** Add helpers and vocabulary only when a test needs them.
  Delete tests and helpers that have no observed failure behind them.

## 2. Test layers

| Layer | Location | Use for | Do not use for |
|---|---|---|---|
| Unit | `tests/unit/` (mirrors `src/wio/`) | Internals: directive grammar (parametrized tables), the pure `compile(...)` core, id generation, parsers | Cross-module behaviour |
| Integration | `tests/integration/` (mirrors `src/wio/`) | Code with something real behind it: an adapter on real git or a real disk, the process's working directory and environment, a fresh interpreter (what an import loads), the installed command | Behaviour a user relies on (acceptance); input tables (unit) |
| Tooling | `tests/tooling/` | The repository's own configuration, layout and hygiene as its tools see them: lint rules probed with `ruff`, what git ignores, the stub rules of the ports, that the sources and the sample config agree with the models | The behaviour of wio |
| Acceptance | `tests/acceptance/` (mirrors features) | Behaviour a user or skill relies on: rule selection, contract check results, config validation, record checks, exit codes | Exhaustive input tables, flag parsing details |
| Golden | `tests/golden/` (expected files only) | Byte-stable output (context bundles, rendered templates) | Anything with timestamps or ordering that is not deterministic |

The `tests/packaging/` and `tests/scripts/` directories are two more groups,
for the built package and for the scripts of the repository.

**Which group a test belongs to.** Ask in this order, and take the first yes:

1. Does it assert on what a user or a skill sees, through the DSL or the CLI
   channel? It is an acceptance test: one acceptance criterion of a Work
   contract, one scenario. Only when you write one, read the [acceptance test
   guide](acceptance/README.md).
2. Does it check a tool's configuration or the files of the repository, such as
   a lint rule, an ignored file or the layout of the sources? It is a tooling
   test.
3. Does something real stand behind the code it calls: git, files whose state it
   depends on, the working directory or the environment of the process, a fresh
   interpreter, the installed command? It is an integration test, however fast
   it runs.
4. Otherwise one module is tested with its collaborators replaced, and it is a
   unit test. A `tmp_path` directory that only gives the code an inert input
   does not make a unit test an integration test; a test that asserts on what
   the real disk does does.

A file that mixes the two is split: the unit tests stay in `tests/unit/...`, and
the rest moves to the same path under `tests/integration/` or `tests/tooling/`.

**Markers.** Every directory under `tests/` that holds tests is a group, and its
marker is its name: `unit`, `integration`, `acceptance`, `tooling`, `packaging`
and `scripts`. `tests/conftest.py` sets the marker from the path, so
`pytest -m integration` runs that group whatever its tests are called. A test
outside every group, or marked with another group's name, fails collection. A
new group is a directory, a registered marker and a module in `tach.toml`.

`slow` is separate from the group. It says that a test spawns a subprocess or
builds the package, and the default run leaves it out. An integration test with
only a temporary directory is not slow and runs by default.

Not covered here: LLM behaviour of skills (`wio-define`, and the review skills
that come later). That
belongs to `wio-eval`. Acceptance tests cover the deterministic engine under the
skills, for example the command sequence a skill runs.

## 3. Directory layout

```text
tests/
├── conftest.py             # register_assert_rewrite, shared options and markers,
│                           # and the `sandbox` fixture
├── sandbox.py              # Sandbox: the directory and environment of a test
├── support.py              # helpers tests share: git in a sandbox, a fake `Environment`
├── unit/                   # mirrors src/wio/
├── integration/            # mirrors src/wio/: the code with something real behind it
├── tooling/                # tests of the repository's configuration and hygiene
├── acceptance/             # the DSL, the test drivers and the scenarios
├── golden/                 # expected bundle bytes
├── packaging/              # build the wheel and sdist and inspect them (slow)
├── scripts/                # tests of the scripts in the top-level scripts/
└── fixtures/               # static sample repos, example templates, rulesets
```

`tach check` enforces the dependency direction in `tach.toml`: `tests.sandbox`
and `tests.support` depend on nothing else in `tests`, so any group may use
them; the acceptance setup imports only `wio.cli` and `wio.io` and its own
parts; `tests/scripts` imports `scripts` and the shared helpers, never the
acceptance setup; the integration tests import the adapters and the shared
helpers, never the unit tests, so a fake that both use lives in `tests.support`;
the tooling tests import only the acceptance setup they check; and nothing in
`src` or `scripts` imports `tests`. A new group of tests needs an entry there.

## 4. What acceptance tests do not cover

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

## 5. pyproject configuration

```toml
[tool.pytest]
testpaths = ["tests"]
pythonpath = ["."]
addopts = ["--import-mode=importlib", "-m", "not slow"]
markers = [
    "channels(*channels): run once per listed Channel",
    "slow: spawns a real subprocess (git, the CLI) or builds the package",
    "unit: tests/unit, one module with its collaborators replaced",
    "integration: tests/integration, code with something real behind it",
    "acceptance: tests/acceptance, behaviour asserted through the DSL",
    "tooling: tests/tooling, the repository's configuration and hygiene",
    "packaging: tests/packaging, the built wheel and sdist",
    "scripts: tests/scripts, the scripts of the repository",
]
```

`pythonpath = ["."]` allows `from tests.acceptance.dsl.wio import Wio` without
`__init__.py` files everywhere. `addopts` deselects the slow tests, so
`uv run pytest` runs the fast set and `uv run pytest -m slow` the slow one.

## 6. Conventions

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
- A test lives in the group its subject asks for (see section 2) and never
  carries another group's marker by hand; the directory sets it.
- Use `tmp_path` for every repo; never write outside it. The `Sandbox` sets
  `WIO_HOME` inside `tmp_path` so tests never touch the real Wio home, and it
  gives git an empty global config, no system config, a ceiling at `tmp_path`,
  no variables that aim it at another repository, and a fixed identity, so a
  developer's own git setup cannot change a result.
- The event log is redirected per test by `WIO_HOME` (the log must never block
  a command).
- No sleeps. No timestamps in compared output.

## 7. Order of work

1. Dataclass models with explicit validation, and the config loader (unit
   tests).
2. `tests/acceptance/` skeleton: `Wio` facade, builders, in-process test driver,
   CLI test driver, with the bare `wio` scenario in `tests/acceptance/cli/`,
   then targeting `wio config check`.
3. `wio contracts new / list / check`, developed against the DSL.
4. `wio trailers` and `wio trailers check`.
5. `wio rules check` and `wio context`, with golden tests.
6. `wio log`, with the `context` and `review` events.
7. Add the CLI channel to the scenarios where exit codes, `--json` or
   environment matter.
