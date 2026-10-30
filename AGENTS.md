# AGENTS.md

wio (work-it-out) is a configurable, stage-gated workflow engine for coding
agents. Use the terms defined in [GLOSSARY.md](GLOSSARY.md) in code, docs and
commit messages. See `README.md` for the overview and `tests/README.md` for the
test strategy.

## Commands

Use `make` for whole-project work (`make help` lists the targets) and `uv run`
for single tools. The checks are defined in `prek.toml` (hooks) and
`pyproject.toml` (tool settings), and the `make` targets only call them.

- `make install`: sync the environment (`uv sync --locked`) and install the git
  hooks (pre-commit and commit-msg). Run it once per clone.
- `make check`: run every hook and the fast tests on all files. Run it before
  declaring work done.
- `make lint`: every hook except pytest.
- `make test`: the fast tests, with the coverage gate (95%).
- `make build`: the slow packaging tests, which build the wheel and sdist and
  verify them.
- `make secrets`: scan the full git history with gitleaks.

Single tools, for quick feedback:

- `uv run pytest`: the fast tests in random order. Add `-p no:randomly` to
  debug, `-k name` to select, and `-m slow` to run the slow tests instead.
- `uv run ruff check --fix` and `uv run ruff format`: lint and format Python.
- `uv run pyrefly check`: strict type check of `src` and `tests`.
- `uv run complexipy src tests`: cognitive complexity.
- `uv run jscpd src tests`: duplicate code.
- `uv run rumdl check --fix`: lint and format Markdown.
- `uv add <package>` or `uv add --dev <package>`: change dependencies. Never
  edit `uv.lock` by hand.

## Code conventions

- Start every Python file with `# SPDX-License-Identifier: Apache-2.0` as the
  first line (second after a shebang). Ruff enforces it (`CPY001`).
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
