<!-- wio
id = "j98t8a"
template = "feature.leaf"
roots = ["wio", "repo"]
depends_on = ["mcn1xg"]
-->

# Checking actions, stages and presets

## Purpose

The names that actions, stage presets, default actions and stages use for one
another must resolve before any command builds a pipeline from them.

## Goals

- A reference to a stage, a stage preset, an action or a root that does not
  exist is an error that says what exists.
- A pipeline that lists a stage twice, and an `after` cycle, are errors.
- The vocabulary of `results` and of the reserved `@` entries is checked.

## Non-Goals

- Whether a template's or a contract's pipeline resolves: the contracts and
  templates Works check those.
- Rule references and paths, which the other check leaves own.
- Reporting a stage, preset or action that nothing uses.

## Assumptions

- **A-1**: A stage preset, a root and an action are keyed by their names in
  their tables, so a duplicate name is already rejected by TOML.

## Mechanisms

- Checks added to the ordered list of the loader, each a function from the
  `Config` and what it may read to diagnostics.
- A depth-first search for the `after` cycle, reporting the actions on it.

## Acceptance criteria

### **AC-1** Stage presets and default actions name known stages

Every stage in a stage preset exists, a default action's string names a stage
preset and each name in its list is a stage, and no stage appears twice in one
pipeline.

#### A missing stage and a repeated stage

- **Given** a stage preset `p = ["define", "review"]` where `review` is not a
  stage, and a preset `q = ["define", "define"]`.
- **When** the checks run.
- **Then** an error at `stage_presets.p[1]` names `review` and lists the known
  stages, and an error at `stage_presets.q[1]` says `define` repeats.

#### Default actions

- **Given** `[works.defaults.actions]` with `deliver = "missing"` where
  `missing` is not a stage preset, `review = "define"` where `define` is a
  stage, `build = ["define", "ghost"]` where `ghost` is not a stage,
  `define = ["define"]` and `ship = ["define"]`, and `[actions]` declaring only
  `define`, `deliver`, `review` and `build`.
- **When** the checks run.
- **Then** an error at `works.defaults.actions.deliver` lists the known stage
  presets, one at `works.defaults.actions.review` says a string is a stage
  preset id and lists them, one at `works.defaults.actions.build[1]` lists the
  known stages, one at `works.defaults.actions.ship` says `ship` is not a
  declared action, and `define` passes.

### **AC-2** A stage's roots are roots or `@work`

Every entry of a stage's `roots` is a declared root or `@work`.

#### An unknown root

- **Given** a stage with `roots = ["contract", "src"]` where `src` is not a
  root.
- **When** the checks run.
- **Then** an error at `stages.define.roots[1]` names `src` and lists the
  declared roots and `@work`.

### **AC-3** `after` and `invalidated_by` name declared actions

`after` names declared actions that are not on demand and has no cycle, and
`invalidated_by` names declared actions, also behind the prefixes
`@descendants:` and `@dependencies:`; any other `@` entry is reserved for v0.2
and gets a note.

#### The errors

- **Given** actions `a` (`after = ["b"]`), `b` (`after = ["a"]`), `c`
  (`after = ["d"]`) where `d` is on demand, `h` (`after = ["zzz"]`) where
  `zzz` is no action, and `e` with
  `invalidated_by = ["f", "@descendants:g"]` where neither `f` nor `g` is an
  action.
- **When** the checks run.
- **Then** there is one error for the cycle that names `a` and `b`, one at
  `actions.c.after[0]` that says `d` is on demand, one at `actions.h.after[0]`
  that names `zzz` and lists the declared actions, and one each at
  `actions.e.invalidated_by[0]` and `actions.e.invalidated_by[1]` that name the
  undeclared action and list the declared ones.

#### The reserved entries

- **Given** an `invalidated_by` entry `@children:a`, an `@` form that v0.2
  reserves.
- **When** the checks run.
- **Then** a note, not an error, says it is reserved.

### **AC-4** `results` is a usable vocabulary

`results` is not empty and has no duplicate.

#### An empty list and a duplicate

- **Given** `results = []`, and `results = ["pass", "pass"]`.
- **When** the checks run on each.
- **Then** each is an error at `results` that says what a result list needs.

## Additional context

- [Invariants wio checks](../../../../../../docs/concepts.md#invariants-wio-checks)
  lists these references.
