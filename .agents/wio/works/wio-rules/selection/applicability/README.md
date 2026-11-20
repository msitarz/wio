<!-- wio
id = "5yb4tz"
template = "feature.leaf"
roots = ["wio"]
depends_on = ["cm25z9"]
-->

# Applicability

## Purpose

The layers say which rules are selected but not which apply where, so nothing
can tell a rule that a stage's roots cut from one that a layer removed, or give
`wio context` and `wio rules list` the same decision for a rule.

## Goals

- Every rule of every ruleset gets one `Decision`: included with the roots it
  applies to, or out with the reason that decided it.
- A selected rule applies when its ruleset is root-independent or reached by a
  selected root, and the roots are not applied when none are given.
- One `select` serves every view of a listing and every consumer of a selection.

## Non-Goals

- Applying the layers and finding the rulesets that a root reaches, which
  `cm25z9` does.
- Finding the roots of a Work, a stage or a file, which `ndwemw` does.
- Printing or explaining a selection, which `wio rules list` does.
- Giving a selection to `wio context` and `wio trailers` through their ports,
  which `9pfyfe` does with this `select`.

## Assumptions

### A-1

When several layers touched a rule, the reason it is out is the last layer that
removed it, so a rule that the root added and the stage removed is excluded by
the stage, and one that the stage removed and the veto removed again is vetoed.

### A-2

A rule that the layers selected is cut by the roots only after the layers have
decided, so a rule that a layer removed is never reported as cut by the roots.

### A-3

A rule of a root-independent ruleset applies to every root whether or not a root
also reaches its ruleset, which `wio rules check` reports as an error, so its
`Decision` has no roots and `root_independent` true in both cases.

## Mechanisms

The names of the types and the functions below are provisional, except that the
field sets of `Decision` and `Reason` are required, because `9pfyfe`, `fjvj3x`
and `qxfpg9` read them.

- **`Decision`** — a frozen dataclass in `wio.models.rules` with
  `included: bool`, `roots: tuple[str, ...]`, `root_independent: bool`,
  `effects: tuple[LayerEffect, ...]` and `reason: Reason | None`; it replaces
  the stub, and `Selection` is the `Mapping[Rule, Decision]` of the same module.
  `root_independent` is the setting of the rule's ruleset in the config, for
  every rule, included or out, and `roots` is empty for a rule that is out.
- **`Reason`** — frozen, with
  `kind: Literal["not-selected", "excluded", "vetoed", "cut-by-roots"]` and
  `layer: Literal["root", "stage"] | None`, which is set for `excluded` and
  none for the others.
- **`LayerEffect` and `Routes`** — move to `wio.models.rules` from `cm25z9` and
  `cyeth5`, because a `Decision` holds them and a model may not import a
  component; `Origin` of `1gs341` also holds `Routes`.
- **`select(roots, stage, config, rulesets) -> Selection`** — the function in
  `wio.rules`, not the method of the same name of `RuleSelector`, where `roots`
  is a `tuple[str, ...]` or `None` and `stage` is a name or `None`; it calls
  `apply_layers` of `cm25z9` and decides each rule.

## Acceptance criteria

### **AC-1** A selected rule applies where its ruleset is reached

With roots given, a selected rule is included when its ruleset is
root-independent or reached by a selected root, and is cut by the roots
otherwise.

#### Reached, unreached and independent

- **Given** a ruleset `demo` with `ARC001`, a ruleset `web` with `WEB001`, and a
  ruleset `process` with `FIX001` whose config setting is
  `root_independent = true`; a root `api` with `rule_presets = ["demo.all"]`, so
  that no root reaches `web`; and a stage `s` whose `rules_include` has
  `web.WEB001` and `process.FIX001`.
- **When** `select` runs for the roots `("api",)` and the stage `s`.
- **Then** `demo.ARC001` is included with the roots `("api",)`, `web.WEB001` is
  out with the reason `cut-by-roots`, and `process.FIX001` is included with
  `root_independent` true and no roots.

#### A root-independent ruleset that a root reaches

- **Given** the same repository with `process.all` added to the rule presets of
  `api`.
- **When** `select` runs for the roots `("api",)` and the stage `s`.
- **Then** `process.FIX001` is included with `root_independent` true and no
  roots, as before.

### **AC-2** The reason is the last layer that removed the rule

A rule that is out has the reason of the last layer that removed it,
`not-selected` when no layer touched it, and `cut-by-roots` only for a rule that
the layers kept.

#### Each reason

