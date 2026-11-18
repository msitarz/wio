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
- A log that holds a damaged line, a log that is not there or a Work that is
  gone is shown without failing.
- The same facts are available as one JSON document.

## Non-Goals

- Saying whether a stage is done or a gate passed, which `wio next` reads from
  the history later.
- Writing or changing a line of the log.
- Joining the events to a transcript, or totalling tokens and cost.
- Filtering by time, harness or session.
- Showing a log file that cannot be read, or that vanishes after it was listed,
  which fails with the error of the file system as any command does.

## Assumptions

### A-1

A person reads the times as UTC, so the text form needs no time zone option.

### A-2

`show` keys on the Work ids that the events hold and never reads the Works tree,
so a Work that was deleted after its events were written is still shown.

## Mechanisms

- **`wio log`** — the command of the `log` component, with its entry in the
  `wio.cli` table, whose subcommands are `show` here and `review` from `9m32d0`.
- **The help** — bare or with `-h`, `wio log` prints its help to standard output
  and exits 0.
- **The usage mistakes** — `wio log --json`, an unknown subcommand and an extra
  argument exit 2 with the message on standard error and nothing on standard
  output, because `--json` belongs to `show` and to `review`.
- **`wio log show [WORK] [--json]`** — reads the bytes of each file that
  `log_files` finds in the directory that `locate_log` gives, decodes them as
  UTF-8 with the replacement character for what is not, and runs `decode_lines`
  on each file on its own.
- **The Work that is asked for** — with a Work id only the rows of that Work are
  shown.
- **The order of events** — by the time of the envelope, then by file name, then
  by line.
- **A row** — one for each Work, action and stage that the events name, with the
  time and the session of its latest `context` event and its reviews.
- **The reviews of a row** — the latest `review` event for each judge and each
  reviewed commit, in the order of the position of each one in the order of
  events.
- **The placement** — a row is placed by the position of its latest event of
  either kind in the order of events, and the Works are ordered by id.
- **The time** — an RFC 3339 string in UTC to the millisecond, written as
  `encode_line` writes it, rounded to the microsecond and then truncated.
- **The session** — `<harness>:<session>`, with `(parent <parent>)` after it
  only when the event has a session and a parent, `<harness>:unknown` for a
  harness with no session, `ambiguous (<harness>, <harness>)` for no harness and
  two or more matches, joined by a comma and a space in the order of `matches`,
  and `unknown session` otherwise.
- **The text form** — a line `<work>` for a Work and, under it and indented by
  two spaces, a line `<action> <stage>  entered <time>  <session>` for each row
  with a `context` event, and a line `<action> <stage>  <judge> <result>
  <commit>  <time>` for each of its reviews, with the first 12 characters of the
  commit and, after two more spaces, each cited item as `<key>=<result>`
  separated by spaces.
- **The JSON form** — one document `{"works": {<id>: [<row>]}, "skipped": <n>}`,
  each row holding in this order `action`, `stage`, `entered` (its time, or
  `null`), `session` (an object of `harness`, `session`, `parent` and `matches`)
  and `reviews`, each a list of `judge`, `result`, `commit` in full, `time` and
  `cited`, a mapping in the order cited; `entered` and `session` are `null`
  exactly when the row has no `context` event, and the criteria compare the
  parsed document with the order of its keys and not its white space.
- **The skipped lines** — `n` is the sum over the files of the lines that
  `decode_lines` skipped, whichever Work is shown, and it is `skipped` in the
  JSON form and, when above 0, `note: skipped <n> line of the event log` or
  `lines` on standard error in the text form, and never changes the exit code.
- **No events** — nothing is printed in the text form, and the JSON form is
  `{"works": {}, "skipped": <n>}`, for a log directory that does not exist, for
  one without events and for a Work that has none, and the exit code is 0.
- **No repository** — the `RuntimeError` of the `Repository` port is a usage
  mistake that exits 2 with its message on standard error, as for
  `wio trailers`.
- **What is required** — the text form, the JSON form and the exit codes are
  required, and the wording of the help and of the note is provisional.

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

- **Given** `events.jsonl` with `context` events, in this order, of
  `architecture` at `10:09:00` with the session `c2`, of `wiring` at `10:07:00`,
  of `architecture` at `10:00:00` and of `architecture` at `10:05:00`.
- **When** `wio log show k3m9xq` runs.
- **Then** it prints exactly these lines, `architecture` once and with the
  session of its latest event:

  ```text
  k3m9xq
    deliver wiring  entered 2026-11-18T10:07:00.000Z  claude-code:c1
    deliver architecture  entered 2026-11-18T10:09:00.000Z  claude-code:c2
  ```

#### A time with milliseconds

- **Given** a `context` event of `wiring` whose time is
  `2026-11-18T10:00:00.123Z`.
- **When** `wio log show` runs.
- **Then** the line holds `entered 2026-11-18T10:00:00.123Z`.

#### The session of the event

- **Given** `context` events at `10:00`, `10:01`, `10:02` and `10:03` of
  `architecture`, `wiring`, `implementation` and `integration`: with the harness
  `codex`, the session `t2` and the parent `s1`; with no harness and `matches`
  holding `claude-code` and `codex`; with no harness and no matches; and with
  the harness `codex` and no session.
- **When** `wio log show` runs.
- **Then** the rows, in that order, say `codex:t2 (parent s1)`,
  `ambiguous (claude-code, codex)`, `unknown session` and `codex:unknown`.

### **AC-3** The latest review of each judge is shown

A person sees the latest review of each gate for each judge and each commit it
judged, with the result and the items it cited.

#### Judges and commits

