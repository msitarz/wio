<!-- wio
id = "eh62g6"
template = "feature.leaf"
roots = ["wio"]
depends_on = []
-->

# Print a validated record

## Purpose

An agent that types a record by hand gets a name, an id or an item wrong, so the
engine prints the record after checking each field.

## Goals

- A record for a named Work, action and stage, with optional item ids, is
  printed when every field holds.
- A field that does not hold is refused and no record is printed.
- A stage outside the Work's pipeline is warned about and the record is still
  printed.

## Non-Goals

- Writing one record for a list of Works and `wio trailers none`.
- Checking the value of `--result` and `--judge` and the cited items; the gate
  leaf does that.
- Editing a commit message; the agent adds the printed paragraph.

## Assumptions

### A-1

A stage that is a gate needs a result, and a stage that is not a gate must not
have one, as concepts.md says. The gate leaf accepts the result; this leaf only
refuses a gate stage without one and a non-gate stage with one.

## Mechanisms

- **`wio trailers <work> <action> <stage>`** — prints one record paragraph and
  exits 1 when a field is refused.
- **Record renderer** — the shared renderer that produces the paragraph.
- **`History` port** — finds a Work that the commit being made deletes, which is
  in `HEAD` and no longer in the index.

## Acceptance criteria

### **AC-1** A valid record is printed

#### A Work, an action, a stage and an item

- **Given** a Work in the working tree with an item `AC-1`, and a stage of its
  actions that is not a gate.
- **When** `wio trailers <work> <action> <stage> --items AC-1` runs.
- **Then** it prints a paragraph holding `Wio-Work`, `Wio-Action`, `Wio-Stage`
  and `Wio-Items: AC-1`, and exits 0.

### **AC-2** The Work must exist

#### A Work that exists nowhere

- **Given** a Work id that is in neither the working tree nor `HEAD`.
- **When** `wio trailers <work> <action> <stage>` runs.
- **Then** the command exits 1, prints no record and names the Work.

#### A Work that the commit deletes

- **Given** a Work that is in `HEAD` and no longer in the index.
- **When** `wio trailers <work> <action> <stage>` runs.
- **Then** it prints the record and exits 0.

### **AC-3** The names must be in the config

#### An action or a stage the config does not have

- **Given** an action `nosuch`, and a stage `nosuch`.
- **When** `wio trailers <work> nosuch <stage>` and
  `wio trailers <work> <action> nosuch` run.
- **Then** each exits 1, prints no record and names the unknown name.

### **AC-4** The items must be the Work's own

#### An item id the Work does not have

- **Given** a Work that has no item `AC-99`.
- **When** `wio trailers <work> <action> <stage> --items AC-99` runs.
- **Then** the command exits 1, prints no record and names `AC-99`.

### **AC-5** A result is present exactly on a gate

#### A gate without a result

- **Given** a stage that is a gate.
- **When** `wio trailers <work> <action> <stage>` runs without `--result`.
- **Then** the command exits 1, prints no record and reports that a result is
  required.

#### A result on a stage that is not a gate

- **Given** a stage that is not a gate.
- **When** `wio trailers <work> <action> <stage> --result pass` runs.
- **Then** the command exits 1, prints no record and reports that the stage is
  not a gate.

### **AC-6** A stage outside the Work's pipeline is a warning

#### A stage that the Work's actions do not list

- **Given** a stage that the config has and the Work's actions do not list.
- **When** `wio trailers <work> <action> <stage>` runs.
- **Then** it prints the record, warns about the stage and exits 0.

### **AC-7** A usage error exits 2

#### A call with no stage

- **Given** a call that gives a Work and an action and no stage.
- **When** `wio trailers <work> <action>` runs.
- **Then** the command exits 2 and prints no record.
