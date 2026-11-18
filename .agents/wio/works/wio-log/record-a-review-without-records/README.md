<!-- wio
id = "9m32d0"
template = "feature.leaf"
roots = ["wio"]
depends_on = ["7v8amt", "zj4ja0"]
-->

# Record a review without records

## Purpose

A workflow that keeps no `Wio-*` records in its commits still has gates, and
their reviews would leave no trace; the engine needs a command that records a
review in the log alone.

## Goals

- A review is recorded in the log with one command, and no record is printed.
- The command checks what `wio trailers --result` checks and writes the event
  it writes, so a log does not show which command wrote it.
- A refusal writes nothing.

## Non-Goals

- Printing a record, or adding a record to a commit.
- A list of Works, which `wio trailers` takes later and this command takes at
  the same time.
- The `--reviewed` override.
- Deciding whether a gate has passed.

## Assumptions

### A-1

The checks and the event of the gate form of `wio trailers` are reachable as
functions that both commands call, so no check is written twice.

## Mechanisms

- **`wio log review <work> <action> <stage> --result RESULT [--judge JUDGE]
  [--cite KEY=RESULT]...`** — the subcommand of `wio log` that `zj4ja0` created.
  It declares `--json`.
- **The checks and the event** — those of `check_cites`, `review_event` and the
  finder of the reviewed commit of the gate form of `wio trailers`, shared and
  not copied, so a refusal, its message and its exit code are the same.
- **The output** — nothing on standard output when it succeeds, and with
  `--json` one object `{"event": <the review event>}` with the cited items in
  order. Exit 0 when the event was handed to the sink, 1 for a refusal and 2 for
  a usage mistake.
- **The sink** — the `EventSink` port, wired by `wio.cli` to the `LogSink` of
  `wt49bz`.

## Acceptance criteria

The examples use the Work `k3m9xq`, with the items `AC-1` and `AC-3`, the action
`deliver` and the gate `docs-review`, a history with a work commit under a pure
gate commit, and a recording `EventSink`.

### **AC-1** The event is the one `wio trailers` writes

A review recorded without records leaves exactly the event that
`wio trailers --result` leaves.

#### The same arguments, the two commands

- **Given** the two commands with the arguments `k3m9xq deliver docs-review
  --result fail --judge human --cite AC-1=fail --cite AC-3=pass`, on the same
  history.
- **When** `wio log review` runs and `wio trailers` runs, each with `--result`.
- **Then** the sink received two equal `ReviewEvent`s, and `wio log review`
  printed nothing on standard output.

### **AC-2** It prints nothing, or a JSON document

A person or a script reads the result of the command as nothing or as one JSON
document.

#### The output

- **Given** the arguments of AC-1 without `--judge`.
- **When** `wio log review` runs, and runs with `--json`.
- **Then** the first exits 0 and prints nothing, and the second prints one JSON
  object with the event, whose judge is `agent`.

### **AC-3** A refusal writes nothing

A review that `wio trailers` refuses is refused here too, and writes nothing.

#### What `wio trailers` refuses

- **Given** the gate and the Work above.
- **When** `wio log review` runs with `--result maybe`, with
  `--cite AC-99=pass`, with `--cite AC-1=pass --cite AC-1=fail`, and on a
  history of commits that each carry only a gate record.
- **Then** each exits 1, prints nothing on standard output, prints the `error:`
  line that `wio trailers` prints for it on standard error, and the sink
  received no event.

### **AC-4** A usage mistake exits 2

A usage mistake is told apart from a refused review by its exit code.

#### A missing argument and a list of Works

- **Given** the same history.
- **When** `wio log review k3m9xq deliver docs-review` runs without `--result`,
  and `wio log review k3m9xq,other1 deliver docs-review --result pass` runs.
- **Then** each exits 2, prints nothing on standard output, says what is wrong
  on standard error, and the sink received no event.

### **AC-5** A review reaches the log and is shown

A review recorded without records is shown by `wio log show` on a real
repository.

#### On a real repository

- **Given** a real clone with the Work and the gate, and a `$WIO_HOME` that
  names an empty directory.
- **When** `wio log review <work> <action> <gate> --result pass` runs, and then
  `wio log show <work>` runs.
- **Then** the first exits 0 and prints nothing, and the second lists the gate
  with the judge `agent`, the result `pass` and the first 12 characters of the
  commit that the gate reviewed.
