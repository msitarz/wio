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

- Writing one record for a list of Works and `wio trailers none`.
- Refusing `agent` for a gate that needs a human, the cited items, the reviewed
  commit and the `review` event; the gate leaf adds them.
- Editing a commit message; the agent adds the printed paragraph.

## Assumptions

### A-1

A comma list in `<work>` is a usage error here, though concepts.md allows a
list, because this leaf writes one record for one Work and a later Work may add
the list.

## Mechanisms

- **`wio trailers <work> <action> <stage> [--items IDS] [--result RESULT]
  [--judge JUDGE]`** —
  prints the record on standard output, one paragraph of `Key: value` lines in
  the order `Wio-Work`, `Wio-Action`, `Wio-Stage`, `Wio-Items`, `Wio-Result` and
  `Wio-Judge`, ending with one newline. `IDS` are separated by a comma on the
  command line and by a comma and one space in the record, in the order given.
  It prints errors and warnings on standard error as
  `<severity>: <where>: <message>` and prints nothing on standard output when a
  field is refused. It exits 0 on success or a warning, 1 when a field is
  refused, and 2 on a usage error or a `WioError`, such as an unknown option or
  a config that cannot be read. When a result is given it also prints
  `Wio-Judge`, `agent` by default and `human` or `agent` with `--judge`, as
  concepts.md says; `--cite` is accepted and handled by the gate leaf.
- **`render(fields: Mapping[str, str]) -> str`** — the record renderer, built
  here in `wio.formats`, which renders any of the six keys in that order and
  which the gate leaf reuses for the result and the judge.
- **`validate_record(record: Record, source: WorkSource) -> list[Diagnostic]`**
  — the field validator, in `wio.trailers`, which this leaf owns and the
  commit-time check of `vy01kg` reuses. A `Record` is the `Wio-*` key and value
  pairs of one record of the shape leaf's `Reading`, a `WorkSource` is a
  protocol with `contract(work_id: str) -> str | None`, the text of a Work's
  contract in the working tree or the index, and a `Diagnostic` is a frozen
  value of `severity: Literal["error", "warning"]`, `where: str` and
  `message: str`. For a message `where` is a line number, and for the write
  command it is the key of the field. A record of `Wio-Work: none` has no Work
  to check and no diagnostic. The validator checks that each Work is in `source`
  or in `HEAD`, which it reads through `History.show`; that the items are among
  the Work's own; that the action and stage are in the config; that the result,
  when present, is one of `gates.results`; that a result is present exactly on a
  gate; and, as a warning, that the stage is in the Work's action. `source` is
  the working tree for the write command and the index for the commit-time
  check, each with the fallback to `HEAD`.

## Acceptance criteria

The examples use a Work `k3m9xq` in the working tree with the items `AC-1` and
`AC-3`. It is a leaf, so its `deliver` is the `typed-boundary` stage preset,
which lists the stages `architecture`, which is not a gate, and
`architecture-review`, which is a gate. The config also has the stage
`integration`, which that preset does not list, and its results are `pass`,
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

- **Given** a leaf Work `d4e5f6` that is in `HEAD` and not in the working tree.
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
  `result required` on standard error.

#### A result on a stage that is not a gate

- **Given** the stage `architecture`, which is not a gate.
- **When** `wio trailers k3m9xq deliver architecture --result pass` runs.
- **Then** the command exits 1, prints nothing on standard output and reports
  `not a gate` on standard error.

#### A result the config does not list

- **Given** the gate stage `architecture-review`.
- **When** `wio trailers k3m9xq deliver architecture-review --result maybe`
  runs.
- **Then** the command exits 1, prints nothing on standard output and names
  `maybe` on standard error.

#### A gate with a listed result

- **Given** the gate stage `architecture-review`.
- **When** `wio trailers k3m9xq deliver architecture-review --result pass`
  runs, and again with `--judge human`.
- **Then** each prints the lines `Wio-Work`, `Wio-Action`, `Wio-Stage`,
  `Wio-Result: pass` and then `Wio-Judge: agent` for the first and
  `Wio-Judge: human` for the second, and exits 0.

#### A judge that is not human or agent

- **Given** the gate stage `architecture-review`.
- **When** `wio trailers k3m9xq deliver architecture-review --result pass
  --judge robot` runs.
- **Then** the command exits 1, prints nothing on standard output and names
  `robot` on standard error.

### **AC-6** A stage outside the Work's pipeline is a warning

#### A stage that the Work's actions do not list

- **Given** `k3m9xq`, whose `deliver` does not list `integration`.
- **When** `wio trailers k3m9xq deliver integration` runs.
- **Then** the record is on standard output, the warning naming `integration` is
  on standard error, and the command exits 0.

### **AC-7** A usage error exits 2

#### A call with no stage

- **Given** a call that gives a Work and an action and no stage.
- **When** `wio trailers k3m9xq deliver` runs.
- **Then** the command exits 2 and prints nothing on standard output.

#### An unknown option and a list of Works

- **Given** the option `--nosuch`, and the Work value `k3m9xq,a7b2c4`, which
  this leaf does not write (A-1).
- **When** `wio trailers k3m9xq deliver architecture --nosuch` and
  `wio trailers k3m9xq,a7b2c4 deliver architecture` run.
- **Then** each exits 2 and prints nothing on standard output.

### **AC-8** The validator is the one both commands use

#### The same diagnostics from two sources

- **Given** a `Record` of `Wio-Work: k3m9xq` with `Wio-Stage: nosuch`, and a
  `Record` of `Wio-Work: d4e5f6`, a Work only in `HEAD`.
- **When** `validate_record` runs on each with a working-tree `WorkSource` and
  with an index-like `WorkSource`.
- **Then** it returns an error `Diagnostic` naming `nosuch` for the first, and
  no error for the second, with either source.

### **AC-9** A malformed field is refused

#### Items and a Work id of the wrong form

- **Given** `k3m9xq`.
- **When** `wio trailers k3m9xq deliver architecture --items "AC-1 AC-3"` and
  `wio trailers "k3 m9xq" deliver architecture` run.
- **Then** each exits 1, prints nothing on standard output and names the value
  on standard error.
