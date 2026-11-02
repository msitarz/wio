<!-- wio
id = "zpnbj3"
template = "feature.draft"
roots = []
depends_on = []
-->

# v0.1 foundation

<!--
A draft is working space while an intent is captured. Its define stage
shapes the intent into a feature.leaf or a feature.parent contract and switches
`template`; the Intent section does not carry over.
-->

## Purpose

Every v0.1 component needs a fixed place, a typed boundary to the others and a
test setup before any of them is built, so that each can be delivered alone.

## Intent

Interview notes from the driver, 2026-11-02.

- No code exists yet and the v0.1 scope is clear, so the architecture can be
  laid down first as a skeleton that drives the later Works.
- Outcome: a prepared `src/wio` layout, with `.pyi` stubs for the Protocols
  between components and for the shared types, a `tach` configuration that
  enforces the boundaries, and a `tests/` setup with the acceptance DSL and one
  `xfail` example that runs bare `wio`.
- The stubs say how components talk to each other, not how a subcommand works
  inside. The layout need not be complete.
- Ports and adapters, one adapter per port for now. Unit tests use fakes,
  integration tests pair a module with a fake adapter and then with its real
  adapter, acceptance tests run the command end to end.
- Packages: `wio.models` (shared types), `wio.formats` (pure codecs between text
  and models), `wio.io` (ports and adapters for the filesystem, stdio, git and
  the environment), one package per component, and `wio.cli` as the composition
  root. Ports are owned by the consumer, so components never import each other.
- Each component exposes a command object for an argparse subparser. `cli` binds
  them with Python 3.15 `lazy from ... import`, so one subcommand loads only its
  own module.
- Tach runs as a prek hook, so `make lint`, `make check` and CI cover it. It
  must count `TYPE_CHECKING` imports and cannot see imports inside `.pyi` files.
  It constrains `src/wio` only.
- A minimal `wio` console script is in scope. Bare `wio` should print the
  project description and exit 0; the example is `xfail(strict=True)` on both
  channels, the CLI case marked slow.
- Verification is `tach check`, `pyrefly check` and `make check`. No test proves
  that tach rejects a forbidden import.
- `docs/v0.1-scope.md` and `tests/README.md` are updated to match.
- Shape: a parent with three leaves, the architecture skeleton, tach
  enforcement and the test DSL. Tach and the test DSL depend on the skeleton.
