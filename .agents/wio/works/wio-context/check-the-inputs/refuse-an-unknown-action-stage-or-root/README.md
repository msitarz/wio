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
- A root that the Work lists and the config does not declare is refused.
- Each refusal names the unknown name, and for an action or a stage the names
  that exist.

## Non-Goals

- A stage that is declared but outside the action's pipeline, which is a warning
  that a sibling gives.
- Refusing an unknown Work, which the sibling does.

## Assumptions

### A-1

The only unknown root that a run can meet is one that the Work lists, because
the roots of a stage are judged by the config, and a config with an error is
refused.

## Mechanisms

- **The declared names** — the actions, stages and roots of the config, read
  through the shared `Settings` port.
- **The roots of a Work** — read from the resolved contract, with
  `@descendants` expanded.

## Acceptance criteria

### **AC-1** An unknown action is refused

An action that the config does not declare exits 2 and names the action and the
declared ones.

#### A misspelled action

- **Given** a config that declares `define` and `deliver`, and a Work.
- **When** `wio context` runs with the action `delivr`.
- **Then** it exits 2, the message names `delivr` and lists `define` and
  `deliver`, and standard output is empty.

### **AC-2** An unknown stage is refused

A stage that the config does not declare exits 2 and names the stage and the
declared ones.

#### A stage that is not declared

- **Given** a config that declares the stages `architecture` and `wiring`.
- **When** `wio context` runs with the stage `no-such-stage`.
- **Then** it exits 2, the message names `no-such-stage` and lists the declared
  stages, and standard output is empty.

### **AC-3** An unknown root of a Work is refused

A Work that lists a root the config does not declare exits 2 and names the root
and the Work.

#### A root that is not declared

- **Given** a Work whose `roots` list `api` and `ghost`, and a config that
  declares `api` only.
- **When** `wio context` runs for it.
- **Then** it exits 2, the message names `ghost` and the Work, and standard
  output is empty.
