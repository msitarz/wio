<!-- wio
id = "xtgz9z"
template = "feature.leaf"
roots = ["wio"]
depends_on = ["h69nf8"]
-->

# Finding the Works

## Purpose

Every command that reads Works needs the same answer to which files are Works
and what each says about itself, and a problem with one Work must not hide
another or break the tree around it.

## Goals

- The Works of a project are found by one walk of the Works directory, in
  either hierarchy mode, with the same answer in every command.
- Each Work is read into one value: its id, title, path, template, roots,
  dependencies and action overrides.
- A problem with one Work is reported once, and no other Work is hidden or
  orphaned by it.
- A person who names a file that is not a Work is told why.

## Glossary

- **Marked file**: a file under the Works directory whose name ends in `.md` and
  whose metadata block starts on its first line.
- **Left out**: a marked file that discovery reports and builds no Work from.

## Non-Goals

- Parents, children, the dependency graph and the resolution of `@descendants`,
  which the hierarchy leaf computes from the Works found here.
- Unknown keys, the existence of templates, actions, stage presets, stages and
  roots, and the form of an id, which the check-works leaf judges.
- The sections and the items of a body, which the check-body leaf judges.
- Looking up a Work that is no longer in the tree in the history.
- Printing a reason to a person, which the show leaf does with what this leaf
  returns.

## Assumptions

- **A-1**: The shared leaf is delivered, so the walk, the refusal of the Works
  directory and the ordering of diagnostics are those of `wio.io` and
  `wio.models`.
- **A-2**: `read_metadata_block` returns none for a file whose block does not
  start on its first line, and raises an error with the line of the problem for
  a block it cannot read or whose marker it does not know, as the templates
  discovery already relies on.
- **A-3**: `Config.works` carries `dir`, `hierarchy` and `defaults`.

## Mechanisms

- A function in `wio.contracts` that walks the Works directory and returns the
  Works found with the diagnostics, and a lookup of a Work by id on that
  result.
- A function in `wio.contracts` that says why a given path is not a Work.
- `Work` in `wio.models`, the plain type of a Work found.
- `walk_markdown`, `refuse_directory` and `order_diagnostics` from the shared
  leaf, `read_metadata_block` for the block and `read_outline` for the title.
- The `FileSystem` port, through which every file is read and none is written.
- The names, the signatures and the fields of `Work` are provisional, for the
  architecture stage to decide.

## Constraints

- **Reported, not raised.** A problem with a file or a Work is a diagnostic. The
  Works directory that cannot be walked is one error and no Work is found.
- **A Work is left out only when it cannot be identified.** A file that cannot
  be read or decoded, a block that cannot be read or whose marker is unknown,
  and an `id` that is missing, not a string or empty each give one error and no
  Work.
- **A wrong optional field is empty and reported.** A `template`, `roots`,
  `depends_on` or `[actions]` of the wrong type gives one error, the Work is
  built with that field empty, and it stays in the tree.
- **A shared id keeps both Works.** Both stay in the tree with one error that
  names both paths, and a lookup by that id is refused with that error.
- **Nesting collisions are the concepts'.** Under `nesting`, a directory with
  two or more marked files holds no Work, one error names all of them, and a
  marked file directly in the Works directory is not a Work. Under `flat`
  neither rule applies.
- **Every place is a path.** A diagnostic's place is the file's path relative to
  the repository root, written with `/`, followed by `:<line>` for a problem of
  the block, and the paths of a shared id are joined by a comma and a space.
- **Read, never written.** Every file is read through `FileSystem`, and no file
  is written.
- **The output is deterministic.** The Works are sorted by path, and the
  diagnostics are ordered as `order_diagnostics` orders them.

## Acceptance criteria

### **AC-1** Marked files become Works with their fields

Each marked file is read into a Work with its id, title, path, template, roots,
dependencies and action overrides, in the order of their paths, and a file that
is not marked is ignored.

#### A tree of Works

- **Given** `hierarchy = "nesting"` and, under the Works directory,
  `a/README.md` with a comment block that has `id = "k3m9xq"`,
  `template = "feature.leaf"`, `roots = ["wio"]`, `depends_on = ["a7b2c4"]` and
  an `[actions]` table with `define = "define-feature"` and
  `deliver = ["implementation"]`, and a body that starts with `# First`,
  `b/spec.md` with `+++` front matter that holds `wio = 1` and `id = "a7b2c4"`
  and a body with `## Only` and no `#` heading, `a/notes.md` with no block,
  `c/x.md` with a block on its second line, a hidden directory `.git` holding a
  marked file, and a symbolic link to a marked file.
