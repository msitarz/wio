<!-- wio
id = "mwyc7s"
template = "feature.leaf"
roots = ["wio"]
depends_on = ["xtgz9z", "sz1zsq", "pv47sz", "h69nf8"]
-->

# The skeleton of an existing Work

## Purpose

A stage that moves a Work to another template must keep the Work's id and
dependencies, so that the Work keeps its records and its place in the order, and
must be told what the move did not carry, so that nothing is dropped silently.
Only `wio contracts` can read a Work, so it is the command that prepares the
skeleton for one.

## Goals

- A stage can print the skeleton of any template for an existing Work, with the
  Work's `id` and `depends_on`.
- A person or an agent is told which of the Work's keys the skeleton did not
  carry.
- Any other key of the Work can be carried on request.
- The command writes nothing, so the stage decides where the skeleton goes.

## Non-Goals

- Writing the skeleton to the Work's file, carrying the Work's body, and
  deciding which keys to keep, which the stage and its skill do.
- Printing a skeleton for no Work, which `wio templates show` does.
- Moving or renaming the Work's file.

## Assumptions

- **A-1**: The new leaf is delivered, so the function that sets keys in a block,
  and the discovery, command and catalog it builds on, exist, and the shared
  leaf's `closest_key` with them.
- **A-2**: The Work's keys, with their values and tables, are read again from
  its file with `read_metadata_block`, because the `Work` of discovery holds
  only the fields that the other commands use. That `depends_on` is carried as
  the file has it, a wrong type included.

## Mechanisms

- A `skeleton` entry in the table of the group, with the argument `template` and
  the options `--work` and `--keep`, the latter repeatable.
- `prepare_skeleton` for the template's skeleton, and the function of the new
  leaf that sets keys in a block, for the Work's `id`, `depends_on` and the kept
  keys.
- The discovery lookup of a Work by id, the catalog's `find` and `is_rejected`,
  `read_metadata_block` for the Work's keys, `closest_key` for a mistyped id,
  and the `FileSystem` port to read the template's text at the catalog's path
  and the Work's file.
- `ContractsError` for each refusal, and a note in the diagnostic form for what
  was not carried.
- The names and the signatures above are provisional, for the architecture stage
  to decide.

## Constraints

- **Standard output is the skeleton and nothing else.** Standard error holds
  only the note, and nothing is written to any file.
- **The skeleton is the template's, with the Work's identity.** It has the form
  and the line endings of the template, `template` is the requested template,
  and the `id` of the Work and its `depends_on` are carried exactly: a Work with
  no `depends_on` leaves the template's as the template has it, and a Work with
  `depends_on = []` gives `depends_on = []`. The template's defaults supply
  everything else.
- **`--keep` carries any key the Work has.** A kept key or table replaces the
  template's in its place, and is added when the template has none, a plain key
  after the last plain key and a table after the last table, or after the plain
  keys when there is none, as the setter of the new leaf does, tables in the
  order of the Work. An inline table counts as a plain key. `id`, `depends_on`,
  `template` and `wio` cannot be kept, because they are handled already, and
  that check comes before the one for a key the Work does not have, which is an
  error that lists the keys that can be kept, in the order of the Work.
- **Nothing is dropped silently.** When the Work has keys that the skeleton does
  not carry, standard error has one note, ``note: <the Work's file>: Not carried
  over: `roots`, `actions`. Use `--keep <key>` to carry one.``, the file being
  relative to the repository root and written with `/`, naming them in
  the order of the Work and giving no values. With nothing dropped there is no
  note.
- **`--work` is required.** Without it the command is a usage error that points
  to `wio templates show`.
