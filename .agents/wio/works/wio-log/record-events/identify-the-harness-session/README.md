<!-- wio
id = "xfy1mq"
template = "feature.leaf"
roots = ["wio"]
depends_on = ["m7yp42"]
-->

# Identify the harness session

## Purpose

An event can be joined to the transcript of the session that wrote it only if
it names that session, and the harnesses expose it under different names, with
a nested run seeing the variables of both; the engine needs one place that
turns the environment into the session fields of an event.

## Goals

- The harness session of a run is identified from the environment, through the
  mappings of the config, with its parent session when it has one.
- A run that shows the variables of several harnesses is resolved by a
  preference, or left unresolved, and never guessed.
- The values of the variables the config names are recorded as they are seen,
  and no other variable is read.
- A value that is not shaped like an id is dropped, with a warning, so a mapping
  that names the wrong variable does not copy it into the log.

## Non-Goals

- Stamping an envelope or writing it, which `wt49bz` does.
- Finding the harness from the process tree, or checking that an id names a real
  transcript.
- Deriving a harness from `AI_AGENT`, which is recorded and never interpreted.

## Assumptions

### A-1

A harness whose variable is set is running the command, or started a harness
that is, and the environment alone cannot say which is the inner one.

### A-2

The config names only variables that hold ids, because a value that passes the
shape check can still be a secret, and `wio config check` cannot tell.

## Mechanisms

- **`identify(log: Log, environment: Environment) -> SessionIdentity`** — in
  `wio.log`, with `SessionIdentity(harness: str | None, session: str | None,
  parent: str | None, matches: tuple[str, ...], ids: Mapping[str, str])`, whose
  fields are those of the `Envelope` of `5pes9b`. It warns on standard error
  through the `Stdio` port.
- **The variables read** — every name in the `session` and `parent` lists of
  every harness and in `record_env_vars`, through `Environment.get`, and no
  other. An empty value counts as not set.
- **The shape of a value** — one to 128 characters of `A-Za-z0-9._:-`. A set
  value of another shape is dropped, as if the variable were not set, with a
  warning that names the variable and never its value.
- **`ids`** — each variable that is set and well shaped, with its value, in the
  order of the config, whether or not a harness was resolved.
- **A match** — a harness matches when one of its `session` variables is set and
  well shaped; `matches` lists the matching harnesses in the order of the
  config, built-ins first.
- **The preference** — `$WIO_PREFER_HARNESS` when it is set and not empty, and
  otherwise `Log.prefer_harness`. The variable is a comma-separated list of
  harness names, and `none` stands for an empty list. A name that is not a
  harness is ignored with a warning that names it.
- **The resolution** — with one match, that harness. With several, the first
  name of the preference that matches. With none or with no preference that
  matches, no harness, session or parent.
- **The derived fields** — `session` is the first well-shaped `session` variable
  of the harness that is set, and `parent` is the first of its `parent`
  variables that is set, and only when it differs from `session`.

## Acceptance criteria

The examples use the built-in harnesses and no `[log]` table, and an
`Environment` fake holds the variables given.

### **AC-1** One harness gives the session

#### Claude Code

- **Given** `CLAUDE_CODE_SESSION_ID=c1` and `AI_AGENT=claude-code_2`.
- **When** `identify` runs.
- **Then** the harness is `claude-code`, the session `c1`, the parent `None`,
  `matches` is `("claude-code",)` and `ids` holds both variables.

#### Codex, main session and subagent

- **Given** `CODEX_SESSION_ID=s1` and `CODEX_THREAD_ID=s1`, and then
  `CODEX_SESSION_ID=s1` and `CODEX_THREAD_ID=t2`.
- **When** `identify` runs for each.
- **Then** the first gives the session `s1` and no parent, and the second the
  session `t2` and the parent `s1`.

#### Codex with the session id alone

- **Given** `CODEX_SESSION_ID=s1` only.
- **When** `identify` runs.
- **Then** the harness is `codex`, the session `s1` and the parent `None`.

### **AC-2** Nothing is guessed when several harnesses match

#### A nested run

- **Given** `CLAUDE_CODE_SESSION_ID=c1`, `CODEX_THREAD_ID=t2` and
  `CODEX_SESSION_ID=s1`, and no preference.
- **When** `identify` runs.
- **Then** the harness, the session and the parent are `None`, `matches` is
  `("claude-code", "codex")` and `ids` holds the three variables.

#### No harness at all

- **Given** only `AI_AGENT=x`.
- **When** `identify` runs.
- **Then** the harness, the session and the parent are `None`, `matches` is
  empty and `ids` is `{"AI_AGENT": "x"}`.

### **AC-3** A preference resolves a nested run

#### The config and the variable

- **Given** the three variables of AC-2, and `prefer_harness = ["codex"]`.
- **When** `identify` runs, and runs again with `$WIO_PREFER_HARNESS` set to
  `claude-code`, to `none`, and to `cursor,codex`.
- **Then** the first gives `codex` with the session `t2` and the parent `s1`,
  the second `claude-code` with the session `c1`, the third none, and the fourth
  `codex` and a warning that names `cursor`.

#### An empty variable

- **Given** `$WIO_PREFER_HARNESS` set to an empty string and `prefer_harness =
  ["codex"]`.
- **When** `identify` runs.
- **Then** the config's preference applies.

### **AC-4** A value that is not an id is dropped

#### A value of the wrong shape

- **Given** `CODEX_THREAD_ID=a b`, then a value of 200 characters, then `x/y`.
- **When** `identify` runs for each.
- **Then** each gives no harness and no `CODEX_THREAD_ID` in `ids`, and a
  warning that names `CODEX_THREAD_ID` and holds none of the value.

### **AC-5** Only the named variables are read

#### A secret in the environment

- **Given** `SECRET_TOKEN=hunter2` and `CLAUDE_CODE_SESSION_ID=c1`, with a fake
  that records each name asked for.
- **When** `identify` runs.
- **Then** `SECRET_TOKEN` is neither read nor in `ids`, and every name asked for
  is one of the config's.

#### A configured harness

- **Given** `[log.harnesses.cursor]` with `session = ["CURSOR_TRACE_ID"]` and
  `CURSOR_TRACE_ID=r9`.
- **When** `identify` runs.
- **Then** the harness is `cursor` and the session `r9`.
