<!-- wio
id = "mb4q2g"
template = "feature.leaf"
roots = ["wio"]
depends_on = ["xtgz9z", "ces6tf", "sz1zsq"]
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

- **Resolved actions of a Work**: the actions of its template, or of the
  config's defaults when it names none, with each action the Work's own
  `[actions]` names replacing that action, and an empty list removing it.

## Non-Goals

- The body of a contract, its sections and items, which the check-body leaf adds
  to the same command.
- The template itself and the config, which `wio templates check` and
  `wio config check` judge.
- Comparing a template's `shape` with the tree. It is a free descriptive string,
  and what it means is the workflow's.
- Looking up a removed dependency in the history.
- Checking the form of an id beyond what a record needs.

## Assumptions

- **A-1**: The discovery, hierarchy and command leaves are delivered, so the
  Works, the diagnostics of finding them and of the graph, the group and the
  catalog exist. A wrong type of an optional key is already an error of
  discovery.
- **A-2**: `Config` carries the declared actions, stage presets, stages and
  roots and `[works.defaults.actions]`.
- **A-3**: A template's `[actions]` can be read from its file, at the path that
  the catalog gives, with the block reader.

## Mechanisms

- A function in `wio.contracts` that runs discovery and the hierarchy and then
  the checks of this leaf, one function for each concern, and returns every
  diagnostic.
- `closest_key` from the shared leaf, for the suggestion of a key.
- The catalog port, whose `find` and `is_rejected` judge a template.
- The `check` entry of the group's table, which renders with `render_check` and
  `has_error` and sets the exit code, and takes `--json`.
- `Config` for the declared names, and `FileSystem` to read a template's
  actions.
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
- **The place is the file.** Each diagnostic of this leaf names the Work's file
  as its place, without a line.
- **Only an error fails.** An error exits 1, and a warning or a note never does.
- **The output is deterministic.** It is ordered as `order_diagnostics` orders
  it, says `The contracts pass.` when there is nothing to report, and with
  `--json` is one array that parses.
- **Nothing is written.** The command reads and reports.

## Acceptance criteria

### **AC-1** `check` reports every problem at once and exits by severity

One run reports what finding the Works, the graph and the metadata give, in a
fixed order, and exits 1 only when there is an error.

#### Problems of three kinds

- **Given** a tree with two Works that share an id, two Works that list each
  other, a Work with the unknown key `depend_on`, and a Work that names a
  template that does not exist.
- **When** `wio contracts check` runs, and then `wio contracts check --json`.
- **Then** both report the shared id, the cycle, the key and the template, in
  the same order, the second as one JSON array that parses, and each exits 1.

#### A clean tree and a warning

- **Given** a tree with no problem, and a tree whose only problem is a warning.
- **When** `wio contracts check` runs on each.
- **Then** the first prints `The contracts pass.` and the second prints the
  warning, and each exits 0.

### **AC-2** A mistyped key is told by its closest known key

An unknown key of the metadata, or an unknown table, is a warning that names the
closest known key when there is one.

#### Unknown keys

- **Given** Works with the keys `depend_on`, `zzz` and `[xx]`, and Works with
  the keys `wio`, `x`, `[x]` and `tracks`.
- **When** `wio contracts check` runs.
- **Then** the first three give ``Unknown key `depend_on` in the metadata. Did
  you mean `depends_on`?``, ``Unknown key `zzz` in the metadata`` and the same
  for `xx`, each a warning at the Work's file, and the second group gives
  nothing.

### **AC-3** An id that would break a record is an error

An id that holds whitespace or a comma, or is `none`, is an error, and any other
non-empty id is not.

#### Ids

- **Given** Works with the ids `a b`, `a,b`, `none`, `SPEC-012` and `k3m9xq`.
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

- **Given** Works that name `nosuch`, which no file has, `bad`, whose file has
  an unknown key, and `unclosed`, whose block does not close, and a Work that
  names no template.
- **When** `wio contracts check` runs.
- **Then** the first gives ``The template `nosuch` does not exist``, the second
  and the third give ``The template `bad` is rejected by `wio templates check`;
  run it for the findings`` and the same for `unclosed`, the last gives nothing,
  and no Work with a template error is also told that it has no action.

### **AC-5** The actions a Work names exist, and it has some

The names in a Work's own `[actions]` are declared in the config, no stage
repeats in a pipeline, and the resolved actions are not empty.

#### Names

- **Given** a config that declares the action `deliver`, the stage preset
  `integrate` and the stage `implementation`, and Works whose `[actions]` hold
  `shipp = ["implementation"]`, `deliver = "nosuch"`,
  `deliver = ["implementation", "implementation"]`, `deliver = ["gone"]` and
  `deliver = []`.
- **When** `wio contracts check` runs.
- **Then** the first four are errors,
  ``The action `shipp` is not declared in `[actions]` of the config``,
  ``The stage preset `nosuch` of action `deliver` is not declared``,
  ``The stage `implementation` appears twice in action `deliver```, and ``The
  stage `gone` of action `deliver` is not declared``, and the last is not an
  error.

#### No action at all

- **Given** a Work without a template, in a project without default actions and
  with no `[actions]`, a Work whose template has the one action `deliver` and
  whose `[actions]` is `deliver = []`, and a Work that names no template in a
  project whose defaults have `deliver`.
- **When** `wio contracts check` runs.
- **Then** the first two give ``The Work resolves to no action`` as an error,
  and the third gives nothing.

### **AC-6** The roots a Work names exist

A root that the config does not declare is an error, `@descendants` is allowed,
a leaf that lists it is a warning, and a parent that leaves out a root of a
descendant is a note.

#### Roots

- **Given** a config with the roots `api` and `web`, a Work with
  `roots = ["nosuch"]`, a leaf with `roots = ["api", "@descendants"]`, and a
  parent with `roots = ["web"]` whose child has `roots = ["api"]`.
- **When** `wio contracts check` runs.
- **Then** the first gives
  ``The root `nosuch` is not declared in `[roots]` of the config`` as an error,
  the second gives ``The Work has no children, so `@descendants` adds no root``
  as a warning, the third gives
  ``Its roots leave out `api`, which a descendant uses`` as a note, and the
  command exits 1 for the first only.

## Additional context

- [Invariants wio checks](../../../../../docs/concepts.md#invariants-wio-checks)
  lists what the command verifies, and this leaf covers the part that is about
  the Works' metadata and the graph.
- The check-body leaf adds its checks to the same command and its `--json`, so
  it is delivered after this one.
- An id that holds a comma or whitespace cannot be listed in `Wio-Work` and
  `none` means no Work, which is why the form of an id is checked here.
