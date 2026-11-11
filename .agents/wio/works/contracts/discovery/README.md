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
  either hierarchy mode, by one function that every command calls.
- Each Work is read into one value: its id, title, path, template, roots,
  dependencies and action overrides.
- A problem with one Work is reported once, and no other Work is hidden or
  orphaned by it.
- The reason that a file is not a Work is available for a person who names it.

## Glossary

- **Marked file**: as
  [Which files are Works](../../../../../docs/concepts.md#which-files-are-works)
  defines it.
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
  a block it cannot read or whose marker it does not know: line 1 for a block
  that does not close, the line of the TOML error, and the line of the `wio` key
  for a marker that is not 1, as the templates discovery already relies on.
- **A-3**: `Config.works` carries `dir`, `hierarchy` and `defaults`.

## Mechanisms

- A function in `wio.contracts` that walks the Works directory and returns the
  Works found with the diagnostics, and a lookup of a Work by id on that
  result.
- A function in `wio.contracts` that says why a given path is not a Work.
- `Work` in `wio.models`, the plain type of a Work found, whose `path` is
  relative to the repository root.
- `walk_markdown`, `refuse_directory` and `order_diagnostics` from the shared
  leaf, `read_metadata_block` for the block and `read_outline` for the title.
- The `FileSystem` port, through which every file is read and none is written,
  `Repository` for the repository root, and `Config.works` for the directory and
  the hierarchy mode.
- The names, the signatures and the fields of `Work` are provisional, for the
  architecture stage to decide.

## Constraints

- **Reported, not raised.** A problem with a file or a Work is a diagnostic. The
  Works directory that cannot be walked is one error and no Work is found.
- **A Work is left out only when it cannot be identified.** A file that cannot
  be read or decoded, a block that cannot be read or whose marker is unknown,
  and an `id` that is missing, not a string or empty each give one error and no
  Work.
- **A wrong optional field is empty and reported.** `template` is a string,
  `roots` and `depends_on` are arrays of strings, and `[actions]` is a table
  whose values are a string or an array of strings. A field of another shape,
  one wrong element or entry included, gives one error for the field, the Work
  is built with the whole field empty, and it stays in the tree.
- **The title is the first heading.** It is the text of the first real heading
  of the body at any level, as `read_outline` finds it, and none when the body
  has none.
- **A shared id keeps its Works.** All stay in the tree with one error that
  names all their paths, and a lookup by that id is refused with that error. A
  lookup of an id that no Work has gives none.
- **Nesting collisions are the concepts'.** Under `nesting`, a directory with
  two or more marked files holds no Work, one error names all of them, and a
  marked file directly in the Works directory is not a Work, and each such file
  gets its own error. A marked file whose block cannot be read counts, and its
  own error is reported as well, while a file that cannot be read or decoded is
  not known to be marked and does not count. Under `flat` neither rule applies.
- **A hidden directory is one below the Works directory.** The walk skips a
  directory whose name starts with `.` below the Works directory, and the Works
  directory itself may start with one.
- **Every place is a path.** A diagnostic's place is the file's path relative to
  the repository root, written with `/`, followed by `:<line>` for a block that
  cannot be read and by nothing for every other problem, and the paths of a
  shared id are joined by a comma and a space.
- **Read, never written.** Every file is read through `FileSystem`, and no file
  is written.
- **The output is deterministic.** The Works are sorted by the string of their
  paths, and the diagnostics are ordered as `order_diagnostics` orders them.

## Acceptance criteria

In these scenarios `[works] dir` is `works`, so a file written `a/README.md` is
at `works/a/README.md`, and the places and paths are written that way.

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
  and a body with `## Only` and no `#` heading, `d/README.md` with the id
  `p5n2hv` and a body with no heading at all, `a/notes.md` with no block,
  `c/x.md` with a block on its second line, a hidden directory `.git` holding a
  marked file, and a symbolic link to a marked file.
- **When** the Works are discovered.
- **Then** there are three Works, `a/README.md`, `b/spec.md` and `d/README.md`,
  with those ids and `First`, `Only` and no title, the first with its template,
  roots, dependencies and both overrides as written, the others with no
  template, no roots, no dependencies and no overrides, there is no diagnostic,
  and no file has been written.

### **AC-2** A Work that cannot be identified is left out with one error

A file that cannot be read or decoded, a block that cannot be read, a marker of
an unknown version, and a missing, non-string or empty id each give one error
and no Work, while the other Works are found.

#### Seven broken files and a good one

- **Given** `hierarchy = "flat"` and, under the Works directory, `bad/utf.md`
  that is not UTF-8, `bad/open.md` whose comment block does not close,
  `bad/toml.md` whose comment block has invalid TOML on its line 3,
  `bad/marker.md` whose `+++` front matter has `wio = 2` on its line 2,
  `bad/noid.md` whose block has no `id`, `bad/empty.md` with `id = ""`,
  `bad/number.md` with `id = 12`, and a good Work `good/README.md`.
- **When** the Works are discovered.
- **Then** the good Work is found, and there is one error for each of the seven
  files and no other diagnostic. Their places are `works/bad/utf.md`,
  `works/bad/open.md:1`, `works/bad/toml.md:3`, `works/bad/marker.md:2`,
  `works/bad/noid.md`, `works/bad/empty.md` and `works/bad/number.md`.

### **AC-3** A wrong optional field is reported and the Work stays

An optional key of the wrong type is an error, the Work is built with that field
empty, and the Work keeps its place in the tree.

#### Wrong fields

- **Given** `hierarchy = "nesting"`, a Work `p` with `roots = "api"` that has a
  child Work `p/c` with `depends_on = [1]`, and a Work `q` whose `[actions]` is
  a string and whose `template` is a number, a Work `r` with `roots = ["a", 1]`,
  and a Work `s` with an `[actions]` table with `define = 5`.
- **When** the Works are discovered.
- **Then** all five Works are found, `p` has no roots, `c` has no dependencies,
  `q` has no overrides and no template, `r` has no roots, `s` has no overrides,
  and there is one error for each of the six fields, each at its file.

### **AC-4** A shared id keeps both Works and refuses the lookup

Two Works with one id are both found, one error names both paths, and a lookup
of that id is refused.

#### Two Works with one id

- **Given** Works `a/README.md` and `b/README.md` with the id `k3m9xq` and a
  Work `c/README.md` with the id `p5n2hv`.
- **When** the Works are discovered, and the ids `k3m9xq` and `p5n2hv` are
  looked up.
- **Then** all three Works are found, there is one error at
  `works/a/README.md, works/b/README.md` that names the id `k3m9xq`, the lookup
  of `k3m9xq` is refused with that error, the lookup of `p5n2hv` gives the Work,
  and the lookup of `zzzzzz` gives none.

### **AC-5** Under nesting a directory holds one Work

A directory with two or more marked files holds no Work, a marked file that is
left out still counts, and a marked file directly in the Works directory is not
a Work.

#### Collisions

- **Given** `hierarchy = "nesting"` and Works `a/one.md` with the id `k3m9xq`
  and `a/two.md` with the id `a7b2c4`, a marked file `top.md` with the id
  `p5n2hv` directly in the Works directory, and a Work `b/README.md` with the id
  `s5t3wx`.
- **When** the Works are discovered.
- **Then** only `b/README.md` is a Work, one error is at
  `works/a/one.md, works/a/two.md` and names the directory, and one error is at
  `works/top.md` and says that a Work cannot sit directly in the Works
  directory.

#### A marked file that is left out

- **Given** `hierarchy = "nesting"` and `a/one.md` with the id `k3m9xq` and
  `a/two.md` whose block has no `id`.
- **When** the Works are discovered.
- **Then** there is no Work, one error is at `works/a/one.md, works/a/two.md`
  for the collision, and one error is at `works/a/two.md` for the missing id.

### **AC-6** Under flat there are no collisions

Under `flat`, any number of Works may share a directory and sit directly in the
Works directory.

#### The same files

- **Given** `hierarchy = "flat"` and the files of the first scenario of AC-5.
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
  the others gives one error whose message begins `The Works directory` and
  whose place is the directory as written, and finds no Work.

### **AC-8** A file that is not a Work is explained

For a path that is not a Work, the reason is the first of a fixed list that
applies, each reason names what it is about, and a Work has none. The list, in
order, is: the path does not exist or is not a file, its name does not end in
`.md`, the path is or runs through a symbolic link, the path is outside the
Works directory, it is under a hidden directory below the Works directory, there
is no block or it does not start on the first line, the `+++` front matter has
no `wio` key, the file is in a directory with another marked file, the file is
directly in the Works directory, and the file is left out for an error of its
own.

#### The reasons

- **Given** `hierarchy = "nesting"` and paths: one that does not exist, a
  directory, `x.txt`, a symbolic link, a path that runs through a symbolic link,
  a file outside the Works directory, one under a directory below the Works
  directory whose name starts with `.`, an `.md` file with no block, one with
  its block on line 2, `+++` front matter without a `wio` key, a file in a
  directory with another marked file, a marked file directly in the Works
  directory, a marked file whose block does not close, and a good Work.
- **When** the reason each is not a Work is asked for.
- **Then** each of the first thirteen has a reason, the thirteen are different
  from one another, each names its subject, which is the other files for the
  collision, the Works directory for the one directly in it, and the error that
  discovery reports for the last, and the Work has none.

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
