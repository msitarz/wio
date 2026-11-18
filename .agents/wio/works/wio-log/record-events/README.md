<!-- wio
id = "7v8amt"
template = "feature.parent"
roots = ["@descendants"]
depends_on = ["jk2yz0", "5pes9b", "m7yp42", "hnakzm"]
-->

# Record events

## Purpose

An event that reaches the log without the session that wrote it cannot be joined
to a transcript, so the engine needs a sink that identifies the session from
the real environment and appends the stamped event to the real log.

## Goals

- An event written by a command on a real repository carries the harness
  session that the real environment shows.
- A harness that the config names, and a preference for a nested run, change
  what the stamp holds without a code change.
- A run that shows several harnesses is stamped without a guess, and says which
  harnesses it saw.

## Non-Goals

- What the children state: the identification, the append, the switch and the
  warnings.
- Reading the events back, which `zj4ja0` does.

## Assumptions

### A-1

The system-level tests run `wio` with a controlled environment, so they set
exactly the variables a scenario names and no others.

## Mechanisms

- **`identify`** — the identification of the session, built by `xfy1mq`.
- **`LogSink`** — the sink that stamps with it and appends, built by `wt49bz`.
- **The log location and the line format** — built by `jk2yz0` and `5pes9b`,
  and used by the sink.
- **The `[log]` settings** — read by the identification, built by `m7yp42`.

## Constraints

### C-1

Only `wio.cli` builds the sink and passes it on, and the identification reads
the environment through `Environment`. `uv run tach check` verifies it.

## Visuals

The Before diagram is drawn from `5fbdd18` on `main`, and the After diagram is
the design this Work delivers.

### Before

```mermaid
flowchart LR
    T["wio trailers --result"] --> N["NoEvents\n(drops the event)"]
```

### After

```mermaid
flowchart LR
    T["wio trailers --result"] --> S["LogSink\n(new)"]
    S --> I["identify the session\n(new)"]
    I --> E["Environment"]
    S --> L["log directory\n(new)"]
    S --> F["encode_line\n(new)"]
    L --> J["events.jsonl"]
    F --> J
```

## Acceptance criteria

### **AC-1** A real review carries the real session

An event written on a real repository carries the harness session that the real
environment shows.

#### Claude Code

- **Given** a real clone, a Work whose pipeline has a gate, an empty
  `$WIO_HOME`, and `CLAUDE_CODE_SESSION_ID=c1` and `AI_AGENT=claude-code_2` in
  the environment.
- **When** `wio trailers <work> <action> <gate> --result pass` runs.
- **Then** the one line of the log has the harness `claude-code`, the session
  `c1`, no parent and `ids` holding both variables.

#### Codex subagent

- **Given** the same clone, and `CODEX_SESSION_ID=s1` and `CODEX_THREAD_ID=t2`.
- **When** the same command runs.
- **Then** the line has the harness `codex`, the session `t2` and the parent
  `s1`.

### **AC-2** The config decides what a stamp holds

A new harness and a preference for a nested run change what a stamp holds
without a code change.

#### A harness of the config

- **Given** a config with `[log.harnesses.cursor]` and `session =
  ["CURSOR_TRACE_ID"]`, and `CURSOR_TRACE_ID=r9` in the environment.
- **When** the same command runs.
- **Then** the line has the harness `cursor` and the session `r9`.

#### A preference for a nested run

- **Given** `CLAUDE_CODE_SESSION_ID=c1` and `CODEX_THREAD_ID=t2`, and a config
  with `prefer_harness = ["codex"]`.
- **When** the command runs, and runs again with `$WIO_PREFER_HARNESS=none`.
- **Then** the first line has the harness `codex` and the session `t2`, and the
  second has no harness, session or parent and `matches` holds `claude-code` and
  `codex`.
