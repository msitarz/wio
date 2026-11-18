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
- The values of the variables the config names are recorded as they are seen
  when they are well shaped, and the only other variable read is
  `WIO_PREFER_HARNESS`.
- A value that is not shaped like an id is dropped, with a warning, so a mapping
  that names the wrong variable does not copy it into the log, and a harness
  whose session variable is malformed is named with an unknown session.

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

### A-3

A real session id fits the shape below, so a value that does not is a mistake
and not an id.

## Mechanisms

- **`identify(log: Log, environment: Environment, stdio: Stdio) ->
  SessionIdentity`** — in `wio.log`, with `SessionIdentity(harness: str | None,
  session: str | None, parent: str | None, matches: tuple[str, ...], ids:
  Mapping[str, str])`, whose fields are those of the `Envelope` of `5pes9b`; it
  warns on standard error through `stdio`.
- **The variables read** — every name in the `session` and `parent` lists of
  every harness and in `record_env_vars`, and `WIO_PREFER_HARNESS` whose value
  never reaches `ids`, through `Environment.get`, and no other.
- **A variable that is set** — one whose value is not empty.
- **The shape of a value** — one to 128 characters of `A-Za-z0-9._:-`; a set
  value of another shape is dropped, with a warning that names the variable and
  never its value.
- **`ids`** — each variable that is set and well shaped, with its value, first
  for each harness in the order of the config its `session` and then its
  `parent` variables, then for `record_env_vars`, and a variable named more than
  once is recorded once, at its first place, whether or not a harness was
  resolved.
- **A match** — a harness matches when one of its `session` variables is set,
  well shaped or not, and `matches` lists the matching harnesses in the order of
  the config: the built-ins first, a replaced built-in in its built-in place,
  and the harnesses of the file after them in the order of the file.
- **The preference** — `$WIO_PREFER_HARNESS` when it is set and not empty, and
  otherwise `Log.prefer_harness`.
- **The variable's list** — comma-separated harness names whose items are
  trimmed, with empty items ignored, and `none` standing for an empty list only
  when it is the whole value; a name that is not a harness, and `none` inside a
  longer list, is ignored with a warning that names it, on every run.
- **The resolution** — with one match, that harness; with several, the first
  name of the preference that matches; with none, or with no preference that
  matches, no harness, session or parent.
- **The derived fields** — `session` is the value of the first `session`
  variable of the harness that is set, and `None`, with the warning, when that
  value is not well shaped; `parent` is the value of the first `parent`
  variable that is set and well shaped, and only when `session` is not `None`
  and the value differs from it.

## Acceptance criteria

The examples use the built-in harnesses and no `[log]` table, and an
`Environment` fake holds the variables given.

### **AC-1** One harness gives the session

A run that shows the variables of one harness is identified with its session
and, for Codex, its parent.

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

A run that shows the variables of several harnesses is left unresolved instead
of guessed.

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

A preference from the config or from `$WIO_PREFER_HARNESS` resolves a nested
run.

#### The config and the variable

- **Given** the three variables of AC-2, and `prefer_harness = ["codex"]`.
- **When** `identify` runs, and runs again with `$WIO_PREFER_HARNESS` set to
  `claude-code`, to `none`, and to `cursor,codex`.
- **Then** the first gives `codex` with the session `t2` and the parent `s1`,
  the second `claude-code` with the session `c1`, the third none, and the fourth
  `codex` and a warning that names `cursor`.

#### The list of the variable

- **Given** the three variables of AC-2.
- **When** `identify` runs with `$WIO_PREFER_HARNESS` set to ` claude-code , `,
  to `claude-code,,codex`, and to `none,codex`.
- **Then** the first gives `claude-code`, the second `claude-code`, and the
  third `codex` and a warning that names `none`.

#### An empty variable

- **Given** `$WIO_PREFER_HARNESS` set to an empty string and `prefer_harness =
  ["codex"]`, and the three variables of AC-2.
- **When** `identify` runs.
- **Then** the config's preference applies, and the harness is `codex`.

#### A preference that does not decide

- **Given** `[log.harnesses.cursor]` with `session = ["CURSOR_TRACE_ID"]` that
  is not set.
- **When** `identify` runs with the three variables of AC-2 and `prefer_harness
  = ["cursor"]`, and with `CLAUDE_CODE_SESSION_ID=c1` only and `prefer_harness =
  ["codex"]`, and with `CLAUDE_CODE_SESSION_ID=c1` only and
  `$WIO_PREFER_HARNESS=none`.
- **Then** the first gives no harness, session or parent, because `cursor` does
  not match, and the second and third give `claude-code` with the session `c1`.

#### A name that is not a harness

- **Given** `CLAUDE_CODE_SESSION_ID=c1` only, so that one harness matches.
- **When** `identify` runs with `$WIO_PREFER_HARNESS=cursor`.
- **Then** the harness is `claude-code` and a warning names `cursor`.

### **AC-4** A value that is not an id is dropped

A value that is not shaped like an id never reaches the log, and the warning
never repeats it.

#### A value of the wrong shape

- **Given** `CLAUDE_CODE_SESSION_ID` set to `a b`, then to a value of 200
  characters, then to `x/y`.
- **When** `identify` runs for each.
- **Then** each gives the harness `claude-code` and the session `None`,
  `matches` is `("claude-code",)`, `ids` lacks the variable, and a warning names
  `CLAUDE_CODE_SESSION_ID` and holds none of the value.

#### A subagent whose thread id is malformed

- **Given** `CODEX_THREAD_ID=a b` and `CODEX_SESSION_ID=s1`.
- **When** `identify` runs.
- **Then** the harness is `codex`, the session and the parent are `None`, `ids`
  is `{"CODEX_SESSION_ID": "s1"}`, and a warning names `CODEX_THREAD_ID`, so the
  subagent is not taken for its main session.

#### The boundaries of the shape

- **Given** `CLAUDE_CODE_SESSION_ID` set to 128 characters of `a`, then to 129,
  then to an empty string.
- **When** `identify` runs for each.
- **Then** the first gives that value as the session, the second the session
  `None` and a warning, and the third no harness, an empty `matches` and no
  warning.

### **AC-5** Only the named variables are read

Only the variables the config names are read, so nothing else in the environment
can reach an event.

#### A secret in the environment

- **Given** `SECRET_TOKEN=hunter2`, `WIO_PREFER_HARNESS=claude-code` and
  `CLAUDE_CODE_SESSION_ID=c1`, with a fake that records each name asked for.
- **When** `identify` runs.
- **Then** `SECRET_TOKEN` is neither read nor in `ids`, `ids` lacks
  `WIO_PREFER_HARNESS`, and every name asked for is one of the config's or
  `WIO_PREFER_HARNESS`.

#### A configured harness

- **Given** `[log.harnesses.cursor]` with `session = ["CURSOR_TRACE_ID"]` and
  `CURSOR_TRACE_ID=r9`.
- **When** `identify` runs.
- **Then** the harness is `cursor` and the session `r9`.

#### The order of the lists

- **Given** `[log.harnesses.cursor]` with `session = ["CURSOR_TRACE_ID",
  "AI_AGENT"]`, `AI_AGENT=x`, `CURSOR_TRACE_ID=r9` and
  `CLAUDE_CODE_SESSION_ID=c1`, and the default `record_env_vars`.
- **When** `identify` runs.
- **Then** the keys of `ids` are `CLAUDE_CODE_SESSION_ID`, `CURSOR_TRACE_ID` and
  `AI_AGENT`, and `AI_AGENT` appears once.
