<!-- wio
id = "eh62g6"
template = "feature.leaf"
roots = ["wio"]
depends_on = ["pnf585", "hk3qt5", "jzvrtx"]
-->

# Print a validated record

## Purpose

An agent that types a record by hand gets a name, an id, an item or a result
wrong, so the engine hands it a record whose fields are known to hold.

## Goals

- A record for a named Work, action and stage, with optional item ids, a result
  and a judge, is printed when every field holds.
- A field that does not hold is refused and no record is printed.
- A stage outside the Work's pipeline is warned about and the record is still
  printed.

## Non-Goals

- Writing one record for a list of Works and `wio trailers none`.
- Refusing `agent` for a gate that needs a human, the cited items, the reviewed
  commit and the `review` event; the gate leaf adds them.

## Assumptions

### A-1

A comma list or `none` in `<work>` is a usage error here, though concepts.md
allows both, because this leaf writes one record for one Work and a later Work
may add the rest.

## Mechanisms

- **`wio trailers <work> <action> <stage> [--items IDS] [--result RESULT]
  [--judge JUDGE]`** — prints the record on standard output, one paragraph of
  `Key: value` lines in the order `Wio-Work`, `Wio-Action`, `Wio-Stage`,
  `Wio-Items`, `Wio-Result` and `Wio-Judge`, ending with one newline. `IDS` are
  separated by a comma on the command line and by a comma and one space in the
  record, in the order given. When a result is given it also prints
  `Wio-Judge`, `agent` by default and `human` or `agent` with `--judge`, as
  concepts.md says; `--judge` without a result is refused. `--cite` is accepted
  and ignored here, and the gate leaf handles it.
- **Checks** — the command applies the shape leaf's form check to the record it
  builds, and then the validator of the validator leaf with the working tree as
  its source of Works. It prints each error and warning on standard error as
  `<severity>: <where>: <message>`, where `<where>` is the key of the field, and
  prints nothing on standard output when there is an error.
- **Exit codes** — 0 on success or a warning, 1 when a field is refused, and 2
  on a usage error or a `WioError`, such as an unknown option or a config that
  cannot be read.
- **`render(fields: Mapping[str, str]) -> str`** — the record renderer, built
  here in `wio.formats`, which renders any of the six keys in that order and
  which the gate leaf reuses.

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

#### A gate with a listed result

- **Given** the gate stage `architecture-review`.
- **When** `wio trailers k3m9xq deliver architecture-review --result pass`
  runs, and again with `--judge human`.
- **Then** each prints the lines `Wio-Work`, `Wio-Action`, `Wio-Stage`,
  `Wio-Result: pass` and then `Wio-Judge: agent` for the first and
  `Wio-Judge: human` for the second, and exits 0.

### **AC-2** A refused field prints no record

#### A Work and a stage that are not valid

- **Given** a Work id `zz9zz9` that exists nowhere, and `k3m9xq`.
- **When** `wio trailers zz9zz9 deliver architecture` and
  `wio trailers k3m9xq deliver nosuch` run.
- **Then** each exits 1, prints nothing on standard output and prints
  `error: Wio-Work:` and `error: Wio-Stage:` lines on standard error that name
  `zz9zz9` and `nosuch`.

#### A result that does not fit its stage

- **Given** the gate stage `architecture-review` and the stage `architecture`.
- **When** `wio trailers k3m9xq deliver architecture-review` and
  `wio trailers k3m9xq deliver architecture --result pass` run.
- **Then** each exits 1, prints nothing on standard output and reports
  `result required` and `not a gate` on standard error.

### **AC-3** The form of the arguments is checked

#### Malformed items, Work id and judge

- **Given** `k3m9xq`.
- **When** `wio trailers k3m9xq deliver architecture --items "AC-1 AC-3"`,
  `wio trailers "k3 m9xq" deliver architecture` and
  `wio trailers k3m9xq deliver architecture-review --result pass --judge robot`
  run.
- **Then** each exits 1, prints nothing on standard output and names the value
  on standard error.

#### A judge without a result

- **Given** `k3m9xq`.
- **When** `wio trailers k3m9xq deliver architecture --judge human` runs.
- **Then** the command exits 1, prints nothing on standard output and names
  `Wio-Judge` on standard error.

### **AC-4** A stage outside the Work's pipeline is a warning

#### A stage that the Work's actions do not list

- **Given** `k3m9xq`, whose `deliver` does not list `integration`.
- **When** `wio trailers k3m9xq deliver integration` runs.
- **Then** the record is on standard output, the warning naming `integration` is
  on standard error, and the command exits 0.

### **AC-5** A usage error exits 2

#### A call with no stage

- **Given** a call that gives a Work and an action and no stage.
- **When** `wio trailers k3m9xq deliver` runs.
- **Then** the command exits 2 and prints nothing on standard output.

#### An unknown option, a list of Works and none

- **Given** the option `--nosuch`, the Work value `k3m9xq,a7b2c4` and the Work
  value `none`, which this leaf does not write (A-1).
- **When** `wio trailers k3m9xq deliver architecture --nosuch`,
  `wio trailers k3m9xq,a7b2c4 deliver architecture` and
  `wio trailers none deliver architecture` run.
- **Then** each exits 2 and prints nothing on standard output.
