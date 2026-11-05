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

## Mechanisms

- `wio.config`'s `check` subcommand on the command table, which uses the
  loader's diagnostics and the shared renderer, not `Settings.load`.
- A local hook in `prek.toml` with `files` set to the config's path and
  `pass_filenames = false`.
- `scripts/config_check_hook.py`, which reads the hook's JSON with the standard
  library and runs `wio config check`.
- `.claude/settings.json`, which installs it as a second `PostToolUse` hook.
- `docs/workflow.md`, which shows the script as an example.

## Constraints

- **Hook script.** It runs `wio config check` only when the edited file is the
  config, prints the diagnostics to standard error and exits 2 when the check
  exits 1, and exits 0 in every other case, including a file it does not know.

## Acceptance criteria

### **AC-1** `wio config check` prints the diagnostics of the config

The command prints each diagnostic, sorted, as text or with `--json` as an
array, exits 0 when none is an error and 1 when any is.

```text
wio config check [--json]
```

#### A valid config and an invalid one

- **Given** a valid config, a config with an unknown key, and a config that has
  only a warning.
- **When** `wio config check` runs on each.
- **Then** the first prints nothing and exits 0, the second prints the error as
  `error: <key path>: <message>` and exits 1, and the third prints the warning
  and exits 0; with `--json` the first prints `[]`.

#### A syntax error

- **Given** a config with a TOML syntax error.
- **When** `wio config check` runs.
- **Then** it prints one error at `<file>:<line>:<column>` and exits 1.

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

`scripts/config_check_hook.py` runs the check after a Claude Code edit of the
config and returns the errors to the agent, and `.claude/settings.json`
installs it.

#### An edit of the config with an error

- **Given** the hook's JSON for an edit of `.agents/wio/config.toml`, and a
  config with an error.
- **When** the script reads it on standard input.
- **Then** it prints the diagnostics to standard error and exits 2.

#### Other edits and a valid config

- **Given** the hook's JSON for an edit of a Python file, an edit of the config
  while it is valid, and a document that is not JSON.
- **When** the script reads each.
- **Then** it exits 0 and prints nothing.

#### Installed

- **Given** `.claude/settings.json`.
- **When** its `PostToolUse` hooks are read.
- **Then** one runs the script after `Edit`, `Write` and `MultiEdit`, beside the
  existing formatter.

### **AC-4** The recipe is documented

`docs/workflow.md` shows the script and the `PostToolUse` entry as an example
for any project, says that each project chooses its own, and says when the
prek hook runs.

## Additional context

- [Workflow](../../../../../../docs/workflow.md) gains the recipe.
