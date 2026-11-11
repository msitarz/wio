<!-- wio
id = "h69nf8"
template = "feature.leaf"
roots = ["wio"]
depends_on = []
-->

# Shared helpers of the templates and contracts commands

## Purpose

`wio.templates` and `wio.contracts` need the same walk of the Works directory,
the same ordering and rendering of a check's findings, and the same suggestion
for a mistyped key, and neither component may import the other. Each helper
therefore moves to a package both may import, so one copy exists and the later
commands use it. `wio.config` already has its own copies of two of them, and
joins them.

## Goals

- One walk of the Works directory, which `wio templates` and `wio contracts`
  both use.
- One place that finds the closest known key to a mistyped one, used by
  `wio config`, `wio templates` and `wio contracts`, and the only importer of
  `difflib`.
- One `has_error`, one ordering of diagnostics by file, line and column, and one
  rendering of a check's result, used by `wio templates` and `wio contracts`,
  with `has_error` also used by `wio config`.
- A person who mistypes a key in a template is told the closest valid key, as a
  person who mistypes a key in the config already is.
- Every other output of `wio config` and `wio templates` stays as it is.

## Glossary

- **Closest key**: the one known key that `difflib.get_close_matches` ranks
  first for a mistyped key, with its default cutoff, or none.

## Non-Goals

- The unknown-key check of a contract, a warning that names the closest key,
  which the check-works leaf builds with the function made here.
- Joining the messages of the three commands for an unknown key. Each keeps its
  own wording, and only the matching is shared.
- Giving `wio config check` a line and a column, or one ordering of diagnostics
  for all three `check` commands, and changing `sort_diagnostics`.
- Sharing what is specific to one command: grouping templates by name, finding
  the templates that discovery could not build, and finding the Works.

## Assumptions

- **A-1**: The existing tests of `wio config` and `wio templates` pin their
  messages and their output, so a move that changes either shows as a failing
  test.
- **A-2**: A component may import a function from `wio.io`, not only a port,
  because `wio.io` is a module that every component may depend on.
- **A-3**: `difflib.get_close_matches(key, known, n=1)` with its default
  cutoff is what both sites of `wio config` use today, and what the new callers
  need.

## Mechanisms

- A module `walk.py` in `wio.io` with `walk_markdown(directory, files)`, which
  yields the Markdown files below a directory, and
  `refuse_directory(directory, written, files, *, noun, default)`, which judges
  the directory itself. Both take a `FileSystem` and read no file.
- `closest_key(key, known)` and `render_check(diagnostics, *, as_json, passes)`
  in `wio.formats`. `closest_key` is the one importer of `difflib`, lazily, and
  returns the closest key or `None`.
- `order_diagnostics` and `has_error` in `wio.models.diagnostics`, beside
  `Diagnostic` and `sort_diagnostics`, reusing that module's rank of severities.
- The callers that change: `wio.templates` (discovery, check and command) and
  `wio.config` (`messages.py`, `keypath.py`, `loader.py` and `report.py`).
- Ruff's `banned-api` table, which gains `difflib` outside `wio.formats` as it
  bans `tomllib` and `markdown_it`.
- The names and the signatures above are fixed. The tests and what else a
  module holds are for the architecture stage.

## Constraints

- **Moved, not changed.** Every output of `wio config` and `wio templates` is
  byte for byte what it was, except the message of a mistyped key in a template,
  which gains the closest key.
- **Nothing is imported before it is needed.** A run that finds no mistyped key
  does not import `difflib`, as the config's own README already requires, and
  neither does a run that renders no result.
- **The helpers import only what they need.** `wio.io.walk` imports the
  `FileSystem` port and the standard library, `closest_key` and `render_check`
  import `wio.models` and the standard library, and the two functions of
  `wio.models.diagnostics` import nothing else.

## Visuals

Before (`main` at `929f0d4`), `wio.templates` holds the walk, `has_error`, the
ordering and the rendering of a check, and `wio.config` matches keys with its
own `difflib` calls and repeats `has_error` inline. After, one copy of each
lives where both components, and later `wio.contracts`, can import it. Bold
boxes are added and bold dashed boxes change.

```mermaid
flowchart LR
    templates["wio.templates"]:::changed
    config["wio.config"]:::changed
    contracts["wio.contracts, later"]
    walk["wio.io: walk_markdown, refuse_directory"]:::new
    formats["wio.formats: closest_key, render_check"]:::changed
    diagnostics["wio.models: order_diagnostics, has_error"]:::changed
    templates --> walk
    templates --> formats
    templates --> diagnostics
    config --> formats
    config --> diagnostics
    contracts -.-> walk
    contracts -.-> formats
    contracts -.-> diagnostics
    classDef new stroke-width: 3px
    classDef changed stroke-width: 3px,stroke-dasharray: 4 3
```

## Acceptance criteria

### **AC-1** The walk yields the visible Markdown files

`walk_markdown` yields the files whose names end in `.md` with that case, below
a directory, and nothing else.

#### A tree with files to skip

- **Given** a tree held by a fake `FileSystem`: `a.md`, `B.MD`, `notes.txt`,
  `sub/f.md`, `.hidden/c.md`, a symbolic link to a directory that holds `d.md`,
  and a symbolic link to a file named `e.md`.