- **When** the Works are discovered.
- **Then** there are two Works, `a/README.md` and `b/spec.md`, with those ids,
  `First` and `Only` as their titles, the first with its template, roots,
  dependencies and both overrides as written, the second with no template, no
  roots, no dependencies and no overrides, there is no diagnostic, and no file
  has been written.

### **AC-2** A Work that cannot be identified is left out with one error

A file that cannot be read or decoded, a block that cannot be read, a marker of
an unknown version, and a missing, non-string or empty id each give one error at
the file and no Work, while the other Works are found.

#### Six broken files and a good one

- **Given** Works under the Works directory: a file that is not UTF-8, a comment
  block that does not close at its line 3, `wio = 2` in `+++` front matter, a
  block without an `id`, `id = ""`, `id = 12`, and a good Work.
- **When** the Works are discovered.
- **Then** the good Work is found, and there is one error for each of the six
  files, at the file, with `:3` for the block that does not close, and no other
  diagnostic.

### **AC-3** A wrong optional field is reported and the Work stays

An optional key of the wrong type is an error, the Work is built with that field
empty, and the Work keeps its place in the tree.

#### Three wrong fields

- **Given** `hierarchy = "nesting"`, a Work `p` with `roots = "api"` that has a
  child Work `p/c` with `depends_on = [1]`, and a Work `q` whose `[actions]` is
  a string and whose `template` is a number.
- **When** the Works are discovered.
- **Then** all three Works are found, `p` has no roots, `c` has no dependencies,
  `q` has no overrides and no template, and there is one error for each of the
  four fields, each at its file.

### **AC-4** A shared id keeps both Works and refuses the lookup

Two Works with one id are both found, one error names both paths, and a lookup
of that id is refused.

#### Two Works with one id

- **Given** Works `a/README.md` and `b/README.md` with the id `k3m9xq` and a
  Work `c/README.md` with the id `p5n2hv`.
- **When** the Works are discovered, and the ids `k3m9xq` and `p5n2hv` are
  looked up.
- **Then** all three Works are found, there is one error at
  `a/README.md, b/README.md` that names the id `k3m9xq`, the lookup of `k3m9xq`
  is refused with that error, and the lookup of `p5n2hv` gives the Work.

### **AC-5** Under nesting a directory holds one Work

A directory with two or more marked files holds no Work, and a marked file
directly in the Works directory is not a Work.

#### Collisions

- **Given** `hierarchy = "nesting"` and Works `a/one.md` and `a/two.md`, a
  marked file `top.md` directly in the Works directory, and a Work
  `b/README.md`.
- **When** the Works are discovered.
- **Then** only `b/README.md` is a Work, one error is at `a/one.md, a/two.md`
  and names the directory, and one error is at `top.md` and says that a Work
  cannot sit directly in the Works directory.

### **AC-6** Under flat there are no collisions

Under `flat`, any number of Works may share a directory and sit directly in the
Works directory.

#### The same files

- **Given** `hierarchy = "flat"` and the files of the previous scenario.
- **When** the Works are discovered.
- **Then** `a/one.md`, `a/two.md`, `top.md` and `b/README.md` are all Works and
  there is no diagnostic.

### **AC-7** The Works directory is judged before it is walked

A missing default directory holds no Works, and any other directory that cannot
be walked is one error and no Work.

#### Each case

- **Given** the default directory missing, a configured directory that is
  missing, one that is a file, one that is a symbolic link, and an empty one.
- **When** the Works are discovered for each.
- **Then** the first and the last find no Work and no diagnostic, and each of
  the others gives one error whose message names the Works directory and whose
  place is the directory as written, and finds no Work.

### **AC-8** A file that is not a Work is explained

For a path that is not a Work, the reason is one of a fixed few, and a Work has
none.

#### The reasons

- **Given** `hierarchy = "nesting"` and paths: one that does not exist, a
  directory, `x.txt`, an `.md` file with no block, one with its block on line 2,
  `+++` front matter without `wio = 1`, a file outside the Works directory, one
  under a directory whose name starts with `.`, a symbolic link, a file in a
  directory with another marked file, a marked file directly in the Works
  directory, and a good Work.
- **When** the reason each is not a Work is asked for.
- **Then** each of the first eleven has its own reason that names what is wrong,
  and the Work has none.

## Additional context

- [Which files are Works](../../../../../docs/concepts.md#which-files-are-works)
  and [Parent and leaf](../../../../../docs/concepts.md#parent-and-leaf) say
  what a Work is and how the hierarchy modes differ.
- The templates discovery builds a `Template` in the same way, and reports and
  does not raise. The difference here is that a Work with a problem of its own
  stays in the tree, so that its children and dependents are not orphaned.
- The hierarchy leaf computes parents and children from the Works found here.
  A dependency on a shared id counts as existing there, so that the one
  duplicate error is the only report.
