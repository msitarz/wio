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

## Non-Goals

- Printing the record with its result and judge; the print leaf does that.
- Finding the reviewed commit; the reviewed-commit leaf does that.
- Writing one record for a list of Works.
- The `--reviewed` override, and the warnings that compare the reviewed commit
  with the `context` event.
- Writing the event to the event log; the `EventSink` wired to the command is a
  no-op until `wio log` exists.
- Stopping an agent from claiming a human judged; `wio trailers` refuses
  `agent` for a human gate and cannot prove who typed `human`.
- Making the agent wait for the driver before the next stage.

## Assumptions

### A-1

A key of `--cite` is an item id when the Work has that item, and otherwise it
must be a qualified `ruleset.CODE` that the stage's rules contain, which settles
the open point of concepts.md about telling them apart.

### A-2

The `review` event holds what concepts.md lists, and the `wio log` Work fixes
its types, because `src/wio/models/events.pyi` declares no fields.

## Mechanisms

- **`wio trailers <work> <action> <stage> --result RESULT --cite KEY=RESULT`**
  — extends the print leaf's command, with `--cite` repeatable and refused
  without `--result` or with a key repeated, and a refusal prints on standard
  error as `error: <key>: <message>`.
- **The event** — `EventSink.write(ReviewEvent)`, written once after every check
  passed, never on a refusal, still after a warning, and whose failure never
  changes the exit code.
- **The content of the event** — the Work, the action, the stage, the reviewed
  commit as a full sha, the judge, the result, and each cited result, with the
  file hash of a cited rule.
- **The reviewed commit** — found by the `reviewed_commit` of the
  reviewed-commit leaf, from the action and the stage,
  and when it returns `None` the command exits 1 and reports that no reviewed
  commit was found.

## Acceptance criteria

The examples use a Work `k3m9xq`, hypothetical, with the items `AC-1` and
`AC-3`, and the gate `docs-review`, whose config says `judge = "human"`. A
recording `EventSink` is injected, and the history holds a work commit under a
pure gate commit.

### **AC-1** A human gate refuses an agent

#### An agent for a gate with `judge = "human"`

- **Given** `k3m9xq` and `docs-review`.
- **When** `wio trailers k3m9xq deliver docs-review --result pass` runs, and
  again with `--judge agent`.
- **Then** each exits 1, prints nothing on standard output, prints
  `error: Wio-Judge:` on standard error and the sink receives no event.

#### A human for the same gate

- **Given** the same gate.
- **When** the command runs with `--judge human`.
- **Then** the printed record holds `Wio-Judge: human`, it exits 0 and the sink
  receives one event.

### **AC-2** The cited items and rules are checked

#### A cite that is refused

- **Given** `k3m9xq`, and a rule `contracts.CON001` that the stage's rules do
  not contain.
- **When** the command runs with `--cite contracts.CON001=fail`,
  `--cite AC-99=pass`, `--cite AC-1=maybe`, `--cite AC-1=pass --cite AC-1=fail`
  and `--cite AC-1=pass` without `--result`.
- **Then** each exits 1, prints nothing on standard output, names the key on
  standard error, and the sink receives no event.

#### A cite that is accepted

- **Given** `k3m9xq` and a rule `docs.DOC001` that the stage's rules contain.
- **When** the command runs with `--cite AC-1=pass --cite docs.DOC001=fail`.
- **Then** it exits 0 and the sink receives one event that cites `AC-1` with
  `pass` and `docs.DOC001` with `fail` and the file hash of `docs.DOC001`.

### **AC-3** The event names the reviewed commit and the judgment

#### The event of a cited review

- **Given** `k3m9xq`, a history of the pure gate commit `c2` above the work
  commit `c1`, and a recording `EventSink`.
- **When** `wio trailers k3m9xq deliver docs-review --result pass --judge human
  --cite AC-1=pass` runs.
- **Then** the sink receives one event with `k3m9xq`, the action, `docs-review`,
  the full sha of `c1`, the judge `human`, the result `pass` and `AC-1` with
  `pass`.

#### A history with no reviewed commit

- **Given** a history of commits that each carry only a gate record.
- **When** the same command runs.
- **Then** it exits 1, reports that no reviewed commit was found and the sink
  receives no event.

### **AC-4** The event is written once and never fails the command

#### A warning, and a sink that fails

- **Given** the gate `system-review`, which `k3m9xq`'s `deliver` does not list,
  and a sink whose write fails.
- **When** `wio trailers k3m9xq deliver system-review --result pass` runs with a
  working sink and with the failing one.
- **Then** the first prints its warning and the sink receives one event, and the
  second still exits 0.
