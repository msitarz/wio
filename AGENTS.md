# AGENTS.md

wio (work-it-out) is a configurable, stage-gated workflow engine for coding
agents. Use the terms defined in [GLOSSARY.md](GLOSSARY.md) in code, docs and
commit messages. See `README.md` for the overview, `docs/README.md` for the
design and `tests/README.md` for the test strategy.

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
- `make audit`: check the locked dependencies for known vulnerabilities (needs
  network; uv's `audit` command is experimental).

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
- End every commit message with a record: a paragraph of `Wio-*` trailers that
  says which Work and stage the commit belongs to (see "Records" in
  [docs/concepts.md](docs/concepts.md#records)). Write `Wio-Work: none` when
  it belongs to no Work. Once `wio trailers` exists, append its output instead
  of writing the record by hand. The commit-msg hook checks the record.

  ```text
  Wio-Work: k3m9xq
  Wio-Action: deliver
  Wio-Stage: architecture
  Wio-Criteria: AC-1, AC-3
  ```

  | Trailer | Meaning |
  | --- | --- |
  | `Wio-Work` | The Work's id, or `none`. |
  | `Wio-Action` | The action, such as `define` or `deliver`. |
  | `Wio-Stage` | The stage the commit finishes. |
  | `Wio-Criteria` | Optional: the acceptance criteria it addresses. |
  | `Wio-Result` | Only for a review stage: `pass`, `fail` or `unknown`. |

- Never skip hooks (`--no-verify`).
- Commit when a step is done and checks pass. Keep commits small, one concern
  each.
- Changes with no design decisions need no Work contract. When in doubt, ask.
- Push and open pull requests only when asked. Never push to `main`: work on a
  branch, run `make check`, push the branch and use `gh pr create`.
- The pull request title is a Conventional Commit. Squash merging makes it the
  commit on `main`, and CI checks it.
- Fill in `.github/PULL_REQUEST_TEMPLATE.md` and delete every HTML comment
  from the body. Do not add records to the body: the Records workflow copies
  them from the commits to its end, so they survive the squash merge.
