<!-- wio
id = "jyhy64"
template = "feature.leaf"
roots = ["wio"]
depends_on = ["eh62g6"]
-->

# Record a gate's result

## Purpose

A gate's review leaves no trace of the items it cited or of the commit it saw,
and a gate that needs a human can be recorded as judged by an agent, so the
engine records the citations and the reviewed commit and refuses that judge.

## Goals

- A gate that needs a human is never recorded as judged by an agent.
- The items a review cites are checked and sent with the result.
- The commit a review judged is found from the history, past the pure gate
  commits above it, and named in the `review` event.

## Non-Goals

- Printing the record with its result and judge; the print leaf does that.
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

The reviewed commit is the one that concepts.md defines: the first commit
reachable from `HEAD` by first parents that is not a pure gate commit of this
gate.

## Mechanisms

- **`wio trailers <work> <action> <stage> --result RESULT --cite ITEM=RESULT`**
  — extends the print leaf's command: it refuses `agent` for a gate with
  `judge = "human"`, checks the cited items, and hands the `review` event to the
  `EventSink`.
- **`History` port** — gives the commits from `HEAD` for the walk.
- **`EventSink` port** — receives the `review` event.

## Acceptance criteria

### **AC-1** A human gate refuses an agent

#### An agent for a gate with `judge = "human"`

- **Given** a gate stage whose config says `judge = "human"`.
- **When** `wio trailers <work> <action> <stage> --result pass` runs, and when
  it runs with `--judge agent`.
- **Then** each exits 1, prints no record and says the gate needs a human judge.

#### A human for a gate with `judge = "human"`

- **Given** the same gate stage.
- **When** `wio trailers <work> <action> <stage> --result pass --judge human`
  runs.
- **Then** the printed record holds `Wio-Judge: human`.

### **AC-2** The cited items are checked

#### A rule code the config does not choose

- **Given** a gate stage and a config that chooses no rule `ZZZ999`.
- **When** `wio trailers <work> <action> <stage> --result pass --cite
  ZZZ999=fail` runs.
- **Then** the command exits 1, prints no record and names `ZZZ999`.

#### An item id outside the Work

- **Given** a Work that has no item `AC-99`.
- **When** the same command runs with `--cite AC-99=pass`.
- **Then** the command exits 1, prints no record and names `AC-99`.

#### A cited result outside the vocabulary

- **Given** a Work with an item `AC-1`.
- **When** the same command runs with `--cite AC-1=maybe`.
- **Then** the command exits 1, prints no record and names `maybe`.

### **AC-3** The reviewed commit is found past the pure gate commits

#### One or more pure gate commits above the work commit

- **Given** commits on `HEAD` where one or more of the latest carry only
  records for this gate's action and stage, and the next earlier commit is the
  work commit, and a recording `EventSink`.
- **When** `wio trailers <work> <action> <stage> --result pass` runs.
- **Then** the sink receives one `review` event whose reviewed commit is the
  work commit's sha.

#### A commit with another record is not skipped

- **Given** the latest commit carries this gate's record together with a record
  of another action or stage.
- **When** the same command runs.
- **Then** the reviewed commit is that latest commit.

#### A commit with no record is not skipped

- **Given** the latest commit carries no record.
- **When** the same command runs.
- **Then** the reviewed commit is that latest commit.

### **AC-4** The review event carries the judgment

#### The event for a cited review

- **Given** a gate stage, a Work with an item `AC-1` and a recording
  `EventSink`.
- **When** `wio trailers <work> <action> <stage> --result pass --judge human
  --cite AC-1=pass` runs.
- **Then** the sink receives one `review` event naming the Work, action, stage,
  reviewed commit, the judge `human`, the result `pass` and `AC-1` with `pass`.
