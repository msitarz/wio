<!-- wio
id = "zj4ja0"
template = "feature.leaf"
roots = ["wio"]
depends_on = ["jk2yz0", "5pes9b"]
-->

# Show what was recorded

## Purpose

An event that cannot be read back is no help to the person who wants to know
when a session started a stage or what a gate's review said, and a log of JSON
lines is not something to search by hand; the engine needs a command that shows
what was recorded.

## Goals

- `wio log` is a command, and bare it prints its help.
- `wio log show` shows, for each Work and stage, when it was last entered and
  the session that entered it.
- For a gate it shows the latest review of each judge, with its result, the
  commit it judged and the items it cited.
- A log that holds a damaged line, a file that is not there or a Work that is
  gone is shown without failing.
- The same facts are available as one JSON document.

## Non-Goals

- Saying whether a stage is done or a gate passed, which `wio next` reads from
  the history later.
- Writing or changing a line of the log.
- Joining the events to a transcript, or totalling tokens and cost.
- Filtering by time, harness or session.

## Assumptions

### A-1

A person reads the times as UTC, so the text form needs no time zone option.

## Mechanisms

- **`wio log`** — the command of `wio.cli` with the subcommand `show` here and
  `review` from `9m32d0`. Bare, it prints its help to standard output and exits
  0. It declares `--json`.
- **`wio log show [WORK]`** — reads every file that `log_files` finds in the
  directory that `locate_log` gives, in order, decodes it with `decode_lines`,
  and orders the entries by their envelope's time, and for equal times by file
  name and line. With a Work id, it shows that Work only.
- **A row** — one for each Work, action and stage of the entries. It holds the
  time and the session of the latest `context` event, and, for each judge, the
  latest `review` event: its result, its commit, its time and its cited items
  with their results. Rows are ordered by the time of their latest event, oldest
  first, and then by action and stage.
- **The text form** — a line for each Work, `<work>`, and under it a line for
  each row, with the action and stage, the time `entered <time>` and the session
  as `<harness>:<session>`, and, for each judge, a line with the judge, the
  result, the first 12 characters of the commit and the time. A session that is
  unknown is `unknown session`, and one with several harnesses that matched is
  `ambiguous (<harness>, <harness>)`.
- **The JSON form** — one object `{"works": {<id>: [<row>]}, "skipped": <n>}`
  with each row holding `action`, `stage`, `entered` (the time or `null`),
  `session` (`harness`, `session`, `parent`, `matches`) and `reviews`, a list
  of `judge`, `result`, `commit` (in full), `time` and `cited`.
- **The skipped lines** — `note: skipped <n> lines of the event log` on standard
  error in the text form, and `skipped` in the JSON form; a note never changes
  the exit code.
- **No log** — a log directory that does not exist, or one without events, shows
  nothing and exits 0. A working directory outside a repository exits 2 with the
  message of the `Repository` port.

## Acceptance criteria

The examples use the Work `k3m9xq`, and a log directory that a fake `FileSystem`
holds with the lines given.

### **AC-1** `wio log` is a command

#### Bare

- **Given** any working directory.
- **When** `wio log` runs, and `wio log -h` runs.
- **Then** each prints help that names `show` and exits 0.

### **AC-2** The last time each stage was entered is shown

#### Several events of a stage

- **Given** `context` events of `k3m9xq`, `deliver` and `architecture` at
  `10:00:00`, `10:05:00` and `10:09:00`, and one of `wiring` at `10:07:00`.
- **When** `wio log show k3m9xq` runs.
- **Then** it lists `wiring`, entered at `10:07:00`, before `architecture`,
  entered at `10:09:00`, and shows `architecture` once.

#### The session of the event

- **Given** a `context` event with the harness `codex`, the session `t2` and the
  parent `s1`, one with none and `matches` holding `claude-code` and `codex`,
  and one with no harness and no matches.
- **When** `wio log show` runs.
- **Then** the rows say `codex:t2`, `ambiguous (claude-code, codex)` and
  `unknown session`.

### **AC-3** The latest review of each judge is shown

#### An agent and a human

- **Given** `review` events of the gate `docs-review` by the judge `agent` with
  the result `fail` at `10:00` and `pass` at `10:10`, and by the judge `human`
  with `pass` at `10:12`, the last with the cited `AC-1=pass`.
- **When** `wio log show k3m9xq` runs, and runs with `--json`.
- **Then** the text lists `agent pass` and `human pass`, each with the first 12
  characters of its commit, and no `fail`, and the JSON holds two reviews with
  the full commits and the cited items of the human's.

### **AC-4** A Work or the log can be missing

#### A Work that has no events, and one that is gone

- **Given** events of `k3m9xq` only.
- **When** `wio log show other1` runs.
- **Then** it prints nothing and exits 0.

#### No log, and no repository

- **Given** a clone with no log directory, and a directory outside a repository.
- **When** `wio log show` runs in each.
- **Then** the first prints nothing and exits 0, and the second exits 2 with
  the message of the `Repository` port on standard error.

### **AC-5** Damaged lines are skipped and noted

#### A log with a torn line

- **Given** two complete events, a torn line and a line of a higher version.
- **When** `wio log show` runs, and runs with `--json`.
- **Then** both exit 0 and show both events, the first with `note: skipped 2
  lines of the event log` on standard error and the second with `"skipped": 2`.

### **AC-6** Every file of the directory is read

#### Two files

- **Given** `events.jsonl` with an event at `10:05` and `a.jsonl` with one at
  `10:00` and one at `10:05` of other stages.
- **When** `wio log show --json` runs.
- **Then** the rows are ordered `10:00`, then the two of `10:05` with the one of
  `a.jsonl` first, because its file name comes first.
