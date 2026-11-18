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
- A sink that fails never changes the result of the command.

## Non-Goals

- Printing a record, or adding a record to a commit.
- A list of Works, which `wio trailers` takes later and this command takes at
  the same time.
- The `--reviewed` override.
- Accepting a cited rule code, which `wio trailers` refuses as not selected
  until the rules component exists, and this command with it.
- Deciding whether a gate has passed.

## Assumptions

### A-1

The gate form of `wio trailers` does all its checks before it writes its event,
as its README says, so the checks can be separated from the write and from the
print of the record.

## Mechanisms

- **`wio log review <work> <action> <stage> --result RESULT [--judge JUDGE]
  [--cite KEY=RESULT]...`** — the subcommand of `wio log` that `zj4ja0` created,
  which declares `--json`.
- **The usage** — one Work, `--result` required and the judge `agent` by
  default, and a missing `--result`, a list of Works, an unknown option and a
  working directory outside a repository are usage mistakes.
- **The port `ReviewChecker`** — provisional, in `wio.log`: `check(work, action,
  stage, result, judge, cites) -> ReviewEvent`, which raises a refusal that
  carries the `error:` lines exactly as `wio trailers` prints them.
- **The factoring** — `wio.trailers` separates the checks from `run_review` into
  one function that runs the field checks, the cite checks and the finder of the
  reviewed commit in the order that its README states and builds the
  `ReviewEvent`, and `run_review` then writes the event and prints the record;
  this Work owns the change.
- **The wiring** — `wio.cli` builds the `ReviewChecker` from that function with
  the services that `wio trailers` is wired with and gives it, with the sink of
  `wt49bz`, to `wio log review`, and `wio.log` never imports `wio.trailers`.
- **The order of the refusals** — the field errors first, then the cites, then a
  history with no reviewed commit, and the first group that finds something
  stops the rest.
- **The output** — nothing on standard output when it succeeds, and with
  `--json` one document `{"event": {...}}` whose keys are, in this order,
  `work`, `action`, `stage`, `commit` in full, `judge`, `result`, `cited`, a
  mapping in the order cited, and `hashes`, a mapping that stays empty until the
  rules component exists, and the criteria compare the parsed document.
- **The exit codes** — 0 when the event was handed to the sink, 1 for a refusal
  with the `error:` lines on standard error and nothing on standard output, and
  2 for a usage mistake with its message on standard error and nothing on
  standard output.
- **The sink** — the `EventSink` port, wired by `wio.cli` to the `LogSink` of
  `wt49bz`, which warns and raises nothing when it fails.

## Acceptance criteria

The examples use the Work `k3m9xq`, with the items `AC-1` and `AC-3`, the action
`deliver` and the gate `docs-review`, a history with a work commit of 40 `a`
under a pure gate commit, and a recording `EventSink`.

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

- **Given** `k3m9xq deliver docs-review --result fail --cite AC-1=fail --cite
  AC-3=pass`, without `--judge`.
- **When** `wio log review` runs, and runs with `--json`.
- **Then** the first exits 0 and prints nothing, and the second prints one
  document that parses to
  `{"event": {"work": "k3m9xq", "action": "deliver", "stage": "docs-review",
  "commit": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa", "judge": "agent",
  "result": "fail", "cited": {"AC-1": "fail", "AC-3": "pass"}, "hashes": {}}}`
  with the keys in that order.

### **AC-3** A refusal writes nothing

A review that `wio trailers` refuses is refused here too, with the same lines,
and writes nothing.

#### What `wio trailers` refuses

- **Given** the gate and the Work above.
- **When** `wio log review` runs with `--result maybe`, with `--judge bogus`,
  with the stage `nonesuch`, with the Work `nope99`, with `--cite AC-99=pass`,
  with `--cite AC-1=pass --cite AC-1=fail`, with `--cite docs.DOC001=fail`, and
  on a history of commits that each carry only a gate record.
- **Then** each exits 1, prints nothing on standard output, prints on standard
  error the `error:` lines that `wio trailers` prints for the same arguments,
  which the criterion compares, among them
  `error: Wio-Work: no reviewed commit was found` for the last, and the sink
  received no event.

#### The first group of refusals stops the rest

- **Given** the same gate and Work.
- **When** `wio log review` runs with `--result maybe --cite AC-99=pass`.
- **Then** it exits 1 and prints only the error that names the result, and none
  that names `AC-99`.

### **AC-4** A usage mistake exits 2

A usage mistake is told apart from a refused review by its exit code.

#### Usage mistakes

- **Given** the same history, and a working directory outside a repository.
- **When** `wio log review k3m9xq deliver docs-review` runs without `--result`,
  `wio log review k3m9xq,other1 deliver docs-review --result pass` runs,
  `wio log review k3m9xq deliver docs-review --result pass --bogus` runs, and
  `wio log review k3m9xq deliver docs-review --result pass` runs outside a
  repository.
- **Then** each exits 2, prints nothing on standard output, says what is wrong
  on standard error, and the sink received no event.

#### A config with an error

- **Given** a config with an error.
- **When** `wio log review` and `wio trailers` run with the same arguments.
- **Then** both exit with the same code and print the same lines on standard
  error.

### **AC-5** The help of the command names the subcommand

A person finds `review` in the help of `wio log`, beside `show`.

#### The help

- **Given** any working directory.
- **When** `wio log -h` runs.
- **Then** the help names `review` and `show`.

### **AC-6** A review reaches the log and is shown

A review recorded without records is shown by `wio log show` on a real
repository.

#### On a real repository

- **Given** a real clone with the Work and the gate, and a `$WIO_HOME` that
  names an empty directory.
- **When** `wio log review <work> <action> <gate> --result pass` runs, and then
  `wio log show <work>` runs.
- **Then** the first exits 0 and prints nothing, and the second prints under the
  Work the line `<action> <gate>  agent pass <commit>  <time>`, with the first
  12 characters of the commit that the gate reviewed and the time of the
  event.

### **AC-7** A sink that fails never changes the result

The result of the command is the same when the log cannot be written or has been
switched off.

#### An unwritable home

- **Given** a real clone with the Work and the gate, and a `$WIO_HOME` that
  names a path under a regular file.
- **When** `wio log review <work> <action> <gate> --result pass` runs.
- **Then** it exits 0, prints nothing on standard output, and standard error
  holds `warning: the event log could not be written:`.

#### Switched off

- **Given** the same clone, `$WIO_LOG=off` and a `$WIO_HOME` that names an empty
  directory.
- **When** the same command runs.
- **Then** it exits 0, prints nothing on standard output or standard error, and
  the directory is still empty.
