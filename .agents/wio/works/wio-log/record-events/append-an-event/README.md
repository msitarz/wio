<!-- wio
id = "wt49bz"
template = "feature.leaf"
roots = ["wio"]
depends_on = ["jk2yz0", "5pes9b", "xfy1mq"]
-->

# Append an event

## Purpose

Events must reach the log without ever costing a command, and in a form that
sessions running at the same time cannot corrupt; the engine needs one sink that
stamps an event and appends it, in place of the one that drops it.

## Goals

- An event written to the `EventSink` is stamped with its envelope and appended
  as one line of the log of its repository.
- A failure to locate or to write the log is a warning that raises nothing and
  never changes a command's result.
- A user can switch the log off, and a value of the switch that is not
  recognized never stops the log or a command.
- `wio trailers` writes its events to this sink, not to the one that drops them.

## Non-Goals

- Finding the location, encoding a line or identifying the session, which
  `jk2yz0`, `5pes9b` and `xfy1mq` do.
- Rotating the log or bounding its size.
- Writing a `context` event, which `wio context` builds and this sink writes
  like any other.

## Assumptions

### A-1

`$WIO_LOG` is recognized only as the exact, lowercase value `off`, so `OFF`, `0`
and `false` are values that are not recognized.

### A-2

The text of the working directory in the envelope is `str` of the path that
`Environment.working_directory()` gives.

## Mechanisms

- **`LogSink`** — in `wio.log`, an `EventSink` built from the ports
  `Environment`, `Clock`, `Directories`, `Repository`, `FileSystem` and `Stdio`,
  and a `Log`.
- **The order of the steps** — `write` reads `$WIO_LOG`, then calls
  `locate_log(Repository, Directories)`, then `identify`, then builds the
  `Envelope`, encodes the line and appends it.
- **The stamp** — an `Envelope` whose time is `Clock.now()`, whose directory is
  `Environment.working_directory()` as text, and whose other fields are those of
  the `SessionIdentity` that `identify` gives, whose warnings pass through
  unchanged on every write.
- **The append** — one call of `append_text` with the line of `encode_line`, to
  `EVENTS_FILE` in the directory that `locate_log` gives.
- **The variables read** — `WIO_LOG` and `WIO_HOME` through `Environment.get`,
  an empty `WIO_HOME` counting as unset, besides those that `identify` reads.
- **`$WIO_LOG`** — `off` switches the log off: nothing is read from the
  repository, the directories or the clock, nothing is written or created and
  nothing is warned. An unset or empty value leaves it on, and any other value
  leaves it on with a warning that names `WIO_LOG`.
- **A failure** — an `OSError`, a `ValueError` or a `RuntimeError` of the
  location, the encoding or the append is a warning, nothing is appended and
  nothing is raised.
- **The warning of a failed location** — `warning: the event log could not be
  located: <message>` on standard error, with the message of the error, as for
  a working directory that is not in a repository or a relative `$WIO_HOME`.
- **The warning of a failed write** —
  `warning: the event log could not be written: <path>: <reason>` on standard
  error, where `<path>` is the events file and `<reason>` is the `strerror` of
  the error, or its message when it has none.
- **The hint** — a `PermissionError` or a read-only file system, with
  `$WIO_HOME` unset or empty, adds to the warning of a failed write that a
  person should add an exception to the harness's configuration so that sessions
  can always write to `~/.agents/wio`, or set `$WIO_HOME` to a directory the
  harness allows.
- **Wiring, provisional** — `wio.cli` builds the sink in the `wire()` of `wio
  trailers` in place of `NoEvents`, which stays for tests that need a sink that
  drops, with a `SystemStdio()`, which binds the streams that `dispatch` has
  redirected to the `Stdio` of the command, and `ConfigSettings(...).load().log`
  as the `Log`.

## Acceptance criteria

The examples use fakes of the ports: a clock at `1795000000.0`, the working
directory `/w/app/sub`, the identity `/w/app/.git`, the home `/h` and the
variable `CLAUDE_CODE_SESSION_ID=c1`, and a `FileSystem` that records each
append. The directory of the log is then `/h/log/app-6f8609bd196b`.

### **AC-1** An event is stamped and appended as one line

An event written to the sink reaches the log of its repository as one stamped
line.

#### A review event

