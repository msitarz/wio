<!-- wio
id = "mwyc7s"
template = "feature.leaf"
roots = ["wio"]
depends_on = ["xtgz9z", "sz1zsq", "pv47sz"]
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
- Any key of the Work can be carried on request.
- The command writes nothing, so the stage decides where the skeleton goes.

## Non-Goals

- Writing the skeleton to the Work's file, carrying the Work's body, and
  deciding which keys to keep, which the stage and its skill do.
- Printing a skeleton for no Work, which `wio templates show` does.
- Moving or renaming the Work's file.

## Assumptions

- **A-1**: The new leaf is delivered, so the function that sets keys in a block,
  and the discovery, command and catalog it builds on, exist.
- **A-2**: The Work's keys, with their values and tables, are read again from
  its file with `read_metadata_block`, because the `Work` of discovery holds
  only the fields that the other commands use.

## Mechanisms

- A `skeleton` entry in the table of the group, with the argument `template` and
  the options `--work` and `--keep`, the latter repeatable.
- `prepare_skeleton` for the template's skeleton, and the function of the new
  leaf that sets keys in a block, for the Work's `id`, `depends_on` and the kept
  keys.
- The discovery lookup of a Work by id, the catalog's `find` and `is_rejected`,
  `read_metadata_block` for the Work's keys, and `closest_key` for a mistyped
  id.
- `ContractsError` for each refusal, and a note in the diagnostic form for what
  was not carried.
- The names and the signatures above are provisional, for the architecture stage
  to decide.

## Constraints

- **Standard output is the skeleton and nothing else.** Standard error holds
  only the note, and nothing is written to any file.
- **The skeleton is the template's, with the Work's identity.** It has the form
  and the line endings of the template, `template` is the requested template,
  and the `id` and the `depends_on` of the Work are carried exactly. The
  template's defaults supply everything else.
- **`--keep` carries any key the Work has.** A kept key or table replaces the
  template's, and is added when the template has none. `id`, `depends_on`,
  `template` and `wio` cannot be kept, because they are handled already, and a
  key the Work does not have is an error that lists the keys it has.
- **Nothing is dropped silently.** When the Work has keys that the skeleton does
  not carry, standard error has one note, ``note: <the Work's file>: Not carried
  over: `roots`, `actions`. Use `--keep <key>` to carry one.``, naming them in
  the order of the Work and giving no values. With nothing dropped there is no
  note.
- **`--work` is required.** Without it the command is a usage error that points
  to `wio templates show`.
- **A mistake prints nothing.** An id that no Work has names it and the closest
  one, a shared id is refused with the error of discovery, a template that is
  missing or rejected points to `wio templates check` as `new` does, and any
  error of finding the Works refuses the command, as `list` and `show` do. Each
  exits 2 with nothing on standard output.

## Acceptance criteria

### **AC-1** The skeleton keeps the Work's identity and says what it dropped

The skeleton has the Work's `id` and `depends_on` in the template's shape, and
standard error names the keys that were not carried.

#### A leaf moved to the parent template

- **Given** a Work at `.agents/wio/works/w/README.md` with `id = "k3m9xq"`,
  `template = "feature.leaf"`, `roots = ["api"]`, `depends_on = ["a7b2c4"]`, an
  `[actions]` table with `deliver = ["ship"]` and an `[x]` table with
  `ticket = "PAY-1"`, and a template `feature.parent` whose `[contract]` has
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
- **Then** the metadata has `roots = ["api"]` in the place the template had its
  `roots`, and a table `[x]` with `ticket = "PAY-1"` after the plain keys, and
  standard error names only `actions`.

#### Keeping everything

- **Given** the same.
- **When** `--keep roots --keep actions --keep x` is given.
- **Then** standard error is empty.

### **AC-3** The skeleton differs from `templates show` only by the identity

For a Work with nothing but an id, the output is what `wio templates show`
prints with the `id` added first, and the form is the template's.

#### A bare Work and a `+++` Work

- **Given** a Work with only `id = "k3m9xq"`, a Work written in `+++` form with
  `wio = 1` and an `id`, and a template `feature.parent` in comment form.
- **When** `wio contracts skeleton feature.parent --work` runs for each, and
  `wio templates show feature.parent` runs.
- **Then** each skeleton is the output of `templates show` with `id = "k3m9xq"`
  or the other id as the first key, in comment form, with `depends_on` as the
  template has it, and standard error is empty.

### **AC-4** Mistakes print nothing and say what to do

Each mistake is an error on standard error, with nothing on standard output.

#### Each mistake

- **Given** the Work of AC-1, two Works that share the id `a7b2c4`, a template
  that is missing, one that is rejected by `wio templates check`, and a tree
  with an unreadable Work file.
- **When** `wio contracts skeleton feature.parent --work k3m9xr`, `--work
  a7b2c4`, `feature.parent --work k3m9xq --keep nosuch`, `--keep id`, a missing
  template, a rejected template, a call with no `--work`, and a call on the tree
  with the unreadable file each run.
- **Then** each exits 2 with its own message: that no Work has the id `k3m9xr`
  with the closest `k3m9xq`, that the id is shared and names both paths, that
  the Work has no key `nosuch` and lists `roots`, `actions` and `x`, that `id`
  cannot be kept, that the template does not exist or is rejected and points to
  `wio templates check`, that `--work` is required and points to
  `wio templates show`, and the error of finding the Works with the pointer to
  `wio contracts check`, and standard output is empty in each.

### **AC-5** Nothing is written and the output is the same every time

The command changes no file, and two runs print the same bytes.

#### Twice

- **Given** the Work and the template of AC-1 and a hash of each contract.
- **When** the command runs twice, with and without `--keep roots`.
- **Then** the two outputs of each are identical, and the hash of every contract
  is unchanged.

## Additional context

- [From template to contract](../../../../../docs/concepts.md#from-template-to-contract)
  says what `--work` and `--keep` carry, and this leaf lets `--keep` take any
  key the Work has, so that its own data in `[x]` is never lost by a move.
- The define stage uses this command to move a draft to the leaf or parent
  template, and pastes the skeleton over the Work's file.
- The new leaf delivers the function that sets keys in a block, and this leaf
  reuses it.