- **Given** a ruleset `demo` that declares `ARC` and `PAY` and holds `ARC001`,
  `ARC002`, `ARC003`, `PAY001`, `PAY002` and `PAY003`, with a rule preset
  `recommended` that includes `ARC` and excludes `ARC001`; a ruleset `web` with
  `WEB001`; a root `api` with `rule_presets = ["demo.recommended"]`; and a stage
  `s` with `rules_include = ["demo.PAY001", "demo.PAY002", "web.WEB001"]` and
  `rules_exclude = ["demo.ARC002", "demo.ARC003"]`, with
  `rules_always_include = ["demo.ARC003"]` and
  `rules_always_exclude = ["demo.PAY001"]`.
- **When** `select` runs for the roots `("api",)` and the stage `s`.
- **Then** `demo.PAY003` is out as `not-selected`, `demo.ARC001` as `excluded`
  with the layer `root`, `demo.ARC002` as `excluded` with the layer `stage`,
  `demo.PAY001` as `vetoed`, and `web.WEB001` as `cut-by-roots`, while
  `demo.ARC003`, which the stage removed and `rules_always_include` added back,
  and `demo.PAY002` are included, and every decision carries the effects of its
  layers.

### **AC-3** Without roots nothing is cut

When the roots are not applied, no rule is cut by the roots, and a rule that is
not root-independent is listed with the roots of the config that reach its
ruleset.

#### Roots not applied

- **Given** the repository of AC-1 with a second root `ui` that has no rule
  presets.
- **When** `select` runs for `None` roots and the stage `s`, and for `None`
  roots and `None` stage.
- **Then** in the first `demo.ARC001` is not selected, `web.WEB001` is included
  with no roots, `process.FIX001` is included with `root_independent` true, and
  no reason is `cut-by-roots`; in the second only the always fields apply, so
  nothing the stage selects is included, and again no reason is `cut-by-roots`.

### **AC-4** Several selected roots give the roots a rule applies to

A rule that two selected roots reach applies to both, in the order of their
names, and to one when only one reaches its ruleset.

#### Two roots

- **Given** rulesets `demo`, `shared` and `only` with a rule each, a root `api`
  with `rule_presets = ["demo.all", "shared.all"]` and a root `ui` with
  `rule_presets = ["demo.all", "shared.all", "only.all"]`.
- **When** `select` runs for the roots `("ui", "api")`.
- **Then** the rules of `demo` and `shared` apply to `("api", "ui")` and the
  rule of `only` applies to `("ui",)`.

### **AC-5** No roots at all leaves only the root-independent rules

When roots are applied and none are given, only rules of root-independent
rulesets are included.

#### An empty tuple

- **Given** the repository of AC-1.
- **When** `select` runs for the roots `()` and the stage `s`.
- **Then** `process.FIX001` is included, and `demo.ARC001` and `web.WEB001` are
  out, `web.WEB001` with the reason `cut-by-roots` and `demo.ARC001` as
  `not-selected`, because no root layer applied.

### **AC-6** The selection holds every rule once and is a value

A `Selection` has an entry for every rule of every ruleset in the order of C-2
of [wio rules](../../README.md), each with one decision, and decisions are
frozen values that compare and hash.

#### Every rule

- **Given** a repository with rules in two rulesets and two families.
- **When** `select` runs for any roots and stage.
- **Then** the selection has exactly one entry for each rule in the order of
  C-2, two selections of the same inputs are equal, and assigning a field of a
  decision raises.

### **AC-7** A name that does not exist is not caught

An unknown stage or root raises the `KeyError` of `apply_layers`.

#### Unknown names

- **Given** the repository of AC-1.
- **When** `select` runs for a stage `none`, and for a root `none`.
- **Then** each raises `KeyError` naming `none`.

### **AC-8** The selection does not depend on the order of the inputs

The same config, rulesets and arguments give an equal selection, whatever the
order of the tables of the config, of the entries of its lists and of the roots,
and `select` reads no file.

#### Two orders

- **Given** the repository of AC-4 declared in two orders, with no file system,
  and the roots given as `("ui", "api")` and `("api", "ui")`.
- **When** `select` runs on each.
- **Then** the selections are equal.

## Additional context

- `LayerEffect` and `Routes` are defined by `cm25z9` and `cyeth5` and move to
  `wio.models.rules` with this Work, which completes the stub there; those
  Works' criteria name the types by their fields, so the move changes none of
  them, and `uv run tach check` verifies that no model imports a component.
