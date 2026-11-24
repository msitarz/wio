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
would be large and would repeat what a harness that loads the skill itself
already has.

## Goals

- A stage with a goal shows the value of its `goal` key.
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

### **AC-1** A goal is shown as its value

The part of a stage with a goal is the value of its `goal` key, unchanged, also
when the value is empty.

#### A goal with two lines, and an empty goal

- **Given** a stage whose `goal` value is two lines of text, and a stage whose
  `goal` is empty.
- **When** the guidance of each is built.
- **Then** the first part is those two lines, unchanged, and the second is
  empty.

### **AC-2** A skill is pointed to and not included

The part of a stage with a skill is this one line, with the skill's name and the
path relative to the repository, and a single space between its sentences, and
it holds nothing of the skill's files:

```text
This stage's procedure is the skill `<name>`. Read `<path>/SKILL.md` and follow it; its other files are in the same directory.
```

#### A skill in a configured directory

- **Given** a stage whose skill `wio-define` is found in `.agents/wio/skills`,
  which `[skills] paths` names.
- **When** its guidance is built.
- **Then** the part is that line with `wio-define` and
  `.agents/wio/skills/wio-define/SKILL.md`, on one line, and it contains no text
  of `SKILL.md`.
