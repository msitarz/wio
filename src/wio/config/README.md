# `wio.config`

The component that reads the project's settings. The terms Source, Shape, Key
path, Check and Check run are defined in the [glossary of this
component](GLOSSARY.md), and Config, Diagnostic and Repository in the
[repository glossary](../../../GLOSSARY.md). The keys the shape covers are
listed in the [config](../../../docs/concepts.md#the-config).

## The loader

`load_config(repository, files, checks)` turns one file into a `Loaded`: the
`Config`, every diagnostic of the check run, and the source of each setting. It
exists so that a command receives the settings read from one file, checked for
shape and handed over complete, or is refused with every problem at once.

- **Where.** The config is `<root>/.agents/wio/config.toml`, where the root is
  the one `Repository.root` finds for the working directory, so a command run
  from a subdirectory finds the same file. There is no walk up the directories,
  no per-directory override and no variable that points at another file: one
  file keeps every command reading the same settings.
- **Absence is an error.** No repository, no file or an unreadable file raises
  `ConfigurationError` that names the path looked at, or the working directory
  when there is no repository, and does not mention `wio init`, which does not
  exist before v0.2. A key the file omits keeps the default of its field, so an
  empty file is valid and gives `Config()`, and a file need set only what
  differs from the defaults. The component
  does not read the working directory itself: the `Repository` adapter names it
  in the message of its `RuntimeError`, which the port documents, so every
  component reaches the environment through a port.
- **A syntax error is one diagnostic.** A file that is not valid TOML gives one
  error whose place is `.agents/wio/config.toml:<line>:<column>`, relative to
  the root, no `Config` and no `sources`, because nothing can be checked in
  text that is not a document.
- **`Loaded.config` is `None` whenever any diagnostic is an error.** Every other
  component receives a `Config` with no error in it, or none. Warnings and notes
  never block. Diagnostics come back in the order of `sort_diagnostics`.
- **`Loaded.sources`** maps each key path of the effective settings that has a
  value to `file` or `default`, so a command can show where a value comes from
  without the `Config` carrying it. It lists leaf settings only: a table entry
  such as `stages.define` has no key of its own, and its keys are `file` when
  set and `default` when not. A setting that is `None` has no entry. A key that
  the file sets to its own default is `file`. The paths come from the fields of
  `Config`, so a new field is a new path with no second list to update.

## The shape

`read_shape` walks a schema that `wio.config.schema` derives once from the
annotations of the `Config` dataclasses, and builds the value, the diagnostics
and the sources in that one walk, so none can drift from the fields.

- **Everything is reported at once.** One run returns every problem of the
  shape, so an agent that edits the file corrects all of them in one turn.
- **The `Config` is best effort.** An invalid value gets its default, an unknown
  key and an entry of the wrong type are dropped, a root or an action that lacks
  a required key is kept with it empty, and a stage with both or neither of
  `goal` and `skill` is kept as written. The checks run on it, also when the
  shape has errors, and a check that looks an entry up finds it instead of
  repeating the shape's problem.
- **Nothing is coerced.** An integer where a string belongs is an error, and a
  TOML date or time is never a setting, because no key of the schema holds one.
- **A message tells how to fix the edit.** It names the key path, and it adds
  what the shape knows. An unknown key lists the valid keys beside it, the
  closest one and the tables whose schema has a key of that name. A wrong value
  or type names the received value, what is allowed or expected, and the
  setting's description. A missing key names the key and its description. A
  stage says what `goal` and `skill` are and that exactly one is needed.
- **`difflib` loads only for a closest match.** A run that finds no problem
  imports neither `difflib`, `json` nor `tomlkit`, so a valid config costs
  nothing for its diagnostics.

## The checks

A check, a function from the `Config` and `CheckInputs` to diagnostics, is kept
in `CHECKS`, one ordered tuple that the loader runs after the shape. A Work that
adds a check appends it there and changes neither the callers of `load_config`
nor `Settings.load`.

- `Loaded`, `load_config`, `Check` and `CHECKS` are required, since the commands
  depend on them. `CheckInputs`, the root and the file port, is provisional: a
  check that needs more adds a member.
- A check never raises for a problem of the config, and it gets a best-effort
  `Config`, so it must not report again what the shape reported.
- `load_config` and `ConfigSettings` bind `CHECKS` as the default of their
  `checks` argument when they are defined. A command that must see a replaced
  tuple, as a test of `wio config check` does, reads `wio.config.CHECKS` when it
  runs and passes it.

## `ConfigSettings`

`ConfigSettings` adapts the loader to the `Settings` port of `wio.ports`.
`load` returns the `Config` when no diagnostic is an error, and otherwise raises
`ConfigurationError` that carries every error and renders them as its message,
so a command prints one message and a caller can render the diagnostics its own
way.

## What is not here

- The cross-reference, path and skill checks, and the `wio config check`
  command, which join the check run through `CHECKS`.
- Printing the settings, which the `show` command does with `Loaded.sources`.
- Reading `continuable`: the field exists so that people and agents can read
  it, and no component acts on it.