- **Given** `review` events of the gate `docs-review`: by the judge `human` of
  the commit of 40 `a` with `pass` at `10:05` and the cited `AC-1=pass` and
  `AC-3=fail`, and by the judge `agent` of the commit of 40 `a` with `fail` at
  `10:00` and `pass` at `10:10`, and of the commit of 40 `b` with `pass` at
  `10:11`.
- **When** `wio log show k3m9xq` runs.
- **Then** it prints exactly these lines, with no `fail` and the reviews in the
  order of their latest events:

  ```text
  k3m9xq
    deliver docs-review  human pass aaaaaaaaaaaa  2026-11-18T10:05:00.000Z  AC-1=pass AC-3=fail
    deliver docs-review  agent pass aaaaaaaaaaaa  2026-11-18T10:10:00.000Z
    deliver docs-review  agent pass bbbbbbbbbbbb  2026-11-18T10:11:00.000Z
  ```

#### The JSON form of a gate row

- **Given** the same events.
- **When** `wio log show k3m9xq --json` runs.
- **Then** the first review of the row is, with its keys in this order,

  ```json
  {"judge": "human", "result": "pass",
   "commit": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
   "time": "2026-11-18T10:05:00.000Z",
   "cited": {"AC-1": "pass", "AC-3": "fail"}}
  ```

  and the row has `"entered": null` and `"session": null`.

#### The JSON form of a stage row

- **Given** a `context` event of `architecture` with the harness `codex`, the
  session `t2`, no parent and `matches` holding `codex`.
- **When** `wio log show --json` runs.
- **Then** its row is

  ```json
  {"action": "deliver", "stage": "architecture",
   "entered": "2026-11-18T10:00:00.000Z",
   "session": {"harness": "codex", "session": "t2", "parent": null,
               "matches": ["codex"]},
   "reviews": []}
  ```

#### A gate with a `context` event and reviews

- **Given** `context` events of `wiring` at `10:05` and of `docs-review` at
  `10:00`, and a `review` of `docs-review` by the judge `agent` of the commit of
  40 `a` with `pass` at `10:10`.
- **When** `wio log show k3m9xq` runs, and runs with `--json`.
- **Then** the text is exactly these lines, the `docs-review` row coming after
  the `wiring` row because its latest event is its review, with its `entered`
  line before its review line:

  ```text
  k3m9xq
    deliver wiring  entered 2026-11-18T10:05:00.000Z  claude-code:c1
    deliver docs-review  entered 2026-11-18T10:00:00.000Z  claude-code:c1
    deliver docs-review  agent pass aaaaaaaaaaaa  2026-11-18T10:10:00.000Z
  ```

  and the JSON row of `docs-review` has the time of its `context` event as
  `entered`, its `session` and one review.

#### A gate that no `context` event entered

- **Given** only `review` events of `docs-review` at `10:00`, and a `context`
  event of `wiring` at `10:05`.
- **When** `wio log show --json` runs.
- **Then** the `docs-review` row has `entered` and `session` as `null` and its
  reviews, and it is placed before the `wiring` row, because its latest event is
  earlier.

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

- **Given** a clone with no log directory, a clone whose log directory holds no
  file, and a directory outside a repository.
- **When** `wio log show` and `wio log show --json` run in each.
- **Then** the first two print nothing in the text form, print
  `{"works": {}, "skipped": 0}` in the JSON form and exit 0, and the third exits
  2 with the message of the `Repository` port on standard error.

### **AC-5** Damaged lines are skipped and noted

A damaged log still shows the events around its damaged lines, and says how many
it skipped.

#### A log with damaged lines

- **Given** two complete events, a torn line, a line of a higher version and a
  line that is only the byte `0xff`.
- **When** `wio log show` runs, and runs with `--json`.
- **Then** both exit 0 and show both events, the first with `note: skipped 3
  lines of the event log` on standard error and the second with `"skipped": 3`.

#### A byte that is not UTF-8 inside a line that is complete

- **Given** a complete `context` event whose session holds the byte `0xff`
  after `c`.
- **When** `wio log show` runs, and runs with `--json`.
- **Then** the event is shown, the row saying `claude-code:c` followed by the
  replacement character `U+FFFD`, and in the JSON form `session` is `c` followed
  by `U+FFFD` and `"skipped": 0`.

#### A torn last line before the next file

- **Given** `a.jsonl` that ends in a torn line with no newline, and
  `events.jsonl` that starts with a complete event.
- **When** `wio log show --json` runs.
- **Then** the complete event is shown, and `"skipped": 1`.

#### One line, none, and another Work

- **Given** a log with one damaged line and events of two Works, and then one
  with no damaged line.
- **When** `wio log show k3m9xq --json` runs on the first, and `wio log show`
  runs on each.
- **Then** the JSON has `"skipped": 1` although another Work was asked for, the
  first text form has `note: skipped 1 line of the event log`, and the second
  has no note.

#### No events and a damaged line

- **Given** a log with one damaged line and no Work `other1`.
- **When** `wio log show other1 --json` runs.
- **Then** it prints `{"works": {}, "skipped": 1}`.

### **AC-6** Every file of the directory is read, in one order

Events spread over several files of a log are shown as one history, in the order
of their times and then of their files.

#### Two files

- **Given** `events.jsonl` with `context` events of `wiring` at `10:00` and of
  `integration` at `10:05`, and `a.jsonl` with one of `architecture` at `10:05`.
- **When** `wio log show --json` runs.
- **Then** the rows are `wiring`, `architecture` and `integration`, because the
  two events at `10:05` are ordered by file name.

#### Several Works

- **Given** `context` events of the Works `zz9999` at `10:00` and `k3m9xq` at
  `10:05`.
- **When** `wio log show` runs.
- **Then** `k3m9xq` is listed before `zz9999`.
