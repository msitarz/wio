# `wio.config`

The component that reads the project's settings. The terms Source, Shape,
Setting, Key path, Check and Check run are defined in the [glossary of this
component](GLOSSARY.md), and Config, Diagnostic and Repository in the
[repository glossary](../../../GLOSSARY.md). The keys the shape covers are
listed in the [config](../../../docs/concepts.md#the-config).

## The loader

[`loader.py`](loader.py) turns one file into a `Loaded`: its docstrings say what
it returns and what it raises. It exists so that a command receives the settings
read from one file, checked for shape and handed over complete, or is refused
with every problem at once. [`settings.py`](settings.py) adapts it to the
`Settings` port.

- **One file.** The config is `<root>/.agents/wio/config.toml`, where the root
  is the one `Repository.root` finds for the working directory, so a command run
  from a subdirectory finds the same file. There is no walk up the directories,
  no per-directory override and no variable that points at another file: one
  file keeps every command reading the same settings.
- **Absence is an error.** No repository, no file and an unreadable file are
  refused, and none of the messages mentions `wio init`, which does not exist
  before v0.2. A key the file omits keeps the default of its field, so an empty
  file is valid and a file need set only what differs from the defaults. The
  component never reads the working directory itself: the `Repository` adapter
  is given it by an `Environment`, so every component reaches the environment
  through a port, and the loader passes the adapter's message on unchanged.
- **A syntax error is one diagnostic and no `Config`,** because nothing can be
  checked in text that is not a document.
- **`Loaded.sources` says `file` for a key that the file sets to its own
  default.** A table entry such as `stages.define` has no key of its own, and
  its keys are `file` when set and `default` when not.

## The shape

`read_shape` in [`shape.py`](shape.py) walks a schema derived once from the
annotations of the `Config` dataclasses, so the value, the diagnostics and the
sources cannot drift from the fields.

- **The `Config` is best effort,** so the checks run on it also when the shape
  has errors, and a check that looks an entry up finds it instead of repeating
  the shape's problem. A stage with both or neither of `goal` and `skill` is
  kept as written.
- **Nothing is coerced.** An integer where a string belongs is an error, and a
  TOML date or time is never a setting, because no key of the schema holds one.
- **A message tells how to fix the edit,** so an agent that edits the file
  corrects every problem in one turn.
- **A run that finds no problem imports neither `difflib`, `json` nor
  `tomlkit`,** so a valid config costs nothing for its diagnostics.

## The checks

[`checks.py`](checks.py) keeps the checks in `CHECKS`, one ordered tuple that
the loader runs after the shape, so a Work that adds a check appends it there.
Its docstrings say which names are required and which are provisional.

`load_config` and `ConfigSettings` bind `CHECKS` as the default of their
`checks` argument when they are defined. A command that must see a replaced
tuple, as a test of `wio config check` does, reads `wio.config.CHECKS` when it
runs and passes it.

## The command

`wio config` lets a person or an agent see the effective settings, where each
value comes from and what each setting is for. The package's `describe()`
returns the spec of the command, and `ConfigCommand` runs it. The spec is made
in the `__init__` of the package, and everything else the package exports,
`ConfigCommand` among it, is bound there with a `lazy from` import, so
describing the command loads no other module of `wio.config`. Every run of
`wio` describes every command, and a run that does not choose `config` must not
pay for it.

- **Bare `wio config` reads no config file,** so it works in a project whose
  config is broken.
- **`list` shortens and `show` does not.** `list` fits a line to 80 columns
  where it can, so a person scans every setting, and `show` and `--json` give a
  value in full. The formats are in [`listing.py`](listing.py).
- **`list` and `show` call `load_config`,** because they read `Loaded.sources`,
  which `Settings` does not return. They raise the errors themselves through
  `config_or_raise`, the one place that `ConfigSettings.load` shares.
- **`resolve` judges a key path by the fields of the `Config` alone,** so a
  table without entries is told from an unknown key.

## What is not here

- The cross-reference, path and skill checks, and the `wio config check`
  command, which join the check run through `CHECKS`.
- Reading `continuable`: the field exists so that people and agents can read
  it, and no component acts on it.
