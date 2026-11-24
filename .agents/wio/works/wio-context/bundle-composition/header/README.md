<!-- wio
id = "bg0g78"
template = "feature.leaf"
roots = ["wio"]
depends_on = []
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
- The header states the number of rules and the size of the body.
- The header states the canonical command.
- For a stage with a skill, the header names the directory the skill was found
  in and a hash of its files.
- The header holds no blank line and no trailing newline.

## Non-Goals

- Computing the id or the hash, which their Works do.
- Warning about the size, which the delivery does.
- Parsing the request, which the command does.
- Defining the body, which the assembly does.

## Assumptions

### A-1

The number of rules is the number of rules that the rules section prints, each
once, and the command supplies it from the included rules of the `Selection`.

### A-2

The command passes the skill tuple exactly when the stage has a skill, so a
stage with a skill never reaches the builder with `None`, and a stage with a
goal never with a tuple.

## Mechanisms

The labels, the layout and the signature below are provisional, but the facts
are required.

- **The lines** — `work: <id> (<title>)`, or `work: <id>` for a Work with no
  title, `action: <name>`, `stage: <name>`, `gate: yes` or `gate: no`, with
  `, judged by a person` after `gate: yes` for `judge = "human"`,
  `session: fresh` or `session: any`, with `, do not continue it` for a stage
  that is not continuable, `rules: <n>`,
  `size: <bytes> bytes, <lines> lines (body)`,
  `command: <canonical command>`, and for a skill
  `skill: <name> (<directory>, files <hash>)`.
- **The builder** — `header(work_id: str, title: str | None, action: str,
  stage_name: str, stage: Stage, rules: int, size_bytes: int, size_lines: int,
  skill: tuple[str, str, str] | None) -> str`, where `skill` is
  the name, the directory and the files hash, which gives the lines joined by
  `"\n"` and builds the command line from `work_id`, `action` and `stage_name`.
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
  the stage, and it has `gate: yes, judged by a person` and `session: fresh`, in
  the provisional wording.

#### A stage that is not a gate

- **Given** a stage with no `gate`, no `session` and `continuable = false`, and
  another with `judge = "human"` and no `gate`.
- **When** the header is built for each.
- **Then** each has `gate: no`, the first has
  `session: any, do not continue it`, and neither says that a person judges.

#### A fresh stage that is not continuable, and a Work with no title

- **Given** a stage with `session = "fresh"` and `continuable = false`, and a
  Work with no title.
- **When** the header is built.
- **Then** it has `session: fresh, do not continue it`, and the Work's line is
  `work:` and the id alone.

### **AC-2** The header states what the session received

The header gives the number of rules and the size of the body in bytes and
lines, in the provisional wording.

#### Three rules, and none

- **Given** the counts 1234 bytes and 56 lines with three rules, and the same
  counts with no rule.
- **When** the header is built for each.
- **Then** the first has `rules: 3` and `size: 1234 bytes, 56 lines (body)`, and
  the second has `rules: 0`.

### **AC-3** The header states the canonical command

The header states the command that the Glossary defines, for the Work, the
action and the stage as parsed.

#### A request

- **Given** the Work id `k3m9xq`, the action `deliver` and the stage name
  `architecture`.
- **When** the header is built.
- **Then** its command line is `command: wio context k3m9xq deliver
  architecture`, in the provisional wording of the label.

### **AC-4** A stage with a skill names where it was found

The header names the skill, the directory it was found in, relative to the
repository, and the hash of its files, and a stage with a goal has no such line.

#### A skill and a goal

- **Given** a stage with the skill `wio-define` found in `.agents/skills` and a
  stage with a goal.
- **When** the header is built for each.
- **Then** the first names `wio-define`, `.agents/skills/wio-define` and the
  hash it was given, and the second has no skill line.

### **AC-5** The header is one block

The header holds no blank line and does not end with a newline.

#### Every kind of header

- **Given** the headers of AC-1 to AC-4.
- **When** each is examined.
- **Then** none contains an empty line or ends with `"\n"`.
