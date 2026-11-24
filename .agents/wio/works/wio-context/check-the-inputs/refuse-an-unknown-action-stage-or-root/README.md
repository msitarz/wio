<!-- wio
id = "42cb49"
template = "feature.leaf"
roots = ["wio"]
depends_on = ["b53rss"]
-->

# Refuse an unknown action, stage or root

## Purpose

An empty bundle looks like success, so an action, a stage or a root that the
config does not declare must be refused and never answered with a bundle.

## Goals

- An action that the config does not declare is refused.
- A stage that the config does not declare is refused.
- A root that a Work lists and the config does not declare is refused when the
  stage selects the Work's roots.
- Each refusal names the unknown name, and for an action or a stage the names
  that exist.

## Non-Goals

- A stage that is declared but outside the action's pipeline, which is a warning
  that a sibling gives.
- Refusing an unknown Work, which the sibling does.
- Naming the descendant that lists an unknown root, which the roots port does
  not give.
- The order in which the refusals are judged, which the parent states.

## Assumptions

### A-1

The only unknown root that a run can meet is one that a Work lists, because the
roots of a stage are judged by the config, and a config with an error is
refused.

### A-2

A root that a Work lists and the config does not declare is already an error of
`wio contracts check`, so refusing it here, where it matters, repeats no check.

## Mechanisms

- **The declared names** — the actions, stages and roots of the config, read
  through the shared `Settings` port.
- **The roots of a Work** — read through the roots port that the parent names,
  and so with `@descendants` expanded.

## Acceptance criteria

### **AC-1** An unknown action is refused

An action that the config does not declare exits 2 and names the action and the
declared ones.

#### A misspelled action

- **Given** a config that declares the actions `define` and `deliver` and the
  stage `architecture`, and a Work.
- **When** `wio context` runs with the action `delivr`.
- **Then** it exits 2, the message names `delivr` and lists `define` and
  `deliver`, and standard output is empty.

### **AC-2** An unknown stage is refused

A stage that the config does not declare exits 2 and names the stage and the
declared ones.

#### A stage that is not declared

- **Given** a config that declares the action `deliver` and the stages
  `architecture` and `wiring`, and a Work.
- **When** `wio context` runs with the action `deliver` and the stage
  `no-such-stage`.
- **Then** it exits 2, the message names `no-such-stage` and lists the declared
  stages, and standard output is empty.

### **AC-3** An unknown root of a Work is refused where the stage selects it

A Work that lists a root the config does not declare exits 2 at a stage that
selects the Work's roots, and the message names the root and the Work that was
run.

#### A root that is not declared

- **Given** a config that declares the roots `api` and `contract` and a stage
  `implementation` that sets no `roots`, and a Work whose `roots` list `api` and
  `ghost`.
- **When** `wio context` runs for it at `implementation`.
- **Then** it exits 2, the message names `ghost` and the Work, and standard
  output is empty.

### **AC-4** A root that the stage does not select is not refused

The same Work at a stage that names its own roots and not `@work` gets its
bundle.

#### A stage with its own roots

- **Given** the Work and config of AC-3 and a stage whose `roots` are
  `["contract"]`.
- **When** `wio context` runs for it at that stage.
- **Then** the bundle is printed and the exit code is 0.
