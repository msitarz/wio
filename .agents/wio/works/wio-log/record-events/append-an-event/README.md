<!-- wio
id = "wt49bz"
template = "feature.leaf"
roots = ["wio"]
depends_on = ["jk2yz0", "5pes9b", "xfy1mq", "hnakzm", "m7yp42"]
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
- The real `Environment`, `Clock` and `Directories`, which `hnakzm` gives.
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

- **`LogSink(environment, clock, directories, repository, filesystem, stdio,
  log)`** — in `wio.log`, an `EventSink` over the ports `Environment`, `Clock`,
  `Directories`, `Repository`, `FileSystem` and `Stdio`, and a `Log`.
- **The order of the steps** — `write` reads `$WIO_LOG`, then calls
  `locate_log(Repository, Directories)`, then
  `identify(log, environment, stdio)` with the sink's own `Log`, `Environment`
  and `Stdio`, then builds the `Envelope`, encodes the line and appends it.
- **The stamp** — an `Envelope` whose time is `Clock.now()`, whose directory is
  `Environment.working_directory()` as text, and whose other fields are those of
  the `SessionIdentity` that `identify` gives, whose warnings pass through
  unchanged on every write.
- **The append** — one call of `append_text` with the line of `encode_line`, to
  `EVENTS_FILE` in the directory that `locate_log` gives.
- **The variables read** — `WIO_LOG` and `WIO_HOME` through `Environment.get`,
  an empty `WIO_HOME` counting as unset, besides those that `identify` reads.
- **`$WIO_LOG`** — what C-2 of `t8embw` says, with `off` also asking nothing of
  the repository, the directories or the clock, and a value that is not
  recognized writing the warning `warning: WIO_LOG must be "off" to switch the
  log off; the log stays on`, which never repeats the value.
- **A failure** — any `Exception` that `write` meets, whatever its class and
  whatever the step, is a warning, nothing is appended and nothing is raised; a
  failure of writing a warning, and of reading `WIO_HOME` for the hint, is
  swallowed too, and the hint is then left out.
- **The message of an error** — its `strerror` when it is an `OSError` that has
  a non-empty one, its text otherwise, and the name of its class when the text
  is empty, with each newline in it replaced by a space.
- **The warning of a failed location** — `warning: the event log could not be
  located: <message>` on standard error, as exactly one line, for a failure of
  the read of `$WIO_LOG` or of the location, such as a working directory that is
  not in a repository, a relative `$WIO_HOME` or a home directory that cannot be
  found.
- **The warning of a failed write** — `warning: the event log could not be
  written: <path>: <message>` on standard error, where `<path>` is the events
  file, for a failure of any step after the location.
- **The hint** — a `PermissionError`, or an `OSError` whose `errno` is `EROFS`,
  raised by the append, with `$WIO_HOME` unset or empty, adds to the warning of
  a failed write a second line on standard error that starts with
  `hint: add an exception to your harness's configuration`, holds
  `~/.agents/wio` and `$WIO_HOME`, and ends with
  `directory your harness allows`.
- **Wiring, provisional** — `wio.cli` builds the sink in `_trailers()` of
  `table.py` in place of `NoEvents`, which stays for tests that need a sink that
  drops, after `trailers_command` has found the repository, so that a working
  directory outside a repository fails as it does today, with the real
  `Environment`, `Clock` and `Directories` of `hnakzm` and a `SystemStdio()`,
  which binds the streams that `dispatch` has redirected to the `Stdio` of the
  command, and `ConfigSettings(repository, filesystem).load().log` as the `Log`.

## Acceptance criteria

The examples use fakes of the ports: a clock at `1795000000.0`, the working
directory `/w/app/sub`, the identity `/w/app/.git`, the Wio home `/h`, the
variables `CLAUDE_CODE_SESSION_ID=c1` and `AI_AGENT=x`, and a `FileSystem` that
records each append. The directory of the log is then `/h/log/app-6f8609bd196b`.

### **AC-1** An event is stamped and appended as one line

An event written to the sink reaches the log of its repository as one stamped
line.

#### A review event

- **Given** the fakes above.
- **When** `write` receives a `ReviewEvent`.
- **Then** one append was made, to `/h/log/app-6f8609bd196b/events.jsonl`, of
  one line that decodes to the event and to an envelope with the time
  `2026-11-18T11:06:40.000Z`, the directory `/w/app/sub`, the harness
  `claude-code`, the session `c1`, no parent, `matches` of `("claude-code",)`
  and `ids` holding both variables.

#### A Codex subagent

- **Given** `CODEX_SESSION_ID=s1` and `CODEX_THREAD_ID=t2`, and no other mapped
  variable.
- **When** `write` receives an event.
- **Then** the envelope of the line has the harness `codex`, the session `t2`
  and the parent `s1`.

#### Two events

- **Given** the fakes above.
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
do and that the sink never raises, so no command stops for it.

#### An unwritable home

- **Given** a `FileSystem` whose append raises `PermissionError(13, "Permission
  denied")`, and `$WIO_HOME` unset.
- **When** `write` receives an event.
- **Then** it returns, nothing is raised, and standard error holds `warning: the
  event log could not be written:
  /h/log/app-6f8609bd196b/events.jsonl: Permission denied` and, on the next
  line, the hint of the mechanism.

#### A home that `$WIO_HOME` names

