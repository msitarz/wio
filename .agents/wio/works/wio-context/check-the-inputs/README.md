<!-- wio
id = "kgf116"
template = "feature.parent"
roots = ["@descendants"]
depends_on = []
-->

# Check the inputs

## Purpose

An unreadable tree, an unknown name, a fault in the rules and a choice that
looks wrong are the cases where a session would start with the wrong context, so
each must be refused or reported and never answered with a bundle that looks
complete.

## Goals

- A config, a Work tree or a Work that cannot be read is refused, and so is a
  Work that does not exist.
- An unknown action, stage or root is refused.
- A fault in a rule file or a ruleset is refused.
- A driver is warned when the stage is outside the action's pipeline for the
  Work.
- A driver is warned when a stage that selects the Work's roots meets a Work
  with none.

## Non-Goals

- The warning about an oversized bundle, which the delivery does.
- Checking the tree beyond what a run needs, which `wio contracts check` does.

## Assumptions

### A-1

A stage selects the Work's roots when its `roots` are not set or list `@work`,
and the Work's roots that a stage does not select play no part, as in
`wio rules`.

## Mechanisms

The name below is provisional.

- **The roots port** — in `src/wio/context/ports.pyi`, satisfied by
  `wio.contracts`, which gives the roots of a Work with `@descendants` expanded
  and each name once; the refusal of an unknown root and the warning about a
  Work with no roots read the roots through it.

## Visuals

Before, `wio context` has no check of its inputs. After, it judges its inputs
before it composes anything, and the warnings of a choice that looks wrong are
reported with the bundle.

## Acceptance criteria

### **AC-1** The refusals are judged in one order

The first problem that applies is the one reported, in this order: the config,
the tree, the Work, the action, the stage, the root, the rules.

#### A repository with every fault

- **Given** under `nesting` a config with a key the schema does not know, a
  directory with two marked files, the id of no Work, an action that the config
  does not declare, a stage that it does not declare, a Work that lists the name
  of no root at a stage that selects the Work's roots, and a rule whose family
  its ruleset does not declare.
- **When** `wio context` runs, and then runs again after each reported fault is
  removed, in the order they were reported.
- **Then** the seven runs report the config, the tree, the Work, the action, the
  stage, the root and the rules, in that order, and each exits 2.

### **AC-2** Every warning of a run is reported once

A run that deserves the warning about the pipeline and the warning about the
roots reports both, each once, and exits 0.

#### Two warnings together

- **Given** a compiler that returns a fixed bundle, a Work with no roots, an
  action whose pipeline does not hold the stage, and a stage with no `roots`.
- **When** `wio context` runs for that Work, action and stage.
- **Then** the fixed bundle is printed, each of the two warnings is reported
  once, and the exit code is 0.