- **When** `walk_markdown` runs on its root.
- **Then** it yields `a.md` and `sub/f.md`, in the order of the listing, and it
  has read no file.

### **AC-2** The directory itself is judged with the caller's noun

`refuse_directory` returns one error for a directory that cannot be walked, and
none for one that can, or for a missing default.

#### Each case

- **Given** `noun="templates"` and `default=".agents/wio/templates"`, and a
  directory that is a symbolic link, one that is missing and written as
  `other`, one that is a file, one that is missing and written as
  `.agents/wio/templates`, and an ordinary directory.
- **When** `refuse_directory` runs on each.
- **Then** the first three return an error whose message is `The templates
  directory must not be a symbolic link`, `The templates directory does not
  exist` and `The templates directory is not a directory`, whose place is the
  path as written, and the last two return none.

#### Another noun

- **Given** `noun="Works"` and a directory that is a symbolic link.
- **When** `refuse_directory` runs on it.
- **Then** the message reads `The Works directory must not be a symbolic link`.

### **AC-3** The closest key is found, and `difflib` loads only then

`closest_key` returns the closest known key or none, and importing `wio.formats`
or running a command that finds no mistyped key does not import `difflib`.

#### The match

- **Given** the known keys `description` and `kind`.
- **When** `closest_key` runs for `descriptions`, for `zzz`, and for `kind` with
  no known keys.
- **Then** the results are `description`, none and none.

#### A fresh interpreter

- **Given** a new Python process, a valid config and valid templates.
- **When** `wio.formats` is imported, then `main(["config", "check"], stdio)`
  and `main(["templates", "check"], stdio)` of `wio.cli` run, and `sys.modules`
  is read, and then `closest_key` is called and it is read again.
- **Then** `difflib` is not there the first time and is there the second.

### **AC-4** `wio config` says what it said

The two sites of `wio config` that suggest a key give the same messages as
before, and `wio config` imports `difflib` nowhere itself.

#### A mistyped setting and a mistyped key

- **Given** a config with a `[stages]` table, and another whose stage `define`
  has the key `sessionn`.
- **When** `wio config show stagez` and `wio config check` run on them.
- **Then** the first prints an error that names `stagez` and says
  ``Did you mean `stages`?`` and exits 2, and the second reports the unknown key
  `sessionn` with ``Did you mean `session`?`` and exits 1, each with the text it
  had before this change.

#### The import

- **Given** the modules of `wio.config`.
- **When** `ruff check` runs on `src/wio`, with one of them importing `difflib`.
- **Then** it reports `TID251` for that import, and for none in `wio.formats`.

### **AC-5** A template says the closest key

The error of an unknown key in a template's metadata names the closest key when
there is one, and is as it was when there is none.

#### Close and far

- **Given** two templates, one whose metadata has the key `descriptions` and one
  that has the key `zzz`.
- **When** `wio templates check` runs.
- **Then** it reports ``Unknown key `descriptions` in the metadata. Did you mean
  `description`?`` and ``Unknown key `zzz` in the metadata``, each at its file,
  and exits 1.

### **AC-6** One `has_error`, one ordering, one rendering

`has_error` tells an error from the rest, `order_diagnostics` orders by file,
line and column as numbers, and `render_check` prints the sentence it is given
when there is nothing to report.

#### The helpers

- **Given** the diagnostics `a.md:10: error`, `a.md:2: warning`,
  `a.md:2: error`, `a.md: note`, `b.md: error` and `nofile: error`.
- **When** `order_diagnostics` runs on them, `has_error` runs on them and on the
  note and the warning alone, and `render_check` runs on none with
  `passes="The contracts pass."`, in text and as JSON.
- **Then** the order is `a.md`, then `a.md:2` error, `a.md:2` warning,
  `a.md:10`, then `b.md`, then `nofile`, `has_error` is true, false, and the
  renderings are `The contracts pass.` and `[]`, each ending in a newline.

#### The same in `config`

- **Given** a config with a warning and no error, and one with an error.
- **When** `wio config check` runs on each.
- **Then** the first exits 0 and the second exits 1, with the output they had.

### **AC-7** `wio templates` prints what it printed

Apart from a mistyped key, every output of the three commands that use the
moved helpers is the same.

#### The repository's templates and a broken directory

- **Given** this repository's templates, and a repository whose templates
  directory is a symbolic link.
- **When** `wio templates list`, `wio templates check` and
  `wio templates check --json` run on each.
- **Then** on the first, the outputs and exit codes are those of the commands
  before this change, and `check` prints `The templates pass.`. On the second,
  `check` prints `error: .agents/wio/templates: The templates directory must
  not be a symbolic link` and exits 1, and `list` prints that error and a line
  that points to `wio templates check`, and exits 2.

## Additional context

- The check-works leaf builds the unknown-key warning of a contract on
  `closest_key`.
- The ordering moved here is the one of `wio templates check`. It is replaced
  when `wio config check` gets a line and a column and the three commands share
  one ordering.
- This leaf changes tests of `wio templates` and `wio config`, and the README of
  `src/wio/config` where it says that `difflib` is imported lazily.
