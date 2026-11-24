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

- A config or a Work tree that cannot be read is refused, while a fault
  elsewhere in the tree does not stop a session.
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

Before, `wio context` has no check of its inputs. After, it judges the config,
the tree and the names before it composes anything, refuses with exit 2 when one
is wrong, and collects the warnings of a choice that looks wrong and reports
them with the bundle.

## Acceptance criteria

### **AC-1** A refusal stops the run before anything is composed or recorded

Each refusal of the children exits 2, prints no bundle and records no event.

#### One refusal of each kind

- **Given** a config with an error, a tree with two marked files in one
  directory, the id of no Work, the name of no action, the name of no stage and
  a Work that lists the name of no root.
- **When** `wio context` runs for each.
- **Then** each exits 2, standard output is empty, and no `context` event is
  written.

### **AC-2** Every warning of a run is reported once

A run that deserves the warning about the pipeline and the warning about the
roots reports both, each once, with the bundle, and exits 0.

#### Two warnings together

- **Given** a Work with no roots, an action whose pipeline does not hold the
  stage, and a stage that selects the Work's roots.
- **When** `wio context` runs for that Work, action and stage.
- **Then** the bundle is printed, each of the two warnings is reported once, and
  the exit code is 0.
