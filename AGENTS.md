# AGENTS.md

wio (work-it-out) is a skill-based engine for coding agents: contract, types,
skeleton, implementation. See `tests/README.md` for the test strategy.

## Commands

Run everything through `uv`.

- `uv sync`: create or update the environment.
- `uv run prek run -a`: run every check on every file (same as the commit
  hooks).
- `uv run pytest`: run tests in random order. Add `-p no:randomly` to debug.
- `uv run pytest --cov`: run tests with the coverage gate (95%).
- `uv run ruff check --fix` and `uv run ruff format`: lint and format Python.
- `uv run pyrefly check`: strict type check of `src` and `tests`.
- `uv run complexipy src tests`: cognitive complexity.
- `uv run jscpd src tests`: duplicate code.
- `uv run rumdl check --fix`: lint and format Markdown.
- `uv add <package>` or `uv add --dev <package>`: change dependencies. Never
  edit `uv.lock` by hand.

## Code conventions

- Annotate everything, tests included. Run `pyrefly` before declaring done.
- Write a Google-style docstring for every module, class and function, private
  helpers too. Ruff enforces it only for public names.
- A `.pyi` stub carries a docstring for each item. Stubs are the architecture
  spec, so say what each item guarantees.
- Write output with `sys.stdout`, not `print`.
- Keep functions small: McCabe complexity 10, cognitive complexity 7, 20
  statements, 3 boolean operands per `if`. Prefer `match` with named guards over
  long `if` chains, and model variants as algebraic data types.
- Python lines are 88 columns. Markdown lines are 80.
- Fix the cause when a check fails. Never weaken a test or loosen a rule to get
  green. If a rule seems wrong, say so and propose a config change.

## Workflow

- Commit messages follow Conventional Commits. The commitizen hook checks them.
- Never skip hooks (`--no-verify`).
- Commit when a step is done and checks pass. Keep commits small, one concern
  each.
- Changes with no design decisions need no Work contract. When in doubt, ask.
