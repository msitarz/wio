<!-- wio
id = "9wbqyb"
template = "feature.draft"
roots = []
depends_on = ["ew60gw"]
-->

# The wio command line

## Purpose

Every subcommand of wio needs one entry point that dispatches to it, gives it
the adapters it consumes and follows one exit-code contract, before the first
subcommand can run.

## Intent

From the interview of 2026-11-03, started while defining the config Work
(hwn995). Decisions are made unless marked open.

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
- The config Work depends on this one; this one depends on promote-architecture
  (ew60gw), so the architecture changes below are made in `src/wio/README.md`
  and `tach.toml`, not by amending the retired foundation contracts.

**Decided.**

- Bare `wio` prints the description (the installed package's `Summary`), then
  the usage with the subcommands, to standard output, and exits 0. `--help`
  shows the same and `--version` prints the version.
- Every command module keeps its heavy imports lazy (`lazy import`, tested on
  Python 3.15.2: importing such a module loads none of them), so `wio.cli`
  imports all command modules to build the parser. A slow test guards it: after
  bare `wio`, no implementation module of any component is loaded.
- A component exposes a port-free `describe()` (name, help, `configure`) and a
  factory taking the ports it consumes, such as `command(settings=...)`, which
  returns the object whose `run` has them bound. `wio.cli` has one explicit
  wiring function per command, builds only the adapters that command needs, and
  takes the platform as a parameter (default `sys.platform`) so tests cover each
  per-platform adapter branch on one machine.
- Errors: a new `wio.errors` module holds `WioError` and the errors shared by
  components; a package adds its own `errors.py` (such as
  `wio.contracts.errors`) only when it has an error of its own, extending
  `WioError`. Every package, `wio.models` and `wio.env` included, may import
  `wio.errors`, which imports nothing from `wio`. `wio.cli` catches `WioError`,
  prints `error: <message>` to standard error and exits 2; any other exception
  is a bug: traceback and exit
  70. A failed check is a result, never an exception. Usage and configuration
  errors share code 2 (the wording is in the scope document, the testing
  README and two docstrings, not in a Work).
- `Settings.load` raises a `WioError` subclass instead of `ValueError`.
- Shape: a small parent with two leaves: `wio.errors` (module, tach, the
  architecture document, glossary), then the command line (dispatch, bare, help,
  version, exit codes, the describe/factory split, the import guard, the
  platform wiring, removal of the strict `xfail` of the bare scenario, and a
  line for this Work in the scope document).
- `--json` is an option of each command, declared by its `configure`, as in
  `uv`; an acceptance test checks that every command that offers it writes one
  JSON document to standard output and nothing else.
- Standard output carries what the command was asked for, a `check`'s findings
  included. Standard error carries diagnostics about the run itself and the
  plain-text `WioError` message, also in `--json` mode. No color and no pager
  in v0.1.

**Open:** nothing yet; the criteria of the two leaves are next.
