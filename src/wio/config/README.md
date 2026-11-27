# `wio.config`

The component behind `wio config` (`list`, `show`, `check`) and the
`Settings` loader consumed by every other command. Local terms are in
[GLOSSARY.md](GLOSSARY.md).

## Package invariants

- **One validated `Config`.** [`loader.py`](loader.py) reads
  `.agents/wio/config.toml`, applies defaults, and runs [`checks.py`](checks.py)
  so every command either receives a valid `Config` or exits with a `WioError`.
- **Unknown keys are errors.** [`shape.py`](shape.py) rejects any key the
  schema does not declare, catching typos at `wio config check`.
- **Config-only checks.** Checks that need rule files or template files belong
  to `wio rules check` and `wio templates check`, not here.

## Log settings

[`log_settings.py`](log_settings.py) validates `[log]` settings, including the
environment variables by which
[session identification](../log/README.md#harness-session) recognizes a
harness.

## Finding a skill

[`skills.py`](skills.py) resolves a stage's skill directory across configured
`[skills] paths`, `.agents/skills`, and `.claude/skills` (never the user's
home), shared by `wio config check` and `wio context`.

## Modules

- Loading & schema: [`loader.py`](loader.py), [`settings.py`](settings.py),
  [`schema.py`](schema.py), [`shape.py`](shape.py), [`keypath.py`](keypath.py).
- Checks: [`checks.py`](checks.py), [`pipelines.py`](pipelines.py),
  [`paths.py`](paths.py), [`selection.py`](selection.py),
  [`log_settings.py`](log_settings.py), [`skills.py`](skills.py),
  [`messages.py`](messages.py).
- Command & tests: [`command.py`](command.py), [`listing.py`](listing.py),
  [`report.py`](report.py), [unit tests](../../../tests/unit/config/).
