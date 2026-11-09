<!-- wio
id = "mcn1xg"
template = "feature.leaf"
roots = ["wio", "repo"]
depends_on = ["fhr0z7", "5s70tt"]
-->

# The check command and its hooks

## Purpose

`wio config check` must print the diagnostics of a config and run by itself
after every edit of it, so that an agent is told what to fix before it goes on.

## Goals

- `wio config check` prints every diagnostic of the config as text or JSON and
  says by its exit code whether there was an error.
- Committing a change to the config runs the check.
- An agent that edits the config is told the errors in the same turn.
- Other projects can copy the recipe for the hook.

## Non-Goals

- The checks beyond the shape, which the other leaves add.
- A hook for any harness but Claude Code in this repository: the recipe shows
  the idea, and each project does its own.
- Generating a hook, which waits for the integrations of v0.3.

## Assumptions

- **A-1**: Claude Code runs a `PostToolUse` hook after `Edit`, `Write` and
  `MultiEdit`, passes it a JSON document on standard input that holds the edited
  file's path in `tool_input.file_path`, and feeds standard error to the model
  when the hook exits 2.
- **A-2**: `uv run wio` runs wio in this repository, as the other hooks run
  their tools through `uv run`, so the hooks need no `wio` on `PATH`.
- **A-3**: `jq` is on the `PATH` of the hook, as the formatter hook already
  assumes.

## Mechanisms

- `wio.config`'s `check` subcommand on the command table, which uses the
  loader's diagnostics and the shared renderer, not `Settings.load`.
- A local hook in `prek.toml` whose entry is `uv run wio config check`, with
  `files` set to the config's path and `pass_filenames = false`.
- `.claude/settings.json`, which installs a second `PostToolUse` hook beside the
  formatter: a shell command that reads the edited path with `jq`, runs
  `uv run wio config check` for the config only and exits 2 with the output on
  standard error when the check fails.
- `docs/workflow.md`, which shows that entry as an example.

## Acceptance criteria

### **AC-1** `wio config check` prints the diagnostics of the config

The command prints each diagnostic, sorted, to standard output as text or with
`--json` as an array, and exits 0 when none is an error and 1 when any is.

```text
wio config check [--json]
```

#### A valid config and an invalid one

- **Given** a valid config, and a config with an unknown key.
- **When** `wio config check` runs on each.
- **Then** the first prints nothing and exits 0, and the second prints the error
  as `error: <key path>: <message>` and exits 1.

#### A warning

- **Given** a valid config and a check put in `wio.config.CHECKS` that returns a
  warning.
- **When** `wio config check` runs.
- **Then** it prints `warning: <where>: <message>` and exits 0.

#### JSON

- **Given** a valid config, and a config with an unknown key.
- **When** `wio config check --json` runs on each.
- **Then** the first prints `[]` and exits 0, and the second prints an array of
  one object with `severity`, `where` and `message`, and exits 1.

#### A syntax error

- **Given** a config with a TOML syntax error.
- **When** `wio config check` runs.
- **Then** it prints one error at `.agents/wio/config.toml:<line>:<column>`, the
  path relative to the repository root, and exits 1.

#### No config

- **Given** a directory outside any repository.
- **When** `wio config check` runs.
- **Then** it exits 2 with a message on standard error, since there is no config
  to check.

### **AC-2** A change to the config runs the check on commit

`prek.toml` has a hook that runs `wio config check` when the config file
changes and passes it no file names.

#### The hook

- **Given** `prek.toml`.
- **When** its hook for the config is read.
- **Then** it runs `wio config check`, matches only
  `.agents/wio/config.toml` and sets `pass_filenames = false`.

### **AC-3** An agent's edit of the config is checked at once

`.claude/settings.json` has a `PostToolUse` hook that runs `wio config check`
after an edit of the config and returns its diagnostics to the agent. It holds
no knowledge of the harness in wio itself.

#### Installed

- **Given** `.claude/settings.json`.
- **When** its `PostToolUse` hooks are read.
- **Then** one runs after `Edit`, `Write` and `MultiEdit`, beside the existing
  formatter, and its command runs `uv run wio config check`.

#### An edit of the config with an error

- **Given** the hook's JSON for an edit whose `tool_input.file_path` is the
  absolute path of `.agents/wio/config.toml`, and a config with an error.
- **When** the command of the hook runs with that JSON on standard input.
- **Then** it prints the diagnostics to standard error and exits 2.

#### Other edits and a config without errors

- **Given** the hook's JSON for an edit of another TOML file, and for an edit
  of the config while it has no error.
- **When** the command of the hook runs with each on standard input.
- **Then** it exits 0 and prints nothing.

### **AC-4** The recipe is documented

`docs/workflow.md` shows the `PostToolUse` entry as an example for any project,
says that each project chooses its own and writes `wio config check` where wio
is installed on the `PATH`, and says when the prek hook runs.

## Additional context

- [Workflow](../../../../../../docs/workflow.md) gains the recipe.
