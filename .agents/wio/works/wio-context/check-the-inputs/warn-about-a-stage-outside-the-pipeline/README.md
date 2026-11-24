<!-- wio
id = "5tqywr"
template = "feature.leaf"
roots = ["wio"]
depends_on = ["b53rss"]
-->

# Warn about a stage outside the pipeline

## Purpose

The driver names the stage, so a stage outside the action's pipeline for the
Work must not block a session, but a mistaken pair, such as `deliver` with
`define`, is easy to type and goes unnoticed.

## Goals

- A driver is warned when the stage is not in the pipeline of the given action
  for the Work.
- A driver is warned when the Work has no pipeline for the action, because it
  removed the action or never had it.
- A driver is not warned when the stage is in that pipeline, whether the
  pipeline is a stage preset or a list of stages.
- The pipeline judged is the Work's effective one, from its own `[actions]`, its
  template or the config's defaults.

## Non-Goals

- Refusing the pair, because the driver decides.
- Checking that a pipeline is well formed or that a stage preset is declared,
  which `wio contracts check` does.

## Assumptions

### A-1

The effective pipeline of an action for a Work, with a stage preset already
expanded into its stages, can be had from `shown_actions` and `ShownAction` of
`wio.contracts`, which `wio contracts show` uses, so that `wio context` cannot
disagree with it about where a pipeline comes from.

### A-2

A Work whose pipeline names a stage preset that the config does not declare has
no stage in its pipeline, so a run for it gets the warning about a stage outside
the pipeline, and `wio contracts check` reports the preset.

## Mechanisms

- **The pipeline port** — in `src/wio/context/ports.pyi`, provisional, satisfied
  by `wio.contracts` from `shown_actions`, which gives each action of a Work
  with its stages.

## Acceptance criteria

Every config in the criteria below declares the action `deliver` and the stages
that its Works and its runs name, so that no run is refused as an unknown stage
or action, and a stage preset that a Work names is declared unless the criterion
says otherwise.

### **AC-1** A stage outside the pipeline is warned about

A stage that the action's pipeline for the Work does not hold gives a warning
that names the stage, the action and the Work, and the run goes on.

#### The pair `deliver` and `define`

- **Given** a config that declares the action `deliver` and the stages
  `architecture`, `wiring` and `define`, and a Work whose `deliver` pipeline is
  `architecture` and `wiring`.
- **When** `wio context` runs for that Work, `deliver` and `define`.
- **Then** a warning names `define`, `deliver` and the Work, the bundle is
  printed, and the exit code is 0.

#### A stage preset that is not declared

- **Given** a config that declares the action `deliver` and the stage
  `architecture`, and a Work whose `deliver` is the preset `ghost-preset`, which
  the config does not declare.
- **When** `wio context` runs for that Work, `deliver` and `architecture`.
- **Then** a warning says that `architecture` is outside the pipeline, and the
  bundle is printed.

### **AC-2** A stage inside the pipeline is not warned about

A stage in the pipeline, written as a list or reached through a stage preset,
gives no warning about the pipeline.

#### A list and a preset

- **Given** a config that declares the action `deliver`, the stages
  `architecture` and `wiring`, and the stage preset `typed-boundary` that holds
  `architecture`, a Work whose `deliver` is the list `architecture`, `wiring`,
  and another whose `deliver` is the preset `typed-boundary`.
- **When** `wio context` runs for each with `deliver` and `architecture`.
- **Then** neither run reports a warning about the pipeline.

### **AC-3** The Work's own pipeline decides

A Work whose own `[actions]` replace the template's pipeline, or remove the
action, or that has no such action at all, is judged by its own.

#### An override, a removal and an absence

- **Given** a config that declares the actions `deliver` and `define` and the
  stages `architecture` and `implementation`, whose `[works.defaults.actions]`
  give `define` the list `architecture` and no `deliver`, a template whose
  `deliver` holds `architecture`, a Work that follows it and replaces `deliver`
  with `implementation`, a Work that follows it and removes `deliver`, and a
  Work that follows no template.
- **When** `wio context` runs for each Work with `deliver` and `architecture`.
- **Then** the first reports a warning, because `architecture` is outside its
  pipeline, and the second and the third each report a warning that says the
  Work has no pipeline for `deliver`.

### **AC-4** The template's pipeline decides when the Work gives none

A Work that follows a template and has no `[actions]` of its own is judged by
the template's pipeline.

#### A template's pipeline

- **Given** a config that declares the action `deliver` and the stages
  `architecture` and `wiring`, a template whose `deliver` holds `architecture`,
  and a Work that follows it and has no `[actions]`.
- **When** `wio context` runs for it with `deliver` and `architecture`, and then
  with `deliver` and `wiring`.
- **Then** the first reports no warning about the pipeline and the second
  reports one.

### **AC-5** The config's defaults decide for a Work with no template

A Work that follows no template is judged by the pipeline of
`[works.defaults.actions]`.

#### A Work with no template

- **Given** a config that declares the action `deliver` and the stages
  `implementation` and `architecture`, whose `[works.defaults.actions]` give
  `deliver` the list `implementation`, and a Work with no template and no
  `[actions]`.
- **When** `wio context` runs for it with `deliver` and `implementation`, and
  then with `deliver` and `architecture`.
- **Then** the first reports no warning about the pipeline and the second
  reports one.
