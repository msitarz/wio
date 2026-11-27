# AGENTS.md

wio (work-it-out) is a configurable, stage-gated workflow engine for AI agents.
Use the terms in [GLOSSARY.md](GLOSSARY.md) (nearest `GLOSSARY.md` wins;
nearer `README.md` adds to farther ones). See [README.md](README.md) for the
overview, [docs/workflow.md](docs/workflow.md) for this repo's workflow,
[src/wio/README.md](src/wio/README.md) for the architecture, and
[tests/README.md](tests/README.md) for the test strategy.

## Starting a session

- For a Work stage, run `wio context <work> <action> <stage>` first and again
  after compaction; it delivers the contract, stage goal/skill, and rules.
- For small changes with no design decisions (no Work contract), run
  `wio rules list` (or `--path <file>`) to see the applicable coding and
  writing rules.

## Commands

Use `make` (`make help` lists all targets) and `uv run` for single tools:

- `make install`: sync the environment (`uv sync --locked`) and install git
  hooks.
- `make check`: run every hook (`ruff`, `pyrefly`, `complexipy`, `tach`,
  `jscpd`, `rumdl`, `typos`) and the fast tests (95% coverage gate). Run before
  declaring work done.
- `make slow`: slow subprocess and packaging tests (CI runs this).
- `uv add [--dev] <package>`: change dependencies; never edit `uv.lock` by hand.

## Git and pull requests

- Put new git worktrees in `.claude/worktrees/`.
- Follow Conventional Commits and end every commit with `wio trailers` output
  (`Wio-Work: none` when a commit belongs to no Work). Never skip hooks
  (`--no-verify`).
- Keep commits small, one concern each, and commit once checks pass.
- Never push to `main`: branch, run `make check`, push, and use `gh pr create`
  with a Conventional Commit title.
- Fill in `.github/PULL_REQUEST_TEMPLATE.md`, delete every HTML comment, and do
  not add `Wio-*` records to the PR body (the Records workflow copies them from
  commits).