- **Given** the fakes above.
- **When** `write` receives a `ReviewEvent`.
- **Then** one append was made, to `/h/log/app-6f8609bd196b/events.jsonl`, of
  one line that decodes to the event and to an envelope with the time
  `2026-11-18T11:06:40.000Z`, the directory `/w/app/sub`, the harness
  `claude-code` and the session `c1`.

#### Two events

- **Given** the same fakes.
- **When** `write` receives two events.
- **Then** two appends were made, each of one line, and the sink did no write or
  read of the file other than those two appends.

#### The warnings of the identification

- **Given** `CLAUDE_CODE_SESSION_ID=bad value!`.
- **When** `write` receives two events.
- **Then** two lines were appended, whose envelopes have the harness
  `claude-code` and no session, and standard error holds exactly two warnings,
  one for each write, that name `CLAUDE_CODE_SESSION_ID` and hold none of its
  value.

### **AC-2** A failure is a warning

A failure to locate or write the log is a warning that tells the person what to
do, and never stops a command.

#### An unwritable home

- **Given** a `FileSystem` whose append raises `PermissionError(13, "Permission
  denied")`, and `$WIO_HOME` unset.
- **When** `write` receives an event.
- **Then** it returns, nothing is raised, and standard error holds `warning: the
  event log could not be written:
  /h/log/app-6f8609bd196b/events.jsonl: Permission denied` followed by the hint
  to let the harness write to `~/.agents/wio` or to set `$WIO_HOME`.

#### A home that `$WIO_HOME` names

- **Given** the same failure with `$WIO_HOME=/h`.
- **When** `write` receives an event.
- **Then** the warning is the one above and holds no hint.

#### An empty `$WIO_HOME` and a read-only file system

- **Given** `$WIO_HOME` set to an empty string and an append that raises
  `PermissionError`, and then one that raises `OSError(30, "Read-only file
  system")`.
- **When** `write` receives an event for each.
- **Then** each warning holds the hint.

#### A failure that the hint does not fit

- **Given** an append that raises `OSError(28, "No space left on device")`, with
  `$WIO_HOME` unset.
- **When** `write` receives an event.
- **Then** the warning names the events file and `No space left on device` and
  holds no hint.

#### A location that fails

- **Given** a `Repository` whose `identity` raises `RuntimeError("not in a
  repository")`, and then `$WIO_HOME` set to `relative/dir`.
- **When** `write` receives an event for each.
- **Then** each returns and nothing was appended, and standard error holds
  `warning: the event log could not be located:` and the message of the error,
  `not in a repository` for the first and the message of the `ValueError` of
  `Directories` for the second.

### **AC-3** The log can be switched off

A user switches the log off with `$WIO_LOG=off`, and a value that is not
recognized never stops it.

#### Off

- **Given** `$WIO_LOG=off`, and a `Repository` whose `identity` raises.
- **When** `write` receives an event.
- **Then** nothing was appended, no directory was created, nothing was warned,
  and `Repository`, `Directories` and the clock were not asked.

#### A value that is not recognized

- **Given** `$WIO_LOG=maybe`, then `OFF`, and then `$WIO_LOG` set to an empty
  string.
- **When** `write` receives an event for each.
- **Then** the first two append the line and warn, naming `WIO_LOG`, and the
  third appends it and warns of nothing.

### **AC-4** `wio trailers` writes to the real log

`wio trailers` writes its events to the real log, from any worktree of a clone.

#### A review on a real repository

- **Given** a real clone with a Work whose pipeline has a gate, a commit to
  review and a `$WIO_HOME` that names an empty directory.
- **When** `wio trailers <work> <action> <gate> --result pass` runs.
- **Then** it prints its record and exits 0, and one file `events.jsonl` under
  `$WIO_HOME/log/` holds one line that decodes to a `review` event of that
  Work, gate and commit.

#### A worktree

- **Given** the same clone, a worktree of it and a `$WIO_HOME` that names an
  empty directory.
- **When** the same command runs once in the main checkout and once in the
  worktree.
- **Then** `$WIO_HOME/log/` holds one directory, with one file `events.jsonl`
  of two lines.

#### A warning reaches the stream of the command

- **Given** a real clone and a `$WIO_HOME` that names a path under a regular
  file, and the `Stdio` of a test.
- **When** the main function of `wio.cli` runs `wio trailers <work> <action>
  <gate> --result pass` with that `Stdio`.
- **Then** it exits 0, the record is on the standard output of that `Stdio`, and
  its standard error holds `warning: the event log could not be written:`.