- **A mistake prints nothing.** An id that no Work has names it and the closest
  one, and a template that no file has points to `wio templates list`, and one
  that is rejected points to `wio templates check`. A shared id refuses a lookup
  of that id with the error of discovery, and any other error of finding the
  Works, a Work left out, a nesting collision or a directory that cannot be
  walked, refuses every call. A wrong type of an optional field, such as a
  `depends_on` that is a string, does not refuse, and the field is carried as
  the file has it. A refusal of the whole tree carries the pointer to
  `wio contracts check`, as `list` and `show` do. When several apply, the first
  of these is reported: a usage error, an incomplete tree, the Work, the
  template, then `--keep`. Each exits 2 with nothing on standard output.

## Acceptance criteria

### **AC-1** The skeleton keeps the Work's identity and says what it dropped

The skeleton has the Work's `id` and `depends_on` in the template's shape, and
standard error names the keys that were not carried.

#### A leaf moved to the parent template

- **Given** a Work at `.agents/wio/works/w/README.md` with `id = "k3m9xq"`,
  `template = "feature.leaf"`, `roots = ["api"]`, `depends_on = ["a7b2c4"]`, an
  `[actions]` table with `deliver = ["ship"]` and an `[x]` table with
  `ticket = "PAY-1"`, a config that declares the kind `feature`, and a template
  `feature.parent` of that kind whose `[contract]` has
  `roots = ["@descendants"]` and `depends_on = []` and whose body is
  `# <Work name>` and `## Purpose`.
- **When** `wio contracts skeleton feature.parent --work k3m9xq` runs.
- **Then** standard output is exactly the text below, standard error is the line
  below it, nothing is written, and it exits 0:

  ```text
  <!-- wio
  id = "k3m9xq"
  template = "feature.parent"
  roots = ["@descendants"]
  depends_on = ["a7b2c4"]
  -->

  # <Work name>

  ## Purpose
  ```

  ```text
  note: .agents/wio/works/w/README.md: Not carried over: `roots`, `actions`,
  `x`. Use `--keep <key>` to carry one.
  ```

  The note is one line, shown here over two.

### **AC-2** `--keep` carries any key the Work has

A kept key replaces the template's, and the note names only what is still
dropped.

#### Keeping roots and a table

- **Given** the Work and the template of AC-1.
- **When** `wio contracts skeleton feature.parent --work k3m9xq --keep roots
  --keep x` runs.
- **Then** standard output is exactly the text below, and standard error names
  only `actions`:

  ```text
  <!-- wio
  id = "k3m9xq"
  template = "feature.parent"
  roots = ["api"]
  depends_on = ["a7b2c4"]

  [x]
  ticket = "PAY-1"
  -->

  # <Work name>

  ## Purpose
  ```

#### Keeping everything

- **Given** the same.
- **When** `--keep roots --keep actions --keep x` is given.
- **Then** standard output is exactly the text below, and standard error is
  empty:

  ```text
  <!-- wio
  id = "k3m9xq"
  template = "feature.parent"
  roots = ["api"]
  depends_on = ["a7b2c4"]

  [actions]
  deliver = ["ship"]

  [x]
  ticket = "PAY-1"
  -->

  # <Work name>

  ## Purpose
  ```

#### A template with a table of its own

- **Given** the Work of AC-1 and a template `t.tabled` of the kind `feature`
  whose `[contract]` has `[x]` with `ticket = ""`.
- **When** `wio contracts skeleton t.tabled --work k3m9xq --keep actions` runs.
- **Then** standard output is exactly the text below, and standard error names
  `roots` and `x`:

  ```text
  <!-- wio
  id = "k3m9xq"
  template = "t.tabled"
  roots = []
  depends_on = ["a7b2c4"]

  [x]
  ticket = ""

  [actions]
  deliver = ["ship"]
  -->

  # <Work name>

  ## Purpose
  ```

  where `t.tabled` has `roots = []` and the same body as `feature.parent`.

### **AC-3** The skeleton differs from `templates show` only by the identity

For a Work with nothing but an id, the output is what `wio templates show`
prints with the `id` added first, and the form is the template's.

#### A bare Work and a `+++` Work

- **Given** a Work `k3m9xq` with only that id, a Work `p5n2hv` written in `+++`
  form with `wio = 1` and that id, and a template `feature.parent` in comment
  form.
