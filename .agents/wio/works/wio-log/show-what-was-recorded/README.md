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
- For a gate it shows the latest review of each judge for each commit it judged,
  with its result and the items it cited.
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

### A-2

`show` keys on the Work ids that the events hold and never reads the Works tree,
so a Work that was deleted after its events were written is still shown.

## Mechanisms

- **`wio log`** — the command of `wio.cli` with the subcommands `show` here and
  `review` from `9m32d0`. Bare or with `-h` it prints its help to standard
  output and exits 0. `--json` belongs to `show` and to `review`, and
  `wio log --json`, an unknown subcommand and an extra argument are usage
  mistakes that exit 2, with the message on standard error and nothing on
  standard output.
- **`wio log show [WORK] [--json]`** — reads the bytes of every file that
  `log_files` finds in the directory that `locate_log` gives, in order, decodes
  them as UTF-8 with the replacement character for what is not, then with
  `decode_lines`. With a Work id it shows that Work only.
- **The order of events** — by the time of the envelope, and for equal times by
  file name and then line.
- **A row** — one for each Work, action and stage that the events name. It holds
  the time and the session of the latest `context` event, and the latest
  `review` event for each judge and each reviewed commit, with its result, time
  and cited items. A row is placed by the position of its latest event of
  either kind in the order of events, and the Works are ordered by id.
- **The time** — an RFC 3339 string in UTC to the millisecond, as in the line.
- **The session** — `<harness>:<session>`, with `(parent <parent>)` after it
  when the event has a parent; `<harness>:unknown` for a harness with no
  session; `ambiguous (<harness>, <harness>)` for no harness and two or more
  matches, in the order of `matches`; and `unknown session` otherwise.
- **The text form** — one line `<work>` for a Work, and under it, each line
  indented by two spaces, for a row with a `context` event
  `<action> <stage>  entered <time>  <session>`, and for each of its reviews
  `<action> <stage>  <judge> <result> <commit>  <time>`, with the first 12
  characters of the commit and each cited item as `<key>=<result>` after the
  time, separated by spaces.
- **The JSON form** — one document `{"works": {<id>: [<row>]}, "skipped": <n>}`
  whose rows hold, in this order, `action`, `stage`, `entered` (the time, or
  `null` for a row with no `context` event), `session` (an object with
  `harness`, `session`, `parent` and `matches`, or `null` with it) and
  `reviews`, a list of objects with `judge`, `result`, `commit` in full, `time`
  and `cited`, a mapping of the items in the order cited. White space is not
  part of the form.
- **The skipped lines** — those of the whole log, whichever Work is shown:
  `note: skipped <n> line of the event log` for 1 and `lines` for more on
  standard error in the text form when `n` is above 0, and `skipped` in the JSON
  form; a note never changes the exit code.
- **No events** — nothing is printed in the text form, and the JSON form is
  `{"works": {}, "skipped": 0}`, for a log directory that does not exist, for
  one without events and for a Work that has none; the exit code is 0.
- **No repository** — the `RuntimeError` of the `Repository` port is a usage
  mistake that exits 2 with its message on standard error, as for
  `wio trailers`.

## Acceptance criteria

The examples use the Work `k3m9xq`, the action `deliver`, the date 2026-11-18,
and a log directory that a fake `FileSystem` holds with the lines given; every
`context` event has the harness `claude-code` and the session `c1` unless it
says otherwise.

### **AC-1** `wio log` is a command

A person reaches the commands of the log through `wio log` and finds `show` in
its help.

#### Bare

- **Given** any working directory.
- **When** `wio log` runs, and `wio log -h` runs.
- **Then** each prints help that names `show` and exits 0.

#### Usage mistakes

- **Given** any working directory.
- **When** `wio log nonsense`, `wio log --json` and `wio log show a b` run.
- **Then** each exits 2, prints nothing on standard output and says what is
  wrong on standard error.

### **AC-2** The last time each stage was entered is shown

A person sees when each stage of a Work was last entered, and by which session.

#### Several events of a stage

- **Given** `context` events of `architecture` at `10:00:00`, `10:05:00` and
  `10:09:00`, and one of `wiring` at `10:07:00`.
- **When** `wio log show k3m9xq` runs.
- **Then** it prints exactly these lines, `architecture` once:

  ```text
  k3m9xq
    deliver wiring  entered 2026-11-18T10:07:00.000Z  claude-code:c1
    deliver architecture  entered 2026-11-18T10:09:00.000Z  claude-code:c1
  ```

