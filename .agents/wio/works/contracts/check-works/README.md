<!-- wio
id = "mb4q2g"
template = "feature.leaf"
roots = ["wio"]
depends_on = ["xtgz9z", "ces6tf", "sz1zsq", "h69nf8"]
-->

# Checking the Works

## Purpose

A person or an agent that edits a contract needs to be told what is wrong with
the Works, all at once and in one run, so that a problem found while finding the
Works, in the graph or in the metadata of a Work is not hidden by another.

## Goals

- `wio contracts check` reports every problem of finding the Works, of the
  dependency graph and of the Works' metadata in one run, as text or as JSON.
- A mistyped metadata key is told by its closest known key.
- A template, action, stage preset, stage or root that a Work names and that
  does not exist is named.
- An id that would break a record is refused.

## Glossary

- **Resolved actions of a Work**: its actions after its own `[actions]` replace
  those of its template, or of the config's defaults when it names none, as
  [Where the pipeline comes from](../../../../../docs/concepts.md#where-the-pipeline-comes-from)
  says, an empty list removing the action.

## Non-Goals

- The body of a contract, its sections and items, which the check-body leaf adds
  to the same command.
- The template itself and the config, which `wio templates check` and
  `wio config check` judge.
- Comparing a template's `shape` with the tree. By the driver's decision it is a
  free descriptive string, so the warning that `docs/concepts.md` and
  `docs/v0.1-scope.md` describe is dropped, and those documents change when they
  are promoted.
- Looking up a removed dependency in the history.
- A repeated stage in a pipeline that a Work inherits from its template, in a
  stage preset or in a config default, which `wio templates check` and
  `wio config check` judge.
- A form of an id beyond what a record needs. That rule is new here, and the
  concepts do not list it among the invariants.

## Assumptions

- **A-1**: The discovery, hierarchy and command leaves are delivered, so the
  Works, the diagnostics of finding them and of the graph, the group and the
  catalog exist. A wrong type of an optional key is already an error of
  discovery.
- **A-2**: `Config` carries the declared actions, stage presets, stages and
  roots and `[works.defaults.actions]`.
- **A-3**: A template's `[actions]` can be read from its file, at the path that
  the catalog gives, which is relative to the repository root, with the block
  reader.
- **A-4**: The unknown-key check reads each Work's block again with
  `read_metadata_block`, because the `Work` of discovery holds only some of its
  keys. A file that cannot be read the second time is one error at the file.

## Mechanisms

- A function in `wio.contracts` that runs discovery and the hierarchy and then
  the checks of this leaf, one function for each concern, and returns every
  diagnostic.
- `closest_key`, `render_check`, `has_error` and `order_diagnostics` from the
  shared leaf.
- The catalog port, whose `find` and `is_rejected` judge a template.
- The function that resolves a Work's actions, which the show leaf reuses.
- The `check` entry of the group's table, which renders with `render_check` and
  `has_error` and sets the exit code, and takes `--json`.
- `Config` for the declared names, `FileSystem` to read a template's actions,
  and `Repository` for the repository root.
- The names and the signatures above are provisional, for the architecture stage
  to decide.

## Constraints

- **Every concern is checked for every Work.** A problem found in one Work or
  one check does not stop another, and a Work with an error still gets the rest.
- **A finding is reported once.** What discovery and the hierarchy report is
  carried through and not found again, and a check that depends on something
  already reported is skipped: the resolved actions of a Work whose template is
  missing or rejected, and the roots of a Work whose `roots` was of the wrong
  type.
- **The known keys are these.** They are `id`, `template`, `roots`, `depends_on`
  and `actions`. The table `[x]` and the key `tracks` are exempt and never
  suggested, a plain key `x` is unknown, and the `wio` marker is not a key,
  because the block reader takes it out.
- **A note is one for each omitted root.** A parent whose roots leave out roots
  that its descendants use gets one note for each.
- **The place is the file.** Each diagnostic of this leaf names the Work's file
  as its place, without a line.
- **Only an error fails.** An error exits 1, and a warning or a note never does.
- **The output is `order_diagnostics`' order.** It says `The contracts pass.`
  when there is nothing to report.
- **An action entry has a shape.** A value of a Work's `[actions]` is a stage
  preset, written as a string, or a list of stages, and any other value is an
  error, ``The action `deliver` must be a stage preset or a list of stages``.

## Acceptance criteria

### **AC-1** `check` reports every problem at once and exits by severity

One run reports what finding the Works, the graph and the metadata give, in a
fixed order, and exits 1 only when there is an error.

#### Problems of three kinds

- **Given** a project whose defaults have the action `deliver`, and a tree with
  two Works that share an id, two Works that list each other, a Work with the
  unknown key `depend_on`, and a Work that names a template that does not
  exist.
- **When** `wio contracts check` runs, and then `wio contracts check --json`.
- **Then** both report the shared id, the cycle, the key and the template, in
  the order of `order_diagnostics`, the second as one JSON array that parses,
  and each exits 1.

#### A clean tree and a warning

- **Given** a tree with no problem, and a tree whose only problem is a warning.
- **When** `wio contracts check` runs on each.
- **Then** the first prints `The contracts pass.` and the second prints the
  warning, and each exits 0.

### **AC-2** A mistyped key is told by its closest known key

An unknown key of the metadata, or an unknown table, is a warning that names the
closest known key when there is one.

#### Unknown keys

- **Given** a project whose defaults have the action `deliver`, Works with the
  keys `depend_on`, `zzz`, a plain `x = 1` and the table `[xx]`, and Works with
  the table `[x]` and the key `tracks`.
- **When** `wio contracts check` runs.
- **Then** the first four give ``Unknown key `depend_on` in the metadata. Did
  you mean `depends_on`?`` and ``Unknown key `zzz` in the metadata``, and the
  same, without a suggestion, for `x` and `xx`, each a warning at the Work's
  file, and the second group gives nothing.

### **AC-3** An id that would break a record is an error

An id that holds whitespace or a comma, or is `none`, is an error, and any other
non-empty id is not.

#### Ids

- **Given** a project whose defaults have the action `deliver`, and five Works
  in separate directories with the ids `a b`, `a,b`, `none`, `SPEC-012` and
  `k3m9xq`.
- **When** `wio contracts check` runs.
- **Then** the first two report ``The id `a b` holds whitespace or a comma`` and
  ``The id `a,b` holds whitespace or a comma``, the third reports
  ``The id `none` is reserved for commits that belong to no Work``, and the last
  two give nothing.

### **AC-4** A missing and a rejected template are told apart

A Work whose template does not exist and one whose template
`wio templates check` rejects are each an error that names the template, and the
second points to that command.

#### Missing, rejected and none

- **Given** a project whose defaults have the action `deliver`, and Works that
  name `nosuch`, which no file has, `bad`, whose file has an unknown key, and
  `unclosed`, whose block does not close, and a Work that names no template.
- **When** `wio contracts check` runs.
- **Then** the first gives ``The template `nosuch` does not exist``, the second
  and the third give ``The template `bad` is rejected by `wio templates check`;
  run it for the findings`` and the same for `unclosed`, the last gives nothing,
  and no Work with a template error is also told that it has no action.

### **AC-5** The actions a Work names exist, and it has some

The names in a Work's own `[actions]` are declared in the config, no stage
repeats in a pipeline, and the resolved actions are not empty.

#### Names

- **Given** a config that declares the actions `deliver` and `amend`, the stage
  preset `integrate`, the stage `implementation` and the kind of `t.leaf`, a
  template `t.leaf` whose actions are `deliver = ["implementation"]` and
  `amend = ["implementation"]`, and Works that follow it whose `[actions]` hold
  `shipp = ["implementation"]`, `deliver = "nosuch"`,
  `deliver = ["implementation", "implementation"]`, `deliver = ["gone"]`,
  `deliver = 5` and `deliver = []`.
- **When** `wio contracts check` runs.
- **Then** the first five are errors,
  ``The action `shipp` is not declared in `[actions]` of the config``,
  ``The stage preset `nosuch` of action `deliver` is not declared``,
  `` The stage `implementation` appears twice in action `deliver` ``, and
  ``The stage `gone` of action `deliver` is not declared``,
  ``The action `deliver` must be a stage preset or a list of stages``, and the
  last is not an error, because `amend` remains.

#### No action at all

- **Given** three projects: one with no default actions, in which a Work names
  no template and has no `[actions]`; one in which a Work follows a template
  whose only action is `deliver` and has `deliver = []`; and one whose defaults
  have `deliver`, in which a Work names no template and has no `[actions]`.
- **When** `wio contracts check` runs in each.
- **Then** the first two give ``The Work resolves to no action`` as an error,
  and the third gives nothing.

### **AC-6** The roots a Work names exist

A root that the config does not declare is an error, `@descendants` is allowed,
a leaf that lists it is a warning, and a parent that leaves out roots of its
descendants gets a note for each.

#### Roots

- **Given** `hierarchy = "nesting"`, a project whose defaults have the action
  `deliver`, a config with the roots `api`, `web` and `db`, a Work `a` with
  `roots = ["nosuch"]`, a leaf `b` with `roots = ["api", "@descendants"]`, and a
  parent `c` with `roots = ["web"]` whose children `c/x` and `c/y` have
  `roots = ["api"]` and `roots = ["db"]`.
- **When** `wio contracts check` runs.
- **Then** the first gives
  ``The root `nosuch` is not declared in `[roots]` of the config`` as an error,
  the second gives ``The Work has no children, so `@descendants` adds no root``
  as a warning, the third gives two notes,
  ``Its roots leave out `api`, which a descendant uses`` and the same for `db`,
  and the command exits 1 because of the first.

### **AC-7** Every concern is checked for every Work, once

A Work with several problems gets every finding, and a check that depends on a
finding already reported is skipped.

#### Several problems at once

- **Given** a project whose defaults have the action `deliver`, a Work with an
  unknown key, an undeclared root and an `[actions]` with an undeclared action,
  and a Work with `roots = "api"`.
- **When** `wio contracts check` runs.
- **Then** the first Work gets a warning for the key and an error for the root
  and one for the action, each at its file, and the second gets the error of
  discovery for its `roots` and no finding about its roots.

## Additional context

- [Invariants wio checks](../../../../../docs/concepts.md#invariants-wio-checks)
  lists what the command verifies, and this leaf covers the part that is about
  the Works' metadata and the graph.
- The check-body leaf adds its checks to the same command and its `--json`, so
  it is delivered after this one.
- An id that holds a comma or whitespace cannot be listed in `Wio-Work` and
  `none` means no Work, which is why the form of an id is checked here.