- **When** `wio contracts skeleton feature.parent --work k3m9xq`,
  `wio contracts skeleton feature.parent --work p5n2hv` and
  `wio templates show feature.parent` run.
- **Then** each skeleton is the output of `templates show` with
  `id = "k3m9xq"` or `id = "p5n2hv"` as the first key, in comment form, with
  `depends_on` as the template has it, and standard error is empty.

#### A template in front matter or with CRLF

- **Given** the Work of AC-1 and templates of the kind `feature`: `t.front` in
  `+++` form with `wio = 1`, and `t.crlf` written with CRLF line endings.
- **When** `wio contracts skeleton t.front --work k3m9xq` and
  `wio contracts skeleton t.crlf --work k3m9xq --keep x` run.
- **Then** the first is in `+++` form with `wio = 1`, `id` and `template` in
  that order, and the second has CRLF endings throughout, including the kept
  table.

### **AC-4** Mistakes print nothing and say what to do

Each mistake is an error on standard error, with nothing on standard output, and
a shared id refuses only its own lookup.

#### Each mistake

- **Given** the Work of AC-1, two Works that share the id `a7b2c4`, a template
  `feature.parent`, a template `bad` that is rejected by `wio templates check`,
  and no template `nosuch`.
- **When** the command runs with `feature.parent --work k3m9xr`,
  `feature.parent --work a7b2c4`, `feature.parent --work k3m9xq --keep nosuch`,
  `--keep id`, `--keep template`, `--keep depends_on` and `--keep wio` in turn,
  `nosuch --work k3m9xq`, `bad --work k3m9xq`, and `feature.parent` alone.
- **Then** each exits 2 with its own message and nothing on standard output:
  that no Work has the id `k3m9xr` with the closest `k3m9xq`, that the id is
  shared and names both paths, that the Work has no key `nosuch` and that
  `roots`, `actions` and `x` can be kept, that each of `id`, `template`,
  `depends_on` and `wio` cannot be kept, that the template `nosuch` does not
  exist and points to `wio templates list`, that `bad` is rejected and points to
  `wio templates check`, and that `--work` is required and points to
  `wio templates show`.

#### A tree that is not complete

- **Given** a tree with an unreadable Work file besides the Work of AC-1.
- **When** `wio contracts skeleton feature.parent --work k3m9xq` runs.
- **Then** it exits 2 with the error of finding the Works and the pointer to
  `wio contracts check`, and nothing on standard output.

#### A wrong type that does not refuse

- **Given** a Work `k3m9xq` whose `depends_on` is the string `"a7b2c4"` and the
  template of AC-1.
- **When** `wio contracts skeleton feature.parent --work k3m9xq` runs.
- **Then** it prints the skeleton with `depends_on = "a7b2c4"` as the file has
  it, and exits 0.

#### Several mistakes at once

- **Given** the same tree, and a template `bad` that is rejected.
- **When** `wio contracts skeleton bad` runs, and then
  `wio contracts skeleton bad --work k3m9xr --keep nosuch`.
- **Then** the first reports only that `--work` is required, and the second only
  the error of finding the Works, because a usage error and an incomplete tree
  come before the Work, the template and `--keep`.

### **AC-5** Nothing is written and the output is the same every time

The command changes no file, and two runs print the same bytes.

#### Twice

- **Given** the Work and the template of AC-1 and a hash of each contract.
- **When** the command runs twice, with and without `--keep roots`.
- **Then** the two outputs of each are identical, and the hash of every contract
  is unchanged.

## Additional context

- [From template to contract](../../../../../docs/concepts.md#from-template-to-contract)
  says what `--work` and `--keep` carry. This leaf extends it: `--keep` takes
  any key the Work has, so that its own data in `[x]` is never lost by a move.
- The define stage uses this command to move a draft to the leaf or parent
  template, and writes the Work's contract in the shape it prints.
- The new leaf delivers the function that sets keys in a block, and this leaf
  reuses it.
