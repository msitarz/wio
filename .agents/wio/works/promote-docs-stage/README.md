<!-- wio
id = "qg33gf"
template = "feature.draft"
roots = []
depends_on = []
-->

# The promote-docs stage

## Purpose

A delivered Work's lasting rules, reasons and diagrams need a stage that moves
them into the documents next to the code, so the contract can be retired
instead of drifting from what later Works change.

## Intent

From the interview of 2026-11-03. Decisions are made unless marked open. It is
a change of this repository's config and rules; the engine does not know it.

- **A stage `promote-docs`**: carry the lasting rules, reasons and diagrams of
  the Work into the `README.md` and `GLOSSARY.md` of the directories the Work
  touched. A `README.md` covers its directory and descendants and owns only
  its level, linking instead of copying; unlike a glossary, a nearer one adds
  to a farther one and does not override it.
- **A gate `docs-review`**: a fresh session judges whether the docs lost any
  guarantee the contract stated. `judge = "human"`, because retiring a
  contract leaves history as its only copy.
- **Retirement is the driver's decision**, made in the last commit of the stage
  and never automatic: the contract is deleted only when the driver confirms it
  is spent. A parent is retired after its system review, with its children.
- **Placement**: the last pair of stages of `deliver` for leaves and parents,
  as a preset entry. It differs from `ratify`, which brings the contract up to
  what was built; this brings the docs up to what the contract guarantees. A
  Work may override its `deliver` pipeline, as promote-architecture does with
  `["promote-docs", "docs-review"]`.
- **A small `docs` ruleset** with tags (`docs`, probably `promote`) added to
  the config's vocabulary: what belongs in a README, diagrams drawn from
  verified source (VIS002), link instead of copying (CON008).
- **Open:** which root the `docs` ruleset binds to (the stage selects the
  Work's roots, while the docs sit under them or under `repo`), the exact
  rules, and whether the existing `contract-upkeep` rules change.
