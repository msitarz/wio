<!-- wio
id = "jyhy64"
template = "feature.leaf"
roots = ["wio"]
depends_on = ["eh62g6", "92xps9"]
-->

# Record a gate's result

## Purpose

A gate that needs a human can be recorded as judged by an agent, and a review
leaves no trace of the items it cited or of the commit it saw, so the engine
refuses that judge and records the citations and the reviewed commit.

## Goals

- A gate that needs a human is never recorded as judged by an agent.
- The items and rules a review cites are checked and sent with the result.
- The commit a review judged is named in the `review` event.
- The event is written once after every check passed, and a sink that fails
  never fails the command.

## Non-Goals

- Printing the record with its result and judge; the print leaf does that.
- Finding the reviewed commit; the reviewed-commit leaf does that.
- Selecting the rules of a stage and hashing their files; the rules Work does
  that, and this leaf consumes a port for it.
- Writing one record for a list of Works.
- The `--reviewed` override, and the warnings that compare the reviewed commit
  with the `context` event.
- Writing the event to the event log, which constraint C-4 of the top parent
  defers to `wio log`.
- Stopping an agent from claiming a human judged; `wio trailers` refuses
  `agent` for a human gate and cannot prove who typed `human`.
- Making the agent wait for the driver before the next stage.

## Assumptions

### A-1

A key of `--cite` is an item id when the Work has that item, and otherwise it
must be a qualified `ruleset.CODE` that the stage selects, which is stricter
than the config choosing it and settles the open point of concepts.md about
telling them apart.

### A-2

The `review` event holds what concepts.md lists, and the `wio log` Work fixes
its types, because `src/wio/models/events.pyi` declares no fields.

### A-3

The hash of a cited rule is the hash of its file that the `context` event
records, and the rules Work settles how it is computed.

## Mechanisms

- **`wio trailers <work> <action> <stage> --result RESULT --cite KEY=RESULT`**
  — extends the print leaf's command, with `--cite` repeatable, and replaces the
  print leaf's scenario "A cited item is ignored".
- **The order of refusals** — the print leaf's field errors come first, then the
  human-gate refusal, then the cite refusals, and the first group that finds
  something prints and stops.
- **Cite refusals** — a cite with no `=`, an empty key or result, a key
  repeated, a result outside `gates.results`, an item the Work lacks, a code
  that is not qualified or that the stage does not select, and `--cite` without
  `--result` are each refused with exit 1 and print `error: <name>: <message>`
  on standard error, the name being `--cite` for a cite with no `=`, an empty
  name or an empty result and for `--cite` without `--result`, and the cite's
  own name otherwise.
- **Human-gate refusal** — read from the stage's `judge = "human"`, an `agent`
  judge, given or by default, is refused with `error: Wio-Judge: <message>`,
  and wins over a cite refusal.
- **Stage rules port** — a provisional port of `wio.trailers` that gives the
  qualified codes of the rules a stage selects for a Work with the hash of each
  rule's file, which the rules component satisfies and which the criteria fake.
- **The reviewed commit** — found by the `reviewed_commit` of the
  reviewed-commit leaf from the action and the stage, and when it returns `None`
  the command exits 1, prints nothing on standard output and prints
  `error: Wio-Work: no reviewed commit was found`.
- **The event** — `EventSink.write(ReviewEvent)` holds the Work, the action, the
  stage, the reviewed commit as a full sha, the judge, the result, each cited
  key with its result and, for a rule, its hash; it is written once after every
  check passed, never on a refusal, still after a warning, and a sink whose
  write fails is reported as a warning on standard error without changing the
  exit code.

## Acceptance criteria

The examples use a Work `k3m9xq`, hypothetical, with the items `AC-1` and
`AC-3`, and the action `deliver`. The gate `docs-review` has `judge = "human"`,
and the stage rules port, faked, gives `docs.DOC001` with the hash `h1` for it
and no `contracts.CON001`. A recording `EventSink` is injected, and the history
holds a work commit under a pure gate commit.

