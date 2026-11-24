<!-- wio
id = "bg0g78"
template = "feature.leaf"
roots = ["wio"]
depends_on = ["bgc8q9", "ghq8mz"]
-->

# Header

## Purpose

A session must see at a glance which Work, action and stage it was given and
whether it is a gate, how it should be run, what it received, and which command
to run again, and a wrong stage must be caught by reading the header.

## Goals

- The header names the Work, the action and the stage first.
- The header says whether the stage is a gate and, for a gate, whether a person
  must judge.
- The header gives the session advice.
- The header states the number of rules, the size of the body and the bundle id.
- The header states the canonical command.
- For a stage with a skill, the header names the directory the skill was found
  in and a hash of its files.

## Non-Goals

- Computing the id or the hash, which their Works do.
- Warning about the size, which the delivery does.

## Assumptions

None.

## Mechanisms

The labels and the layout below are provisional, but the facts are required.

- **The lines** — `work: <id> (<title>)`, `action: <name>`, `stage: <name>`,
  `gate: yes` or `gate: no` with `, judged by a person` for `judge = "human"`,
  `session: fresh` or `session: any` with `, do not continue it` for a stage
  that is not continuable, `rules: <n>`,
  `size: <bytes> bytes, <lines> lines (body)`, `bundle: <id>`,
  `command: <canonical command>`, and for a skill
  `skill: <name> (<directory>, files <hash>)`.
- **The canonical command** — `wio context <work> <action> <stage>` with the
  names as resolved, and no option that changes only where the bundle goes.

## Acceptance criteria

### **AC-1** The header names the stage and what it is

The first lines name the Work, the action and the stage, and say whether the
stage is a gate and what session it advises.

#### A fresh human gate

- **Given** a stage that is a gate with `judge = "human"` and
  `session = "fresh"`.
- **When** the header is built.
- **Then** it names the Work with its title, the action and the stage, and says
  `gate: yes, judged by a person` and `session: fresh`.

#### A stage that is not a gate

- **Given** a stage with no `gate`, no `session` and `continuable = false`.
- **When** the header is built.
- **Then** it says `gate: no` and `session: any, do not continue it`.

### **AC-2** The header states what the session received

The header gives the number of rules, the size of the body in bytes and lines,
and the bundle id, and says that no rule was selected when none was.

#### Three rules, and none

- **Given** a body of 1234 bytes and 56 lines with three rules, and a body with
  no rule.
- **When** the header is built for each.
- **Then** the first says `rules: 3` and `size: 1234 bytes, 56 lines (body)`,
  the second says `rules: 0`, and each gives the id that it was given.

### **AC-3** The canonical command does not depend on the invocation

The command in the header is the same whatever option was given.

#### With and without `--output`

- **Given** a run of `wio context k3m9xq deliver architecture` and a run of the
  same with `--output`.
- **When** their headers are built.
- **Then** both say `command: wio context k3m9xq deliver architecture`.

### **AC-4** A stage with a skill names where it was found

The header names the skill, the directory it was found in, relative to the
repository, and the hash of its files, and a stage with a goal has no such line.

#### A skill and a goal

- **Given** a stage with the skill `wio-define` found in `.agents/skills` and a
  stage with a goal.
- **When** the header is built for each.
- **Then** the first holds `skill: wio-define (.agents/skills/wio-define, files
  <hash>)` and the second holds no `skill:` line.
