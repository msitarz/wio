<!-- wio
id = "m7yp42"
template = "feature.leaf"
roots = ["wio"]
depends_on = []
-->

# Declare the log settings in the config

## Purpose

The environment variables that name a harness session differ between harnesses
and grow with every new one, so a code change would be needed for each; the
config needs to declare them, with the two harnesses wio knows built in.

## Goals

- The config declares a harness and the variables that give its session, so a
  new harness needs no code change.
- Claude Code and Codex are known without any configuration.
- The config says which harness to prefer when a run shows the variables of
  several, and which further variables to record as they are.
- `wio config check` reports a mistake in the log settings, and
  `wio config list` and `wio config show` show them with their source.

## Non-Goals

- Reading the environment or choosing a harness, which `xfy1mq` does.
- `$WIO_PREFER_HARNESS` and `$WIO_LOG`, which the identify and append leaves
  read.
- Checking a value of a variable, which `xfy1mq` does when it reads one.

## Assumptions

### A-1

The listing of the config shows a built-in harness with the source `default`
and a configured one with the source `file`, as it does for every other table
entry, and no new kind of source is needed.

### A-2

`wio config show` and `wio config list` reach a key inside the table of a
harness, as `log.harnesses.<name>.session`, as they reach a key of
`actions.<name>`, and a `parent` that is not set shows as `[]`.

### A-3

`AI_AGENT` is a variable that some harnesses set, with a value that is shaped
like an id, so it is a useful default of `record_env_vars`; where no harness
sets it, nothing is recorded for it.

## Mechanisms

- **`[log]` in `config.toml`** — `prefer_harness`, an ordered list of harness
  names, empty by default, and `record_env_vars`, a list of variable names,
  `["AI_AGENT"]` by default.
- **`[log.harnesses.<name>]`** — one harness with `session`, a required list of
  variable names of which the first one set gives the session, and `parent`, an
  optional list of names of which the first one set gives the parent session.
- **The replacement rule** — an entry replaces the built-in entry of the same
  name as a whole.
- **The built-in harnesses** — `claude-code` with `session =
  ["CLAUDE_CODE_SESSION_ID"]`, and `codex` with `session = ["CODEX_THREAD_ID",
  "CODEX_SESSION_ID"]` and `parent = ["CODEX_SESSION_ID"]`.
- **`Log` and `Harness`** — frozen dataclasses of `wio.models.config`:
  `Harness(session: tuple[str, ...], parent: tuple[str, ...] = ())` and
  `Log(harnesses: frozendict[str, Harness], prefer_harness: tuple[str, ...] =
  (), record_env_vars: tuple[str, ...] = ("AI_AGENT",))`, reached as
  `Config.log`.
- **The check** — in `wio.config`, with the diagnostics of the other settings,
  each problem below an error of the form `error: <where>: <message>`:
  - A harness table with no `session`, or with an empty one.
  - A variable name that does not match `[A-Za-z_][A-Za-z0-9_]*`, in `session`,
    `parent` or `record_env_vars`.
  - A repeated name in `prefer_harness`, `record_env_vars`, `session` or
    `parent`.
  - A name in `prefer_harness` that is not a built-in or a configured harness.
  - A harness named `none`, which `$WIO_PREFER_HARNESS` reserves.
  - An unknown key of `[log]` or of a harness table, named as the config names
    one elsewhere, such as `log.bogus`.

## Acceptance criteria

The examples use a config that sets nothing under `[log]` unless they say so.

### **AC-1** The built-in harnesses need no configuration

#### The defaults

- **Given** a config with no `[log]` table.
- **When** `wio config show log.harnesses.codex.session`, `wio config show
  log.harnesses.codex.parent`, `wio config show
  log.harnesses.claude-code.session` and `wio config show
  log.record_env_vars` run.
- **Then** they print `["CODEX_THREAD_ID", "CODEX_SESSION_ID"]`,
  `["CODEX_SESSION_ID"]`, `["CLAUDE_CODE_SESSION_ID"]` and `["AI_AGENT"]`, each
  with the source `default`, and `wio config check` exits 0.

### **AC-2** A configured harness is added, or replaces a built-in

#### A new harness

- **Given** a config with `[log.harnesses.cursor]`, `session =
  ["CURSOR_TRACE_ID"]` and `parent = ["CURSOR_PARENT_ID"]`.
- **When** `wio config show log.harnesses.cursor.session`, `wio config show
  log.harnesses.cursor.parent` and `wio config list` run.
- **Then** the first two print `["CURSOR_TRACE_ID"]` and `["CURSOR_PARENT_ID"]`,
  each with the source `file`, and the list holds `cursor` together with
  `claude-code` and `codex`.

#### A built-in that is replaced

- **Given** a config with `[log.harnesses.codex]` and `session =
  ["MY_CODEX_ID"]`.
- **When** `wio config show log.harnesses.codex.parent` and `wio config show
  log.harnesses.claude-code.session` run.
- **Then** the first prints `[]`, because the entry replaced the built-in as a
  whole, and the second prints `["CLAUDE_CODE_SESSION_ID"]` with the source
  `default`.

### **AC-3** The preference is read and checked

#### A preference that names harnesses

- **Given** a config with `prefer_harness = ["codex", "claude-code"]` under
  `[log]`.
- **When** `wio config show log.prefer_harness` and `wio config check` run.
- **Then** they print `["codex", "claude-code"]` with the source `file` and exit
  0.

#### A preference that is refused

- **Given** configs that set `prefer_harness` to `["cursor"]` with no such
  harness, and to `["codex", "codex"]`, and one with `[log.harnesses.none]` and
  `session = ["X"]`.
- **When** `wio config check` runs on each.
- **Then** each exits 1 and prints one `error:` line whose `<where>` is, in
  turn, `log.prefer_harness`, `log.prefer_harness` and `log.harnesses.none`.

### **AC-4** The further variables to record are read

#### A list of variables

- **Given** a config with `record_env_vars = ["MY_VAR"]` under `[log]`.
- **When** `wio config show log.record_env_vars` and `wio config check` run.
- **Then** the first prints `["MY_VAR"]` with the source `file`, and the second
  exits 0.

### **AC-5** A mistake in the log settings is reported

#### A mistake in a harness table or in the variables

- **Given** configs of which each sets `[log.harnesses.a]` with `session =
  ["S"]` unless it says otherwise: one with no `session`, one with `session =
  []`, one with `session = ["bad name"]`, one with `session = ["S", "S"]`, one
  with `parent = ["1X"]`, one with `parent = ["X", "X"]`, one with
  `record_env_vars = ["bad name"]` and one with `record_env_vars = ["AI_AGENT",
  "AI_AGENT"]`.
- **When** `wio config check` runs on each.
- **Then** each exits 1 and prints one `error:` line whose `<where>` is, in
  turn, `log.harnesses.a.session` for the first four, `log.harnesses.a.parent`
  for the next two and `log.record_env_vars` for the last two.

#### An unknown key

- **Given** a config with `bogus = 1` under `[log]`, and one with `bogus = 1` in
  `[log.harnesses.a]` with `session = ["S"]`.
- **When** `wio config check` runs on each.
- **Then** each exits 1 and prints one `error:` line whose `<where>` is, in
  turn, `log.bogus` and `log.harnesses.a.bogus`.

#### Other commands refuse the config

- **Given** a config with an error in `[log]`.
- **When** `wio contracts check` runs.
- **Then** it refuses to run, as it does for any config with an error.
