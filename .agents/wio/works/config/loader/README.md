<!-- wio
id = "fhr0z7"
template = "feature.leaf"
roots = ["wio", "repo"]
depends_on = ["ky2ztw", "wxwwnt", "309p3v"]
-->

# Loading the settings

## Purpose

A command needs the project's settings read from one file, checked for shape,
and handed over as a `Config` with the source of every value, or refused with
every problem at once.

## Goals

- The config is found from the working directory, and its absence is a clear
  error.
- A file becomes a `Config`, or a list of diagnostics that says how to fix each
  problem of it, the shape and every check together, in one run.
- The source of every setting, the file or the default, is known without being
  part of `Config`.
- Every other component receives a `Config` with no error in it, or none.
- Further checks join the same check run without a change to the loader's
  callers.
- A run that finds no problem imports nothing it does not use.

## Non-Goals

- The cross-reference, path and skill checks, and the `wio config check`
  command, which are the checks Work's.
- Printing the settings, which the show Work does.
- A walk up the directories, a per-directory override and an environment
  variable that points at another file.
- Mentioning `wio init` in a message, which comes in v0.2.
- Reading `continuable`: the field exists so that people and agents can read it.

## Assumptions

- **A-1**: A `Repository` finds the root of the repository that contains the
  working directory, and the config is at
  `<root>/.agents/wio/config.toml`.
- **A-2**: A TOML date or time is never a valid setting, because no key of the
  schema holds one.

## Mechanisms

- `Repository.root` and `FileSystem.read_text`, through the ports, to find and
  read the file.
- `decode_toml` and `TomlSyntaxError` of `wio.formats`, for the text.
- A walk of the `Config` dataclasses with `dataclasses.fields`, which builds
  the value, the diagnostics of its shape and the source of each key path from
  the same schema.
- A best-effort `Config`, built even when the file has errors, so the checks can
  run and one run reports every problem: an invalid value gets its default, an
  unknown key and an entry of the wrong type are dropped, and a root or an
  action that lacks a required key is kept with it empty.
- For an unknown key, a search of the other tables of the schema for a field of
  that name, which gives the hint of where the key belongs.
- `difflib.get_close_matches`, imported only when a diagnostic needs a closest
  match.
- `wio.config`, which holds the loader and adapts it to the `Settings` port of
  `wio.ports`.

## Constraints

- **What a message holds beyond the parent's rule.** An unknown key names the
  valid keys beside it, the closest match and, when another table has a key of
  that name, the tables it belongs to. A stage with both or neither of `goal`
  and `skill` says what each is. Nothing is coerced: an integer where a string
  belongs is an error.

## Visuals

Before, no loader exists (`main` at commit
`e7b10d8cde19aaf60eaae4a650ffd96b29dcd6d3`). After, it is one function with two
views. Bold boxes are added.

```mermaid
flowchart LR
    file["config.toml"] --> decode["decode_toml"]
    decode --> walk["walk of the schema"]:::new
    walk --> loaded["(config or None, diagnostics, sources)"]:::new
    loaded --> load["Settings.load: Config, or ConfigurationError"]:::new
    loaded --> check["config check, list, show"]
    classDef new stroke-width: 3px
```

## Acceptance criteria

### **AC-1** The config is found at the root of the repository

The loader, in `wio.config`, reads `<root>/.agents/wio/config.toml`, where the
root is that of the working directory, and refuses when there is no repository
or no file.

```python
@dataclass(frozen=True)
class Loaded:
    config: Config | None
    diagnostics: tuple[Diagnostic, ...]
    sources: frozendict[str, Literal["file", "default"]]


CHECKS: tuple[Check, ...]


def load_config(
    repository: Repository,
    files: FileSystem,
    checks: Sequence[Check] = CHECKS,
) -> Loaded: ...
```

#### Found from a subdirectory

- **Given** a repository whose config sets `[works] hierarchy = "nesting"`, and
  the working directory in a subdirectory.
- **When** `load_config` runs.
- **Then** `config.works.hierarchy` is `"nesting"`.

#### Missing

- **Given** a directory outside any repository, and a repository without a
  config file.
- **When** `load_config` runs in each.
- **Then** each raises `ConfigurationError` that names the path looked at and
  does not mention `wio init`; with no repository it names the working
  directory.

### **AC-2** A key the file does not set keeps its default

The loader builds `Config` from the table of the file, and a key it does not
set has the default of its field.

#### An empty file and a partial one

- **Given** an empty file, and a file that sets only `[trailers] reader = "git"`
  and one stage.
- **When** `load_config` runs on each.
- **Then** the first gives `Config()` with no diagnostics, and the second gives
  `trailers.reader` `"git"`, one stage with `session` `"any"` and `continuable`
  true, and every other field its default.

### **AC-3** The source of every setting is known

`sources` maps every key path of the effective settings that has a value to
`file` or `default`, built from the fields of `Config`, so it cannot drift from
the schema. It lists leaf settings only: a table entry such as `stages.define`
has no key of its own, and its keys are `file` when set and `default` when not.
An optional setting that is `None` has no entry.

#### Defaults and file values

- **Given** a file that sets `[works] hierarchy = "flat"`, which is the default,
  and one stage with `goal` set.
- **When** `load_config` runs.
- **Then** `works.hierarchy` is `file`, `works.dir` is `default`,
  `stages.define.goal` is `file`, `stages.define.session` is `default`, and
  every key path of `Config()`, with those of the stage, has an entry, except
  the optional settings that are `None`: `bundle.size_threshold`,
  `stages.define.judge` and `stages.define.roots` have none.

#### A new field

- **Given** the dataclasses of `Config`.
- **When** the key paths of `sources` for an empty file are compared with the
  fields found by walking them, leaving out the optional settings that are
  `None`.
