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
  when there is no repository (only when git cannot be run does it name the
  tool instead), and does not mention `wio init`, which does not exist before
  v0.2. A key the file omits keeps the default of its field, so an
  empty file is valid and gives `Config()`, and a file need set only what
  differs from the defaults. The component does not read the working directory
  itself: the `Repository` adapter is given it by an `Environment` and names it
  in the message of its `RuntimeError`, which the port documents, so every
  component reaches the environment through a port. That message also says
  whether the directory does not exist, is not a directory, cannot be entered or
  is in no repository, and what to do, and the loader passes it on unchanged.
  The messages of a missing file and of a file that cannot be read name the path
  once, say in words what is wrong (it is missing, unreadable for permissions, a
  directory, not valid UTF-8) and what to do next, and carry no Python-style
  error text, so a person or an agent knows the next step. For any other OS
  error the message gives the OS's own reason, such as "Input/output error".
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

## The command

`wio config` lets a person or an agent see the effective settings, where each
value comes from and what each setting is for. The package's `describe()`
returns the spec of the command, and `ConfigCommand` runs it. The spec is made
in the `__init__` of the package, so describing the command loads no other
module of `wio.config`, and `ConfigCommand` is bound with a `lazy` import for
the same reason: every run of `wio` describes every command, and a run that does
not choose `config` must not pay for it.

- **Bare `wio config`** prints its own usage and exits 0, without reading the
  config file, so it works in a project whose config is broken.
- **`list`** prints one line for each setting that has a value, as
  `key.path = value  # file` or `# default`, in key-path order. A line is at
  most 80 columns where it can be. A string of several lines shows its first
  line, then `…` before the closing quote, a string or an array that is too long
  is cut with `…`, and the key path and the label are never cut, so a line whose
  key path and label reach 80 columns shows `…` as its value and is longer.
- **`show`** prints the setting or the table at a key path in full, with its
  source. A single setting is followed by a line with its description, and a
  table prints the setting lines only. With no key path it prints the whole
  config. A string is written on one line, its newlines as `\n`, so every
  setting stays one line.
- **`--json`**, on both, writes one object that maps each key path to
  `{"value": ..., "source": ...}`, sorted by key path and never shortened. The
  `json` module is imported only for it.
- **A table with no setting**, such as `roots` of a config without roots, prints
  nothing and exits 0, and `{}` with `--json`.
- **What cannot be shown exits 2** and says what to ask for. An unknown key path
  names the closest match and the keys it could have been, an optional setting
  that is not set says so, and an item of a list is refused because a list is
  shown whole, under its own key path.
- **A config with an error is refused** like it is for every other command:
  nothing reaches standard output and standard error lists the errors.
  `list` and `show` read `Loaded.sources`, which `Settings` does not return, so
  they call `load_config` and raise the errors themselves through
  `config_or_raise`, the one place that `ConfigSettings.load` shares.

Three small modules hold the logic, so each can be tested without the others:

- `settings_of` in `listing.py` walks the `Config` once and yields a `Setting`
  for each leaf that has a value, with the source from `Loaded.sources` and the
  description from the field. A list is a leaf and a table has no setting of its
  own. The same module writes the lines and the JSON object.
- `resolve` in `keypath.py` follows a key path through the `Config` and returns
  a `Target`, a single setting or a table, judging it by the fields of the
  `Config` alone. That is how a table without entries is told from an unknown
  key.
- `ConfigCommand` in `command.py` composes them with the loader and writes to
  the streams it is given.

## What is not here

- The cross-reference, path and skill checks, and the `wio config check`
  command, which join the check run through `CHECKS`.
- Reading `continuable`: the field exists so that people and agents can read
  it, and no component acts on it.
