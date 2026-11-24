<!-- wio
id = "kgf116"
template = "feature.parent"
roots = ["@descendants"]
depends_on = []
-->

# Check the inputs

## Purpose

An unreadable tree, an unknown name and a choice that looks wrong are the cases
where a session would start with the wrong context, and today nothing refuses
the first two or tells the driver about the last.

## Goals

- A config, a Work tree or a Work that cannot be read is refused, and so is a
  Work that does not exist.
- An unknown action, stage or root is refused.
- A driver is warned when the stage is outside the action's pipeline for the
  Work.
- A driver is warned when a stage that selects the Work's roots meets a Work
  with none.

## Non-Goals

- The warning about an oversized bundle, which the delivery does.
- Checking the tree beyond what a run needs, which `wio contracts check` does.

## Assumptions

None.

## Visuals

Before, `wio context` has no check of its inputs. After, it judges its inputs in
a fixed order before it composes anything, refuses with exit 2 at the first that
is wrong, and collects the warnings of a choice that looks wrong and reports
them with the bundle.

## Acceptance criteria

### **AC-1** The refusals are judged in one order

The first problem that applies is the one reported, in this order: the config,
the tree, the Work, the action, the stage, the root.

#### A repository with every fault

- **Given** under `nesting` a config with a key the schema does not know, a
  directory with two marked files, the id of no Work, an action that the config
  does not declare, a stage that it does not declare, and a Work that lists the
  name of no root at a stage that selects the Work's roots.
- **When** `wio context` runs, and then runs again after each reported fault is
  removed, in the order they were reported.
- **Then** the six runs report the config, the tree, the Work, the action, the
  stage and the root, in that order, and each exits 2.

### **AC-2** Every warning of a run is reported once

A run that deserves the warning about the pipeline and the warning about the
roots reports both, each once, with the bundle, and exits 0.

#### Two warnings together

- **Given** a Work with no roots, an action whose pipeline does not hold the
  stage, and a stage with no `roots`.
- **When** `wio context` runs for that Work, action and stage.
- **Then** the bundle is printed, each of the two warnings is reported once, and
  the exit code is 0.