- **Then** they are the same set.

### **AC-4** Every shape problem is reported at once

The loader returns all the diagnostics of the shape of a file, each naming the
key path and how to fix it, and runs the checks of AC-7 on a best-effort
`Config`; `Loaded.config` is `None` whenever any diagnostic of the check run,
of the shape or of a check, is an error. A root or an action that lacks a
required key is kept with it empty, an entry of the wrong type is dropped, and
a stage with both or neither of `goal` and `skill` is kept as written, so the
a check that looks the entry up finds it and does not repeat the problem.

#### An unknown key

- **Given** a stage with a key `sessions`.
- **When** `load_config` runs.
- **Then** `config` is `None` and one error is at `stages.define.sessions` that
  says the key is unknown, suggests `session`, and lists the valid keys of a
  stage.

#### A key that belongs elsewhere

- **Given** `rules_exclude` on a root, `rule_presets` on an action, and
  `rules_always_include` inside a stage.
- **When** `load_config` runs.
- **Then** each unknown-key error names the tables whose schema has a key of
  that name: a stage and a rule preset for `rules_exclude`, a root for
  `rule_presets`, and for `rules_always_include` the top level of the config.

#### A wrong value and a wrong type

- **Given** `[works] hierarchy = "nest"` and `[trailers] reader = 3`.
- **When** `load_config` runs.
- **Then** two errors come back at once: `works.hierarchy` names the received
  `"nest"`, the allowed `"flat"` and `"nesting"` and the setting's description,
  and `trailers.reader` names the received `3`, the expected string and the
  description.

#### A missing required key

- **Given** a root without `paths`, and an action without `description`.
- **When** `load_config` runs.
- **Then** each has an error at its table that names the missing key and the
  setting's description.

#### A broken entry does not cascade

- **Given** a root `wio` without `paths`, a stage whose `roots` is `["wio"]`,
  and a stand-in check passed in `checks` that reports an unknown root for each
  name in a stage's `roots` that is not a key of `Config.roots`.
- **When** `load_config` runs.
- **Then** exactly one error is reported, for the missing `paths`, and the
  stand-in reports none.

#### A wrong default action

- **Given** `[works.defaults.actions]` with `define = 3`.
- **When** `load_config` runs.
- **Then** an error at `works.defaults.actions.define` names the received `3`
  and says a value is a stage preset id or a list of stage names.

#### The other vocabularies

- **Given** a stage with `session = "later"` and `judge = "robot"`.
- **When** `load_config` runs.
- **Then** one error lists `"any"` and `"fresh"`, and one lists `"human"`.

#### A date or a time

- **Given** a key set to a TOML date, and another to a TOML time.
- **When** `load_config` runs.
- **Then** each has an error at its key path that says no setting holds a date
  or a time.

#### Both or neither of goal and skill

- **Given** one stage with both `goal` and `skill`, and one with neither.
- **When** `load_config` runs.
- **Then** each has an error that says what `goal` and `skill` are and that
  exactly one is needed.

### **AC-5** A syntax error is one diagnostic with a position

A file that is not valid TOML gives one error at
`<file>:<line>:<column>` and no `Config`.

#### An invalid file

- **Given** a config whose second line is `b = = 2`.
- **When** `load_config` runs.
- **Then** `diagnostics` is one error whose `where` is
  `.agents/wio/config.toml:2:5`, the path relative to the repository root with
  the line and the column.

### **AC-6** `Settings.load` returns a `Config` or refuses

`Settings.load` returns the `Config` when no diagnostic is an error, and
otherwise raises `ConfigurationError` that carries every error and renders
them, warnings and notes never blocking.

```python
class ConfigSettings:
    def __init__(
        self,
        repository: Repository,
        files: FileSystem,
        checks: Sequence[Check] = CHECKS,
    ) -> None: ...
    def load(self) -> Config: ...
```

#### Valid and invalid

- **Given** a valid config, one with two shape errors, and a valid config with a
  check passed in `checks` that returns a warning and a note.
- **When** `load` runs on each.
- **Then** the first returns the `Config`, the second raises with both errors in
  `diagnostics` and in its message, and the third returns the `Config`.

### **AC-7** A further check joins the same check run

A check (see the parent's glossary) is kept in `CHECKS`, one ordered tuple in
`wio.config` that the loader runs after the shape, also when the shape has
errors, on the best-effort `Config`, so a leaf that adds one changes neither the
loader's callers nor `Settings.load`. `CheckInputs` is provisional; `Loaded`,
`load_config`, `Check` and `CHECKS` are required, since the commands depend on
them. A test adds a check by passing `checks`, or, for the `check` command, by
replacing `wio.config.CHECKS`, which the command reads when it runs.

```python
@dataclass(frozen=True)
class CheckInputs:
    root: Path
    files: FileSystem


Check = Callable[[Config, CheckInputs], Iterable[Diagnostic]]
```

#### An added check

- **Given** a check that returns an error at `x`, passed in `checks`, and a file
  with a valid shape, and then one with an unknown key.
- **When** `load_config` and `Settings.load` run on each.
- **Then** for the first the diagnostics hold that error, `config` is `None` and
  `load` raises; for the second they hold the unknown-key error and that error,
  both at once.

### **AC-8** Loading imports nothing it does not use

A valid file loads without importing `difflib`, `json` or `tomlkit`.

#### A fresh interpreter

- **Given** a new Python process and a valid config.
- **When** `load_config` runs and `sys.modules` is read.
- **Then** none of the three is there, and `difflib` is there after a config
  with an unknown key.

## Additional context

- [Concepts: the config](../../../../../docs/concepts.md#the-config) lists
  every table and key the shape covers.
