<!-- wio
id = "5yb4tz"
template = "feature.leaf"
roots = ["wio"]
depends_on = ["cm25z9", "ndwemw"]
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
- One `select` serves every view and the `RuleSelection` port of `wio.context`.

## Non-Goals

- Applying the layers and finding the rulesets that a root reaches, which
  `cm25z9` does.
- Finding the roots of a Work, a stage or a file, which `ndwemw` does.
- Printing or explaining a selection, which `wio rules list` does.

## Assumptions

### A-1

When several layers touched a rule, the reason it is out is the last layer that
removed it, so a rule that the root added and the stage removed is excluded by
the stage, and one that the stage removed and the veto removed again is vetoed.

### A-2

A rule that the layers selected is cut by the roots only after the layers have
decided, so a rule that a layer removed is never reported as cut by the roots.

## Mechanisms

The names of the types and the functions below are provisional.

- **`Decision`** — a frozen dataclass in `wio.models.rules` with
  `included: bool`, `roots: tuple[str, ...]`, `root_independent: bool`,
  `events: tuple[LayerEvent, ...]` and `reason: Reason | None`; it replaces the
  stub, and `Selection` is the `Mapping[Rule, Decision]` of the same module.
- **`Reason`** — frozen, with `kind`, one of `not-selected`, `excluded`,
  `vetoed` and `cut-by-roots`, and the `layer`, `root` or `stage`, of an
  `excluded` reason and none otherwise.
- **`LayerEvent` and `Routes`** — move to `wio.models.rules` from `cm25z9` and
  `cyeth5`, because a `Decision` holds them and a model may not import a
  component.
- **`select(roots, stage, config, rulesets) -> Selection`** — in `wio.rules`,
  where `roots` is a `tuple[str, ...]` or `None` and `stage` is a name or
  `None`; it calls `apply_layers` of `cm25z9` and decides each rule.
- **The `RuleSelection` adapter** — satisfies the port of `wio.context`: its
  `select(contract, stage)` takes the roots from `ndwemw` for the contract's
  Work and the stage and calls `select`; the port is in
  `src/wio/context/ports.pyi`.

## Constraints

### C-1

`select` does no input or output, and the `Selection` holds every rule of every
ruleset in the order of A-8 of [wio rules](../../README.md), each with one
decision. AC-6 and AC-8 verify it.

## Acceptance criteria

### **AC-1** A selected rule applies where its ruleset is reached

With roots given, a selected rule is included when its ruleset is
root-independent or reached by a selected root, and is cut by the roots
otherwise.

#### Reached, unreached and independent

- **Given** a ruleset `demo` reached by the root `api`, a ruleset `web` that no
  root reaches, a root-independent ruleset `process`, and a stage whose layers
  select `demo.ARC001`, `web.WEB001` and `process.FIX001`.
- **When** `select` runs for the roots `("api",)` and that stage.
- **Then** `demo.ARC001` is included with the roots `("api",)`, `web.WEB001` is
  out with the reason `cut-by-roots`, and `process.FIX001` is included with
  `root_independent` true and no roots.

### **AC-2** The reason is the last layer that removed the rule

A rule that is out has the reason of the last layer that removed it,
`not-selected` when no layer touched it, and `cut-by-roots` only for a rule that
the layers kept.

#### Each reason

- **Given** rules that the layers leave in these states: never touched, added by
  a root and removed by its rule preset's exclude, added by a root and removed
  by the stage, removed by the stage and then by the veto, removed by the stage
  and added back by `rules_always_include`, and kept by the layers in an
  unreached ruleset.
- **When** `select` runs for the roots that reach the other rulesets.
- **Then** the reasons are `not-selected`, `excluded` with the layer `root`,
  `excluded` with the layer `stage`, `vetoed`, no reason because the rule is
  included, and `cut-by-roots`, and every decision carries the events of its
  layers.

### **AC-3** Without roots nothing is cut

When the roots are not applied, no rule is cut by the roots, and a rule that is
not root-independent is listed with the roots of the config that reach its
ruleset.

#### Roots not applied

- **Given** the repository of AC-1 with two roots `api` and `web` of which only
  `api` reaches `demo`.
- **When** `select` runs for `None` roots and the stage.
- **Then** `demo.ARC001` is included with the roots `("api",)`, `web.WEB001` is
  included with no roots, `process.FIX001` is included with `root_independent`
  true, and no reason is `cut-by-roots`.

### **AC-4** Several selected roots give the roots a rule applies to

A rule that two selected roots reach applies to both, in the order of their
names, and to one when only one reaches its ruleset.

#### Two roots

- **Given** rulesets `demo` and `shared` that both `api` and `web` reach, and
  `only` that only `web` reaches, each with a selected rule.
- **When** `select` runs for the roots `("web", "api")`.
- **Then** the rules of `demo` and `shared` apply to `("api", "web")` and the
  rule of `only` applies to `("web",)`.

### **AC-5** No roots at all leaves only the root-independent rules

When roots are applied and none are given, only rules of root-independent
rulesets are included.

#### An empty tuple

- **Given** the repository of AC-1.
- **When** `select` runs for the roots `()` and the stage.
- **Then** `process.FIX001` is included, and `demo.ARC001` and `web.WEB001` are
  out with the reason `cut-by-roots`.

### **AC-6** The selection holds every rule once and is a value

A `Selection` has an entry for every rule of every ruleset in the order of A-8,
each with one decision, and decisions are frozen values that compare and hash.

#### Every rule

- **Given** a repository with rules in two rulesets and two families.
- **When** `select` runs for any roots and stage.
- **Then** the selection has exactly one entry for each rule in the order of
  A-8, two selections of the same inputs are equal, and assigning a field of a
  decision raises.

### **AC-7** A name that does not exist is refused

An unknown stage or root raises `KeyError` that names it, as `apply_layers`
does.

#### Unknown names

- **Given** the repository of AC-1.
- **When** `select` runs for a stage `none`, and for a root `none`.
- **Then** each raises `KeyError` naming `none`.

### **AC-8** The selection does not depend on the order of the inputs

The same config, rulesets and arguments give an equal selection, whatever the
order of the tables of the config, of the entries of its lists and of the roots.

#### Two orders

- **Given** the repository of AC-4 declared in two orders and the roots given as
  `("web", "api")` and `("api", "web")`.
- **When** `select` runs on each.
- **Then** the selections are equal.

### **AC-9** `wio.context` receives the selection of a Work at a stage

The adapter of the `RuleSelection` port gives, for a resolved contract and a
stage, the selection for the roots that `ndwemw` finds for that Work and stage.

#### Same as `select`

- **Given** a Work whose roots list `api`, a stage with no `roots`, and a stage
  with `roots = ["web"]`.
- **When** the adapter's `select` runs for each stage.
- **Then** the first equals `select` for the roots `("api",)` and the second for
  `("web",)`.

#### Refusals

- **Given** a Work with no roots, a stage with no `roots`, and a stage `none`.
- **When** the adapter's `select` runs for the first stage and for `none`.
- **Then** the first raises the error that the port declares, a `ValueError` in
  its provisional form, and the second raises `KeyError`.

## Additional context

- `LayerEvent` and `Routes` are defined by `cm25z9` and `cyeth5` and move to
  `wio.models.rules` with this Work, which completes the stub there; those
  Works' criteria name the types by their fields, so the move changes none of
  them.
