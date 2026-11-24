<!-- wio
id = "30gfec"
template = "feature.leaf"
roots = ["wio"]
depends_on = ["bgc8q9"]
-->

# Stage guidance

## Purpose

A session must learn what its stage is to produce, either from the stage's goal
or from the skill that carries it, and a bundle that held a skill's whole text
would be large and would not work for a harness that loads the skill itself.

## Goals

- A stage with a goal shows the goal exactly as the config writes it.
- A stage with a skill shows one fixed instruction that names the skill and the
  path of its `SKILL.md`.
- The text of the skill is never part of the bundle.

## Non-Goals

- Finding the skill and hashing its files, which the lookup does.
- Judging whether the goal is good.

## Assumptions

None.

## Mechanisms

- **The stage's `goal` or `skill`** — read through the shared `Settings` port;
  the config requires exactly one of them.
- **The skill lookup** — gives the directory of the skill, relative to the
  repository.

## Acceptance criteria

### **AC-1** A goal is shown as written

The part of a stage with a goal is the goal's text, unchanged.

#### A goal with two lines

- **Given** a stage whose goal is two lines of text.
- **When** its guidance is built.
- **Then** the part is those two lines, unchanged.

### **AC-2** A skill is pointed to and not included

The part of a stage with a skill is the instruction `This stage's procedure is
the skill `<name>`. Read `<path>/SKILL.md` and follow it; its other files are in
the same directory.`, with the skill's name and the path relative to the
repository, and it holds nothing of the skill's files.

#### A skill in a configured directory

- **Given** a stage whose skill `wio-define` is found in `.agents/wio/skills`,
  which `[skills] paths` names.
- **When** its guidance is built.
- **Then** the part is the instruction with `wio-define` and
  `.agents/wio/skills/wio-define/SKILL.md`, and it contains no text of
  `SKILL.md`.
