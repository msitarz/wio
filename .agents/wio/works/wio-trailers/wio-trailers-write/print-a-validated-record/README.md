<!-- wio
id = "eh62g6"
template = "feature.leaf"
roots = ["wio"]
depends_on = ["pnf585"]
-->

# Print a validated record

## Purpose

An agent that types a record by hand gets a name, an id, an item or a result
wrong, so the engine hands it a record whose fields are known to hold.

## Goals

- A record for a named Work, action and stage, with optional item ids, is
  printed when every field holds.
- A field that does not hold is refused and no record is printed.
- A stage outside the Work's pipeline is warned about and the record is still
  printed.
- One validator owns every check of a record's fields, so the write command and
  the commit-time check cannot disagree.

## Non-Goals

- Writing one record for a list of Works and `wio trailers none`; a comma list
  in `<work>` is a usage error.
- The judge, the cited items and the `review` event; the gate leaf adds them.
- Editing a commit message; the agent adds the printed paragraph.

## Assumptions

### A-1

A comma list in `<work>` is a usage error here, though concepts.md allows a
list, because this leaf writes one record for one Work and a later Work may add
the list.

## Mechanisms

- **`wio trailers <work> <action> <stage> [--items IDS] [--result RESULT]`** —
  prints the record on standard output, one paragraph of `Key: value` lines in
  the order `Wio-Work`, `Wio-Action`, `Wio-Stage`, `Wio-Items`, `Wio-Result` and
  `Wio-Judge`, ending with one newline. `IDS` are separated by a comma on the
  command line and by a comma and one space in the record, in the order given.
  It prints errors and warnings on standard error as
  `<severity>: <where>: <message>` and prints nothing on standard output when a
  field is refused. It exits 0 on success or a warning, 1 when a field is
  refused, and 2 on a usage error or a `WioError`, such as an unknown option or
  a config that cannot be read. It also accepts `--judge` and `--cite`, whose
  checks and effects are the gate leaf's.
- **`render(fields: Mapping[str, str]) -> str`** — the record renderer, built
  here in `wio.formats`, which renders any of the six keys in that order and
  which the gate leaf reuses for the result and the judge.
- **`validate_record(record: Record, source: WorkSource) -> list[Diagnostic]`**
  — the field validator, which this leaf owns and the commit-time check of
  `vy01kg` reuses, with a `Diagnostic` of a severity, a position and a message.
  It checks that each Work is in `source` or in `HEAD`, which it reads through
  `History.show`; that the items are among the Work's own; that the action and
  stage are in the config; that the result, when present, is one of
  `gates.results`; that a result is present exactly on a gate; and, as a
  warning, that the stage is in the Work's action. `source` is the working tree
  for the write command and the index for the commit-time check.

## Acceptance criteria

The examples use a Work `k3m9xq` in the working tree with the items `AC-1` and
`AC-3`. Its `deliver` action lists the stages `architecture`, which is not a
gate, and `architecture-review`, which is a gate. The config also has the stage
`wiring`, which `k3m9xq`'s `deliver` does not list, and its results are `pass`,
`fail` and `unknown`.

### **AC-1** A valid record is printed

#### A Work, an action, a stage and items

- **Given** `k3m9xq`.
- **When** `wio trailers k3m9xq deliver architecture --items AC-3,AC-1` runs.
- **Then** it prints exactly the four lines `Wio-Work: k3m9xq`,
  `Wio-Action: deliver`, `Wio-Stage: architecture` and
  `Wio-Items: AC-3, AC-1`, each ending with a newline, and exits 0.

### **AC-2** The Work must exist

#### A Work that exists nowhere

- **Given** a Work id `zz9zz9` that is in neither the working tree nor `HEAD`.
- **When** `wio trailers zz9zz9 deliver architecture` runs.
- **Then** the command exits 1, prints nothing on standard output and names
  `zz9zz9` on standard error.

#### A Work that the commit deletes

- **Given** a Work `d4e5f6` that is in `HEAD` and not in the working tree, whose
  contract at `HEAD` lists `deliver` with the stage `architecture`.
- **When** `wio trailers d4e5f6 deliver architecture` runs.
- **Then** it prints the record and exits 0.

### **AC-3** The names must be in the config

#### An action the config does not have

- **Given** `k3m9xq`.
- **When** `wio trailers k3m9xq nosuch architecture` runs.
- **Then** the command exits 1, prints nothing on standard output and names
  `nosuch` on standard error.

#### A stage the config does not have

- **Given** `k3m9xq`.
- **When** `wio trailers k3m9xq deliver nosuch` runs.
- **Then** the command exits 1, prints nothing on standard output and names
  `nosuch` on standard error.

### **AC-4** The items must be the Work's own

#### An item id the Work does not have

- **Given** `k3m9xq`, which has no item `AC-99`.
- **When** `wio trailers k3m9xq deliver architecture --items AC-99` runs.
- **Then** the command exits 1, prints nothing on standard output and names
  `AC-99` on standard error.

### **AC-5** A result is present exactly on a gate and is one the config lists

#### A gate without a result

- **Given** the gate stage `architecture-review`.
- **When** `wio trailers k3m9xq deliver architecture-review` runs.
- **Then** the command exits 1, prints nothing on standard output and reports
  that a result is required.

#### A result on a stage that is not a gate

- **Given** the stage `architecture`, which is not a gate.
- **When** `wio trailers k3m9xq deliver architecture --result pass` runs.
- **Then** the command exits 1, prints nothing on standard output and reports
  that the stage is not a gate.

#### A result the config does not list

- **Given** the gate stage `architecture-review`.
- **When** `wio trailers k3m9xq deliver architecture-review --result maybe`
  runs.
- **Then** the command exits 1, prints nothing on standard output and names
  `maybe` on standard error.

### **AC-6** A stage outside the Work's pipeline is a warning

#### A stage that the Work's actions do not list

- **Given** `k3m9xq`, whose `deliver` does not list `wiring`.
- **When** `wio trailers k3m9xq deliver wiring` runs.
- **Then** the record is on standard output, the warning naming `wiring` is on
  standard error, and the command exits 0.

### **AC-7** A usage error exits 2

#### A call with no stage

- **Given** a call that gives a Work and an action and no stage.
- **When** `wio trailers k3m9xq deliver` runs.
- **Then** the command exits 2 and prints nothing on standard output.

#### An unknown option and a list of Works

- **Given** the option `--nosuch`, and the Work value `k3m9xq,a7b2c4`.
- **When** `wio trailers k3m9xq deliver architecture --nosuch` and
  `wio trailers k3m9xq,a7b2c4 deliver architecture` run.
- **Then** each exits 2 and prints nothing on standard output.
