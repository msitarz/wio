<!-- wio
id = "5s70tt"
template = "feature.leaf"
roots = ["wio", "repo"]
depends_on = ["fhr0z7"]
-->

# Showing the settings

## Purpose

A person or an agent must be able to see the effective settings of a project,
where each value comes from, and what each setting is for, from the command
line.

## Goals

- `wio config` tells what the component offers.
- `wio config list` shows every setting and its source in a short, stable form.
- `wio config show` shows one setting or a table in full, with its meaning.
- Both can be read by a program as JSON.
- A config with errors is refused, not shown.
- Starting the command costs no more than it needs.

## Non-Goals

- `wio config check`, which the checks Work adds as `check`.
- Listing templates, kinds or the names of a table by themselves: the keys of a
  table are in `wio config show <table> --json`, and templates belong to
  `wio templates`.
- Printing a config that has errors: it is refused like any other command.
- Changing a setting.

## Assumptions

- **A-1**: A table of the config, such as `stages`, is a key path whose value is
  its entries.

## Mechanisms

- `Loaded.sources` and the fields of `Config`, for the labels and the
  descriptions.
- `load_config`, whose diagnostics the command raises as a `ConfigurationError`
  itself when any is an error, because `Settings.load` returns no sources.
- `wio.cli`'s table of commands, which gains the `config` command and its
  subcommands.

## Acceptance criteria

### **AC-1** Bare `wio config` shows the component's help

`wio config` with no subcommand prints the usage of `wio config` and the
subcommands it has, and exits 0.

#### The help

- **Given** a repository with a valid config.
- **When** `wio config` runs.
- **Then** the output names `list` and `show`, and the exit code is 0.

### **AC-2** `wio config list` prints every setting with its source

Each setting that has a value is one line, `key.path = value  # file` or
`# default`, with the value in TOML syntax (strings quoted, lists as arrays),
sorted by key path, at most 80 columns wide unless the key path and the label
alone reach 80; an absent optional setting is not listed.

```text
wio config list [--json]
```

#### Lines and shortening

- **Given** a config that sets one `goal` of three lines and an action
  `description` of ninety characters.
- **When** `wio config list` runs.
- **Then** the goal's line shows the first line of the value, then `…` and the
  closing quote, as `stages.define.goal = "Turn an intent…"  # file`, every line
  is at most 80 columns wide with its key path and its `# file` or `# default`
  whole, and the lines are in key-path order.

#### A long key

- **Given** a key path and a source label that together reach 80 columns.
- **When** `wio config list` runs.
- **Then** its value shows as `…`, the key path and the label are whole, and the
  line may be longer than 80 columns.

#### JSON

- **Given** the same config.
- **When** `wio config list --json` runs.
- **Then** the output is one object that maps each key path to
  `{"value": ..., "source": "file" | "default"}`, sorted by key path, with no
  value shortened.

### **AC-3** `wio config show` prints a setting or a table in full

`wio config show [key.path]` prints the setting or the table at the key path in
full, each with its source; for a single setting it also prints the setting's
description under the line, and a table prints the setting lines only.

```text
wio config show [key.path] [--json]
```

#### A setting

- **Given** a config that sets `[works] hierarchy = "nesting"`.
- **When** `wio config show works.hierarchy` and
  `wio config show works.hierarchy --json` run.
- **Then** the first prints `works.hierarchy = "nesting"  # file` and under it
  the description of the setting, and the second prints
  `{"works.hierarchy": {"value": "nesting", "source": "file"}}`.

#### A table and the whole config

- **Given** a config with two stages, one with a three-line `goal`.
- **When** `wio config show stages` and `wio config show` run, and again with
  `--json`.
- **Then** the first prints every setting under `stages`, the goal in full and
  no description, the second every setting of the config, and with `--json`
  each gives the object of `list --json` restricted to the key paths under the
  argument.

#### Unset, empty and inside a list

- **Given** a stage `define` without `judge`, no roots, and a `rules_include`
  list.
- **When** `wio config show stages.define.judge`, `wio config show roots` and
  `wio config show stages.define.rules_include[0]` run.
- **Then** the first exits 2 with a message that the optional setting is not
  set, the second prints nothing and exits 0 (`{}` with `--json`), and the
  third exits 2 with a message that a list is shown whole, as
  `stages.define.rules_include`.

#### An unknown key path

- **Given** the key paths `stage.define` and `stages.definer`, with a stage
  `define`.
- **When** `wio config show` runs on each.
- **Then** each exits 2; the first names the closest match `stages` and the
  valid top-level keys, and the second names `stages.define` and the children
  of `stages`.

### **AC-4** A config with errors is refused

`list` and `show` print the errors of the config and exit 2, as any command
does.

#### An invalid config

- **Given** a config with an unknown key.
- **When** `wio config list` and `wio config show` run.
- **Then** each exits 2, standard output is empty and standard error lists the
  error.

### **AC-5** The command is light to start

Describing the command loads no module of its implementation, and `json` is
loaded only with `--json`.

#### Describing

- **Given** a new Python process.
- **When** the table of commands is described.
- **Then** no submodule of `wio.config` is in `sys.modules`.

#### Listing

- **Given** a new Python process and a valid config.
- **When** `wio config list` runs without `--json`.
- **Then** `json` is not in `sys.modules`.

## Additional context

- [Command line Work](../../../../../docs/v0.1-scope.md#the-wio-command-line)
  states the rules of exit codes and streams that this command follows.