#### The session of the event

- **Given** `context` events of four stages: with the harness `codex`, the
  session `t2` and the parent `s1`; with no harness and `matches` holding
  `claude-code` and `codex`; with no harness and no matches; and with the
  harness `codex` and no session.
- **When** `wio log show` runs.
- **Then** the rows say `codex:t2 (parent s1)`, `ambiguous (claude-code,
  codex)`, `unknown session` and `codex:unknown`.

#### The JSON form

- **Given** the first event of the scenario above.
- **When** `wio log show --json` runs.
- **Then** the document holds one row whose `session` is an object with the
  harness `codex`, the session `t2`, the parent `s1` and `matches` of the event,
  and whose `entered` is its time and whose `reviews` is empty.

### **AC-3** The latest review of each judge is shown

A person sees the latest review of each gate for each judge and each commit it
judged, with the result and the items it cited.

#### Judges and commits

- **Given** `review` events of the gate `docs-review`: by the judge `agent` of
  the commit of 40 `a` with `fail` at `10:00` and `pass` at `10:10`, of the
  commit of 40 `b` with `pass` at `10:11`, and by the judge `human` of the
  commit of 40 `a` with `pass` at `10:12` and the cited `AC-1=pass`.
- **When** `wio log show k3m9xq` runs, and runs with `--json`.
- **Then** the text lists `agent pass aaaaaaaaaaaa`, `agent pass bbbbbbbbbbbb`
  and `human pass aaaaaaaaaaaa` with the time of each and `AC-1=pass` after the
  last, and no `fail`, and the JSON holds those three reviews with the commits
  in full and `cited` of the last as `{"AC-1": "pass"}`.

#### A gate that no `context` event entered

- **Given** only `review` events of `docs-review`, and a `context` event of
  `wiring` at an earlier time.
- **When** `wio log show --json` runs.
- **Then** the `docs-review` row has `entered` and `session` as `null` and its
  reviews, and it is placed after the `wiring` row.

### **AC-4** A Work or the log can be missing

A Work with no events, a Work that is gone, a clone with no log and a directory
with no repository each have a defined result.

#### A Work that has no events

- **Given** events of `k3m9xq` only.
- **When** `wio log show other1` runs, and runs with `--json`.
- **Then** the first prints nothing, and the second prints
  `{"works": {}, "skipped": 0}`, and both exit 0.

#### A Work that is gone

- **Given** events of `k3m9xq` in a clone whose Works directory holds no such
  Work.
- **When** `wio log show` runs.
- **Then** it lists the rows of `k3m9xq` and exits 0.

#### No log, and no repository

- **Given** a clone with no log directory, and a directory outside a repository.
- **When** `wio log show` runs in each.
- **Then** the first prints nothing and exits 0, and the second exits 2 with the
  message of the `Repository` port on standard error.

### **AC-5** Damaged lines are skipped and noted

A damaged log still shows the events around its damaged lines, and says how many
it skipped.

#### A log with damaged lines

- **Given** two complete events, a torn line, a line of a higher version and a
  line that holds the byte `0xff`.
- **When** `wio log show` runs, and runs with `--json`.
- **Then** both exit 0 and show both events, the first with `note: skipped 3
  lines of the event log` on standard error and the second with `"skipped": 3`.

#### One line, none, and another Work

- **Given** a log with one damaged line and events of two Works, and then one
  with no damaged line.
- **When** `wio log show k3m9xq --json` runs on the first, and `wio log show`
  runs on each.
- **Then** the JSON has `"skipped": 1` although another Work was asked for, the
  first text form has `note: skipped 1 line of the event log`, and the second
  has no note.

### **AC-6** Every file of the directory is read, in one order

Events spread over several files of a log are shown as one history, in a fixed
order.

#### Two files

- **Given** `events.jsonl` with a `context` event of `wiring` at `10:05`, and
  `a.jsonl` with one of `architecture` at `10:00` and one of `integration` at
  `10:05`.
- **When** `wio log show --json` runs.
- **Then** the rows are `architecture`, then `integration`, then `wiring`,
  because the two events at `10:05` are ordered by file name.

#### Several Works

- **Given** `context` events of the Works `zz9999` at `10:00` and `k3m9xq` at
  `10:05`.
- **When** `wio log show` runs.
- **Then** `k3m9xq` is listed before `zz9999`.
