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
- A failure to write is a warning that names the path, and never changes a
  command's result.
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

`FileSystem.append_text` makes one write of the text it is given, so the lines
of processes that write at once do not interleave, as its docstring says.

## Mechanisms

- **`LogSink`** — in `wio.log`, an `EventSink`. It is built from the ports
  `Environment`, `Clock`, `Directories`, `Repository`, `FileSystem` and `Stdio`,
  and the settings of `Config.log`, and `wio.cli` wires it.
- **The stamp** — an `Envelope` whose time is `Clock.now()`, whose directory is
  `Environment.working_directory()` as text, and whose other fields are those of
  the `SessionIdentity` that `identify` gives.
- **The append** — one call of `append_text` with the line of `encode_line`, to
  `EVENTS_FILE` in
  `log_directory(Repository.identity(), Directories.wio_home())`.
- **`$WIO_LOG`** — `off` switches the log off: nothing is read from the
  repository, nothing is written or created and nothing is warned. An unset or
  empty value leaves it on, and any other value leaves it on with a warning that
  names `WIO_LOG`.
- **The warning of a failure** — `warning: the event log could not be written:
  <path>: <reason>` on standard error, for an `OSError` of the append, and
  `warning: the event log needs a repository: <message>` for the
  `RuntimeError` of `Repository`. When `$WIO_HOME` is unset and the home is the
  default one, the first warning also says to add an exception to the harness's
  configuration so that sessions can always write to `~/.agents/wio`, or to set
  `$WIO_HOME` to a directory the harness allows.
- **Wiring** — `wio.cli` passes this sink to `wio trailers` in place of
  `NoEvents`, which stays for tests that need a sink that drops.

## Acceptance criteria

The examples use fakes of the ports: a clock at `1795000000.0`, the working
directory `/w/app/sub`, the identity `/w/app/.git`, the home `/h` and the
variable `CLAUDE_CODE_SESSION_ID=c1`, and a `FileSystem` that records each
append.

### **AC-1** An event is stamped and appended as one line

#### A review event

- **Given** the fakes above.
- **When** `write` receives a `ReviewEvent`.
- **Then** one append was made, to `events.jsonl` in `log_directory` of
  `/w/app/.git` under `/h`, of one line that decodes to the event and to an
  envelope with the time `2026-11-18T11:06:40.000Z`, the directory `/w/app/sub`,
  the harness `claude-code` and the session `c1`.

#### Two events

- **Given** the same fakes.
- **When** `write` receives two events.
- **Then** two appends were made, each of one line, and nothing else was done to
  the file.

### **AC-2** A failure is a warning

#### An unwritable home

- **Given** a `FileSystem` whose append raises `PermissionError` for `/h/log/…`,
  and `$WIO_HOME` unset.
- **When** `write` receives an event.
- **Then** it returns, standard error holds a warning that names the path and
  the reason and says to let the harness write to `~/.agents/wio`, and nothing
  is raised.

#### A home that `$WIO_HOME` names

- **Given** the same failure with `$WIO_HOME=/h`.
- **When** `write` receives an event.
- **Then** the warning names the path and the reason and says nothing about an
  exception to the harness.

#### Outside a repository

- **Given** a `Repository` whose `identity` raises `RuntimeError`.
- **When** `write` receives an event.
- **Then** it returns, nothing was appended, and a warning holds the message of
  the error.

### **AC-3** The log can be switched off

#### Off

- **Given** `$WIO_LOG=off`.
- **When** `write` receives an event.
- **Then** nothing was appended, no directory was created, nothing was warned,
  and `Repository`, `Directories` and the clock were not asked.

#### A value that is not recognized

- **Given** `$WIO_LOG=maybe`, and then `$WIO_LOG` set to an empty string.
- **When** `write` receives an event for each.
- **Then** the first appends the line and warns, naming `WIO_LOG`, and the
  second appends it and warns of nothing.

### **AC-4** `wio trailers` writes to the real log

#### A review on a real repository

- **Given** a real clone with a Work whose pipeline has a gate, a commit to
  review and an empty `$WIO_HOME`.
- **When** `wio trailers <work> <action> <gate> --result pass` runs.
- **Then** it prints its record and exits 0, and one file `events.jsonl` under
  `$WIO_HOME/log/` holds one line that decodes to a `review` event of that
  Work, gate and commit.

#### A worktree

- **Given** the same clone and a worktree of it.
- **When** the same command runs in the worktree.
- **Then** the line is appended to the same file.
