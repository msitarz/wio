<!-- wio
id = "9wbqyb"
template = "feature.draft"
roots = []
depends_on = []
-->

# The wio command line

## Purpose

Every subcommand of wio needs one entry point that dispatches to it, gives it
the adapters it consumes and follows one exit-code contract, before the first
subcommand can run.

## Intent

Seeded by the interview for the config Work (hwn995), 2026-11-03. Nothing here
has been defined yet; the cli interview comes first when this Work is defined.

- Today `wio.cli.main` ignores its arguments and returns 0. The foundation
  Work left "the Work of the `cli` package" as a non-goal, and the scope
  document's order of work does not list it, so the scope document needs a line
  for it.
- It is the composition root: argparse subparsers, one per command, each bound
  with a lazy import; it gives each command the implementations of the ports it
  consumes (the adapters of `wio.io` and `wio.env`).
- It owns the exit-code contract (0 success, 1 a failed check, 2 a usage or
  configuration error), deterministic output, a machine-readable form where a
  tool consumes output, and fast start-up.
- The bare `wio` command prints its description.
- The config Work depends on this one.