### **AC-1** A human gate refuses an agent

#### An agent for a gate with `judge = "human"`

- **Given** `k3m9xq` and `docs-review`.
- **When** `wio trailers k3m9xq deliver docs-review --result pass` runs, and
  again with `--judge agent`.
- **Then** each exits 1, prints nothing on standard output, prints
  `error: Wio-Judge:` on standard error and the sink receives no event.

#### The human-gate refusal comes before a cite refusal

- **Given** the same gate.
- **When** `wio trailers k3m9xq deliver docs-review --result pass --cite
  AC-99=pass` runs, with no `--judge`.
- **Then** it exits 1, prints `error: Wio-Judge:` on standard error and no line
  about `AC-99`.

#### A human for the same gate

- **Given** the same gate.
- **When** the command runs with `--judge human`.
- **Then** the printed record holds `Wio-Judge: human`, it exits 0 and the sink
  receives one event.

### **AC-2** The cited items and rules are checked

#### A cite that is refused

- **Given** `k3m9xq` and the gate `docs-review`.
- **When** `wio trailers k3m9xq deliver docs-review --result pass --judge human`
  runs with each of `--cite contracts.CON001=fail`, `--cite AC-99=pass`,
  `--cite AC-1=maybe`, `--cite AC-1`, `--cite =pass`, `--cite AC-1=`,
  `--cite AC-1=pass --cite AC-1=fail` and `--cite DOC001=fail`.
- **Then** each exits 1, prints nothing on standard output and prints on
  standard error an `error:` line that names, in turn, `contracts.CON001`,
  `AC-99`, `AC-1`, `--cite`, `--cite`, `--cite`, `AC-1` and `DOC001`, and the
  sink receives no event.

#### A cite without a result

- **Given** `k3m9xq` and the stage `architecture`, which is not a gate.
- **When** `wio trailers k3m9xq deliver architecture --cite AC-1=pass` runs.
- **Then** it exits 1, prints nothing on standard output and prints
  `error: --cite:` on standard error.

#### A cite that is accepted

- **Given** `k3m9xq` and the gate `docs-review`.
- **When** the command runs with `--result pass --judge human --cite
  AC-1=pass --cite docs.DOC001=fail`.
- **Then** it exits 0 and the sink receives one event that cites `AC-1` with
  `pass` and `docs.DOC001` with `fail` and the hash `h1`.

### **AC-3** The event names the reviewed commit and the judgment

#### The event of a cited review

- **Given** `k3m9xq`, a history of the pure gate commit `c2` above the work
  commit `c1`, and the recording `EventSink`.
- **When** `wio trailers k3m9xq deliver docs-review --result pass --judge human
  --cite AC-1=pass` runs.
- **Then** the sink receives one event with `k3m9xq`, `deliver`, `docs-review`,
  the full sha of `c1`, the judge `human`, the result `pass` and `AC-1` with
  `pass`.

#### A history with no reviewed commit

- **Given** a history of commits that each carry only a gate record.
- **When** the same command runs.
- **Then** it exits 1, prints nothing on standard output, prints
  `error: Wio-Work: no reviewed commit was found` on standard error and the
  sink receives no event.

### **AC-4** A warning does not stop the event

#### A stage outside the Work's pipeline

- **Given** the gate `system-review`, which is outside the `typed-boundary`
  preset that is `k3m9xq`'s `deliver`.
- **When** `wio trailers k3m9xq deliver system-review --result pass` runs.
- **Then** it prints a warning naming `system-review` on standard error, exits 0
  and the sink receives one event.

### **AC-5** A failing sink never fails the command

#### A sink that reports its failure

- **Given** a sink whose write fails and which reports the failure itself as a
  warning on standard error, without raising, as the `EventSink` port says.
- **When** `wio trailers k3m9xq deliver docs-review --result pass --judge human`
  runs.
- **Then** the warning of the sink is on standard error, the record is on
  standard output and the command exits 0.
