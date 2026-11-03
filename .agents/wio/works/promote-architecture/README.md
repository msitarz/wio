<!-- wio
id = "ew60gw"
template = "feature.draft"
roots = []
depends_on = ["qg33gf"]
-->

# Promote the architecture

## Purpose

The rules of the architecture are stated only in the contracts of the delivered
v0.1 foundation Work, which later Works will change, so agents that read a
finished contract as current truth drift from the code.

## Intent

From the interview of 2026-11-03. Decisions are made unless marked open.

- **Retire the foundation Work** (zpnbj3 and its three children) once what only
  it states has a home next to the code. Git history keeps the contracts, and a
  removed Work that others depend on is read from the history. Only
  `docs/v0.1-scope.md` (two links) and a comment in `tach.toml` refer to it.
- **Docs live where they belong**, like `GLOSSARY.md`: a `README.md` covers the
  directory it is in and its descendants, and a nearer one adds to a farther
  one and does not override it, unlike a glossary, where the nearest wins.
  `src/wio/README.md` is the architecture of `wio`; each component and layer may
  have its own `README.md` for what is true at its level, linking instead of
  copying. A `README.md` without a `wio` metadata block is not a Work.
- **What must be promoted**, because no tool checks it: the dependency
  direction; port ownership and the reasons for the exceptions (`wio.io` and
  `wio.env` own their ports, `wio.ports` is shared); no component imports
  another; one adapter per port, and fakes under `tests`; the stub lifecycle;
  access to the outside only through ports; counting `TYPE_CHECKING` imports;
  which checks verify what (tach, pyrefly, the architecture review); and the
  after-state diagram.
- **Packaging.** The wheel excludes `**/GLOSSARY.md` (`pyproject.toml`
  `wheel-exclude`) and a packaging test checks it; `README.md` files under
  `src/wio` need the same exclusion and check.
- **How it is delivered**: through the promote-docs stage (Work qg33gf), by
  overriding its `deliver` pipeline to `["promote-docs", "docs-review"]`, so
  this Work is the stage's first use. It depends on that Work.
- Work that follows (the cli Work, `wio.errors`) depends on this one, and
  changes the architecture document instead of amending a contract.
