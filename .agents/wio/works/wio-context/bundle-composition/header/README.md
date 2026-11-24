<!-- wio
id = "bg0g78"
template = "feature.leaf"
roots = ["wio"]
depends_on = ["bgc8q9"]
-->

# Header

## Purpose

A session must see at a glance which Work, action and stage it was given and
whether it is a gate, how it should be run, what it received, and which command
to run again, and a wrong stage must be caught by reading the header.

## Goals

- The first three lines of the header name the Work, the action and the stage.
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
- Defining the body, which the assembly does.

## Assumptions

None.

## Mechanisms

The labels and the layout below are provisional, but the facts are required, and
the header has no blank line.

- **The lines** — `work: <id> (<title>)`, or `work: <id>` for a Work with no
  title, `action: <name>`, `stage: <name>`, `gate: yes` or `gate: no`, with
  `, judged by a person` after `gate: yes` for `judge = "human"`,
  `session: fresh` or `session: any`, with `, do not continue it` for a stage
  that is not continuable, `rules: <n>`, `size: <bytes> bytes, <lines> lines
  (body)`, `bundle: <id>`, `command: <canonical command>`, and for a skill
  `skill: <name> (<directory>, files <hash>)`.
- **The canonical command** — the one that the Glossary of `j85eh5` defines.

## Acceptance criteria

### **AC-1** The header names the stage and what it is

The first three lines name the Work, the action and the stage, and the header
says whether the stage is a gate and what session it advises, in the provisional
wording of the lines.

#### A fresh human gate

- **Given** a stage that is a gate with `judge = "human"` and
  `session = "fresh"`.
- **When** the header is built.
- **Then** its first three lines name the Work with its title, the action and
  the stage, and it says that the stage is a gate judged by a person and that
  the session is fresh.

#### A stage that is not a gate

- **Given** a stage with no `gate`, no `session` and `continuable = false`, and
  another with `judge = "human"` and no `gate`.
- **When** the header is built for each.
- **Then** each says that the stage is not a gate, the first says that the
  session is any and not to continue it, and neither says that a person judges.

#### A fresh stage that is not continuable, and a Work with no title

- **Given** a stage with `session = "fresh"` and `continuable = false`, and a
  Work with no title.
- **When** the header is built.
- **Then** it says that the session is fresh and not to continue it, and the
  Work's line holds its id alone.

### **AC-2** The header states what the session received

The header gives the number of rules, the size of the body in bytes and lines,
and the bundle id, in the provisional wording, and says that no rule was
selected when none was.

#### Three rules, and none

- **Given** a body of 1234 bytes and 56 lines with three rules, and a body with
  no rule.
- **When** the header is built for each.
- **Then** the first says that it holds three rules and that the body is 1234
  bytes and 56 lines, the second says that it holds no rule, and each gives the
  id that it was given.

### **AC-3** The header states the canonical command

The header states the command that the Glossary defines, for the Work, the
action and the stage as parsed.

#### A request

- **Given** the request for the Work `k3m9xq`, the action `deliver` and the
  stage `architecture`.
- **When** the header is built.
- **Then** its command line is `wio context k3m9xq deliver architecture`, in the
  provisional wording of the label.

### **AC-4** A stage with a skill names where it was found

The header names the skill, the directory it was found in, relative to the
repository, and the hash of its files, and a stage with a goal has no such line.

#### A skill and a goal

- **Given** a stage with the skill `wio-define` found in `.agents/skills` and a
  stage with a goal.
- **When** the header is built for each.
- **Then** the first names `wio-define`, `.agents/skills/wio-define` and the
  hash it was given, and the second has no skill line.
