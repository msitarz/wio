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
- A driver is not warned when the stage is in that pipeline, whether the
  pipeline is a stage preset or a list of stages.
- The pipeline judged is the Work's effective one, from its own `[actions]`, its
  template or the config's defaults.

## Non-Goals

- Refusing the pair, because the driver decides.
- Checking that a pipeline is well formed, which `wio contracts check` does.

## Assumptions

### A-1

The effective pipeline of an action for a Work can be had from the actions that
`wio.contracts` already resolves, so the pipeline is not computed a second time
and `wio context` cannot disagree with `wio contracts show` about where it comes
from.

## Mechanisms

- **The pipeline port** — in `src/wio/context/ports.pyi`, provisional, satisfied
  by `wio.contracts` from `resolve_actions`, which gives the pipeline of an
  action as a stage preset id or a list of stage names.
- **The stage presets** — read through the shared `Settings` port, to expand a
  preset to its stages.

## Acceptance criteria

### **AC-1** A stage outside the pipeline is warned about

A stage that the action's pipeline for the Work does not hold gives a warning
that names the stage, the action and the Work, and the run goes on.

#### The pair `deliver` and `define`

- **Given** a Work whose `deliver` pipeline is the stages `architecture` and
  `wiring`, and a config that declares the stage `define`.
- **When** `wio context` runs for that Work, `deliver` and `define`.
- **Then** a warning names `define`, `deliver` and the Work, the bundle is
  printed, and the exit code is 0.

### **AC-2** A stage inside the pipeline is not warned about

A stage in the pipeline, written as a list or reached through a stage preset,
gives no warning.

#### A list and a preset

- **Given** a Work whose `deliver` is the list `architecture`, `wiring`, and
  another whose `deliver` is the preset `typed-boundary` that holds
  `architecture`.
- **When** `wio context` runs for each with `deliver` and `architecture`.
- **Then** neither run reports a warning.

### **AC-3** The Work's own pipeline decides

A Work whose own `[actions]` replace the template's pipeline, or remove the
action, is judged by its own.

#### An override and a removal

- **Given** a template whose `deliver` holds `architecture`, a Work that
  replaces it with `implementation`, and a Work that removes `deliver`.
- **When** `wio context` runs for each Work with `deliver` and `architecture`.
- **Then** the first reports a warning, because `architecture` is outside its
  pipeline, and the second reports a warning that says the Work has no pipeline
  for `deliver`.