- **Given** the same failure with `$WIO_HOME=/h`.
- **When** `write` receives an event.
- **Then** standard error holds the warning above and no hint.

#### An empty `$WIO_HOME` and a read-only file system

- **Given** `$WIO_HOME` set to an empty string and an append that raises
  `PermissionError(13, "Permission denied")`, and then one that raises
  `OSError(30, "Read-only file system")`.
- **When** `write` receives an event for each.
- **Then** each warning is followed by the hint.

#### A failure that the hint does not fit

- **Given** an append that raises `OSError(28, "No space left on device")`, with
  `$WIO_HOME` unset.
- **When** `write` receives an event.
- **Then** the warning names the events file and `No space left on device` and
  has no hint.

#### An error without an errno

- **Given** an append that raises `OSError("boom")`.
- **When** `write` receives an event.
- **Then** the warning ends in `events.jsonl: boom`.

#### A step after the location that fails

- **Given** an `Environment` whose `working_directory()` raises
  `FileNotFoundError(2, "No such file or directory")`, then one whose
  `get("CLAUDE_CODE_SESSION_ID")` raises `RuntimeError("boom")`, then a `Clock`
  whose `now()` raises `KeyError("x")`, then one that raises
  `ZeroDivisionError()`.
- **When** `write` receives an event for each.
- **Then** nothing was appended, nothing is raised, and standard error holds
  exactly one warning for each, `warning: the event log could not be written:
  /h/log/app-6f8609bd196b/events.jsonl:` followed by `No such file or
  directory`, `boom`, `'x'` and `ZeroDivisionError`, and none has a hint.

#### An append that fails with another class

- **Given** a `FileSystem` whose append raises `RuntimeError("boom")`.
- **When** `write` receives an event.
- **Then** nothing is raised, and standard error holds exactly one warning,
  `warning: the event log could not be written:
  /h/log/app-6f8609bd196b/events.jsonl: boom`.

#### A permission failure that is not the append

- **Given** an `Environment` whose `get("CLAUDE_CODE_SESSION_ID")` raises
  `PermissionError(13, "Permission denied")`, and `$WIO_HOME` unset.
- **When** `write` receives an event.
- **Then** standard error holds the warning of a failed write and no hint.

#### A location that fails

- **Given** a `Repository` whose `identity` raises `RuntimeError("not in a
  repository")`, a `Directories` whose `wio_home` raises `ValueError("WIO_HOME
  must be absolute")`, and one whose `wio_home` raises `OSError(2, "home not
  found")`.
- **When** `write` receives an event for each.
- **Then** each returns and nothing was appended, and standard error holds
  exactly one line for each, `warning: the event log could not be located: not
  in a repository`, `... : WIO_HOME must be absolute` and `... : home not
  found`, and no hint.

#### A message that holds a newline

- **Given** a `Repository` whose `identity` raises `RuntimeError("a\nb")`.
- **When** `write` receives an event.
- **Then** standard error holds exactly one line,
  `warning: the event log could not be located: a b`.

#### A failure while warning

- **Given** a `Stdio` whose standard error raises `ValueError("closed")` when it
  is written, and an append that raises `PermissionError(13, "Permission
  denied")`.
- **When** `write` receives an event.
- **Then** it returns and nothing is raised.

#### A hint whose variable cannot be read

- **Given** an append that raises `PermissionError(13, "Permission denied")`,
  and an `Environment` whose `get("WIO_HOME")` raises `OSError("denied")`.
- **When** `write` receives an event.
- **Then** nothing is raised, and standard error holds the warning of a failed
  write and no hint.

#### A switch that cannot be read

- **Given** an `Environment` whose `get("WIO_LOG")` raises `OSError("denied")`.
- **When** `write` receives an event.
- **Then** it returns, nothing was appended, and standard error holds exactly
  one line, `warning: the event log could not be located: denied`.

### **AC-3** The log can be switched off

A user switches the log off with `$WIO_LOG=off`, and a value that is not
recognized never stops it.

#### Off

- **Given** `$WIO_LOG=off`, `CLAUDE_CODE_SESSION_ID=bad value!` and a
  `Repository` whose `identity` raises.
- **When** `write` receives an event.
- **Then** nothing was appended, no directory was created, nothing was warned,
  `Environment` was asked only for `WIO_LOG`, and `Repository`, `Directories`
  and the clock were not asked.

#### A value that is not recognized

- **Given** `$WIO_LOG=maybe`, then `OFF`, and then `$WIO_LOG` set to an empty
  string.
- **When** `write` receives an event for each.
- **Then** the first two append the line and write `warning: WIO_LOG must be
  "off" to switch the log off; the log stays on` and nothing of the value, and
  the third appends it and warns of nothing.

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

#### Outside a repository

- **Given** a working directory that is not in a repository and a `$WIO_HOME`
  that names an empty directory.
- **When** `wio trailers <work> <action> <gate> --result pass` runs.
- **Then** it fails exactly as it did before the sink existed, with the usage
  error of `wio trailers`, and `$WIO_HOME` is still empty.

#### A warning reaches the stream of the command

- **Given** a real clone and a `$WIO_HOME` that names a path under a regular
  file, and the `Stdio` of a test.
- **When** the main function of `wio.cli` runs `wio trailers <work> <action>
  <gate> --result pass` with that `Stdio`.
- **Then** it exits 0, the record is on the standard output of that `Stdio`, and
  its standard error holds `warning: the event log could not be written:`.
