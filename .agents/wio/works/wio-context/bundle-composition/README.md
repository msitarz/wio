<!-- wio
id = "v2dxyw"
template = "feature.parent"
roots = ["@descendants"]
depends_on = []
-->

# Bundle composition

## Purpose

The parts of a bundle are specified one by one, but nothing yet joins them into
one text whose id and size describe it, so a session cannot be given a bundle
that can be compared with another.

## Goals

- A bundle holds the header, the stage's goal or skill pointer, the resolved
  contract, the rules and the closing line, in that order.
- The id and the size that the header states are those of the body, so a reader
  can check them against the text.
- A skill that a stage names is found, pointed to and counted in the id.

## Non-Goals

- Delivering the bundle, which the delivery does.
- Recording the stage entry, which the event does.

## Assumptions

None.

## Visuals

Before, nothing builds a bundle. After, the lookup of a skill, the stage's
guidance, the contract section, the rules section, the identity and the header
each build one part, and the assembly joins them in order and gives the header
the id and the size of the body.

## Acceptance criteria

### **AC-1** The header states the id and the size of the body

The bundle id in the header is the hash of the body and the skill's files, and
the size is the body's bytes and lines, so both are recomputable from the text.

#### Recomputing from the text

- **Given** a bundle printed for a stage with a goal.
- **When** its body, everything after the header, is hashed and counted.
- **Then** the hash gives the bundle id in the header, and the counts give the
  size in the header.

### **AC-2** A skill stage is pointed to and counted

For a stage with a skill, the body holds the pointer and not the skill's text,
and the id changes when a file of the skill changes.

#### A skill with two files

- **Given** a stage whose skill has `SKILL.md` and a reference file.
- **When** the bundle is printed, the reference file is changed, and the bundle
  is printed again.
- **Then** the body of each holds the pointer to `SKILL.md` and none of the
  skill's text, and the two ids differ.
