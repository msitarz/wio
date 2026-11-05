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
- The `Settings` adapter, so the command refuses a config with errors as every
  command does.
- `wio.cli`'s table of commands, which gains the `config` command and its
  subcommands.

## Constraints

- **Plain and JSON.** Output is sorted by key path and has no timestamps, and a
  value is printed in TOML syntax: strings quoted, lists as arrays.
- **Streams and codes.** The result goes to standard output with exit 0; a
  config with errors prints nothing there and exits 2 with the errors on
  standard error.
- **Import-light.** Importing the command loads no module of its implementation,
  and `json` is imported only with `--json`.

## Acceptance criteria

### **AC-1** Bare `wio config` shows the component's help

`wio config` with no subcommand prints the usage of `wio config` and its
subcommands `list` and `show`, and exits 0.

#### The help

- **Given** a repository with a valid config.
- **When** `wio config` runs.
- **Then** the output names `list` and `show`, and the exit code is 0.

### **AC-2** `wio config list` prints every setting with its source

Each setting is one line, `key.path = value  # file` or `# default`, sorted by
key path, at most 80 columns wide.

```text
wio config list [--json]
```

#### Lines and shortening

- **Given** a config that sets one `goal` of three lines and an `alias` of
  ninety characters.
- **When** `wio config list` runs.
- **Then** the goal's line shows the first line of the value and `…`, every line
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
  `{"value": ..., "source": "file" | "default"}`, with no value shortened.

### **AC-3** `wio config show` prints a setting or a table in full

`wio config show [key.path]` prints the setting or the table at the key path in
full, each with its source, and under a setting its description.

```text
wio config show [key.path] [--json]
```

#### A setting

- **Given** a config that sets `[works] hierarchy = "nesting"`.
- **When** `wio config show works.hierarchy` runs.
- **Then** the output is `works.hierarchy = "nesting"  # file` and under it the
  description of the setting.

#### A table and the whole config

- **Given** a config with two stages, one with a three-line `goal`.
- **When** `wio config show stages` and `wio config show` run.
- **Then** the first prints every setting under `stages`, the goal in full, the
  second every setting of the config, and with `--json` each gives the value or
  subtree with the source of each setting and no description.

#### An unknown key path

- **Given** the key path `stage.define`.
- **When** `wio config show stage.define` runs.
- **Then** it exits 2 with a message that names the closest match `stages` and
  the valid top-level keys.

### **AC-4** A config with errors is refused

`list` and `show` print the errors of the config and exit 2, as any command
does.

#### An invalid config

- **Given** a config with an unknown key.
- **When** `wio config list` and `wio config show` run.
- **Then** each exits 2, standard output is empty and standard error lists the
  error.

### **AC-5** The command is light to start

Importing the command loads no module under `wio.config` other than its
`__init__`, and `json` is loaded only with `--json`.

#### A fresh interpreter

- **Given** a new Python process.
- **When** the table of commands is described and `wio config list` runs
  without `--json`.
- **Then** `json` is not in `sys.modules`.

## Additional context

- [Command line Work](../../../../../docs/v0.1-scope.md#the-wio-command-line)
  states the rules of exit codes and streams that this command follows.
