<!-- wio
id = "5qgs79"
template = "feature.leaf"
roots = ["wio"]
depends_on = ["cm25z9"]
-->

# Errors of rules and rulesets

## Purpose

A reference that names nothing in its ruleset, a cycle of rule presets and a
root-independent ruleset that a root reaches are faults that only the rule files
and the config show together, and no command reports them.

## Goals

- Every error that `wio rules check` owns is found and placed: the errors of the
  discovery, and the errors of the references of the config and of the
  manifests.
- Each fault is reported once, at the key where it is written, whatever the
  number of entries that reach it.
- The key paths that name a place in the config and the finding of cycles are
  written and done by functions that `wio config check` shares.

## Non-Goals

- The warnings, which `785y9k` builds, and the report that joins them, which the
  parent builds.
- Judging the form of a reference in the config or that a ruleset of the config
  exists, which `wio config check` does.
- Expanding a rule preset, which `cyeth5` does.

## Assumptions

### A-1

The config is valid, as A-1 of [wio rules](../../README.md) says, so every
reference in it is well-formed and names a ruleset or a rule preset of the
config; what needs the rule files is whether the item after the dot exists.

### A-2

An entry is judged where it is written and by itself, so a fault found inside a
rule preset that the entry reaches is not the entry's and is reported at the
preset's own key.

## Mechanisms

The names of the functions below are provisional.

- **`check_errors(config, discovery) -> tuple[Diagnostic, ...]`** — in
  `wio.rules`, with the `Config` and the `Discovery` of `8zn10d`, built from the
  errors of the discovery and the problems that `expand` of `cyeth5` returns for
  each entry; it does no input or output.
- **The key paths and the cycles** — `join_path` and `item_path`, moved from
  `wio.config.messages`, and `find_cycles`, moved from `wio.config.pipelines`,
  to `wio.formats`, which `wio.config` and `wio.rules` both import.
- **The reach of the roots** — `reach` of `apply_layers` of `cm25z9`, for the
  roots whose rule presets reach a root-independent ruleset.

## Acceptance criteria

### **AC-1** The errors of the discovery are shown

Every error of the discovery is returned as it is, and its warnings are not.

#### Pass-through

- **Given** a discovery with a rule whose block does not close, a manifest that
  does not parse and an unknown key in a rule's block.
- **When** `check_errors` runs.
- **Then** it returns the two errors with their places and messages unchanged,
  and not the warning.

### **AC-2** A reference of the config that names nothing is an error

An entry of the config whose family, code or rule preset after the dot is not in
its ruleset is one error at the entry's key path, and an entry that names
something is not.

#### Every field of the config

- **Given** a ruleset `demo` that declares `ARC` and holds `ARC001` and a preset
  `recommended`, and entries that name `demo.ZZZ`, `demo.ARC999` and `demo.none`
  in `roots.api.rule_presets`, in `stages.s.rules_include`, in
  `stages.s.rules_exclude`, in `rule_presets.backend.rules_include`, in
  `rules_always_include` and, for `demo.ZZZ` and `demo.ARC999`,
  `rules_always_exclude`, and valid entries `demo.ARC`, `demo.ARC001` and
  `demo.recommended` beside them.
- **When** `check_errors` runs.
- **Then** each unknown entry is one error whose place is its key path, such as
  `stages.s.rules_include[1]`, whose message names the reference and what its
  ruleset holds, and the valid entries give none.

### **AC-3** A reference of a manifest that cannot be used is an error

An entry of a manifest that names nothing in its own ruleset, is not in the form
of a reference, or is qualified is one error at the manifest's key.

#### Three kinds

- **Given** a ruleset `demo` that declares `ARC` and holds `ARC001`, whose
  manifest has a rule preset `local` with `rules_include = ["ZZZ", "Docs",
  "demo.ARC"]` and `rules_exclude = ["ARC999"]`.
- **When** `check_errors` runs.
- **Then** it returns four errors, whose places are
  `.agents/wio/rules/demo/ruleset.toml#rule_presets.local.rules_include[0]`,
  `…rules_include[1]`, `…rules_include[2]` and `…rules_exclude[0]`, saying that
  `ZZZ` names nothing, `Docs` is not a reference, `demo.ARC` is qualified and a
  manifest names only its own items, and `ARC999` names nothing.

### **AC-4** Each fault is reported once, where it is written

A fault in a manifest or in a rule preset of the config is one error however
many entries reach that rule preset.

#### A preset reached three times

- **Given** the manifest of AC-3, a rule preset `backend` of the config that
  includes `demo.local`, a root `api` and a stage that both include `backend`,
  and an entry of `rules_always_include` of `demo.local`.
- **When** `check_errors` runs.
- **Then** the four errors of AC-3 are returned once each, and no error is
  placed at the entries that reach `demo.local` or `backend`.

### **AC-5** A cycle of rule presets is an error that names them

Rule presets of a manifest that include each other, or one that includes itself,
are one error for each cycle, at the key of the first of them by name.

#### Cycles

- **Given** a manifest with rule presets `a` and `b` that include each other,
  `c` that includes itself, and `d` that includes `a`.
- **When** `check_errors` runs.
- **Then** it returns one error at `…#rule_presets.a` that names `a` and `b`,
  and one at `…#rule_presets.c` that names `c`, and none for `d`.

### **AC-6** A manifest cannot define `all`

A rule preset called `all` in a manifest is one error at its key, and a
reference to `all` is valid.

#### The reserved name

- **Given** a manifest with a rule preset `all` and a rule preset `x` that
  includes `all`, and a config entry `demo.all`.
- **When** `check_errors` runs.
- **Then** it returns one error at `…#rule_presets.all` that says `all` is
  reserved for the whole ruleset, and none for `x` or `demo.all`.

### **AC-7** A root-independent ruleset must not be reached by a root

A root whose rule presets name a root-independent ruleset is one error at each
entry of the root that names it, and a stage that includes it is not.

#### A root and a stage

- **Given** a root-independent ruleset `process` that holds `FIX001`, a root
  `api` whose rule presets are `["demo.recommended", "process.all"]`, and a
  stage that includes `process.FIX001`.
- **When** `check_errors` runs.
- **Then** it returns one error at `roots.api.rule_presets[1]` that names
  `process` and `api`, and none for the stage or for the first entry.

### **AC-8** A reference to a rule that was left out is reported

A reference is judged against the rules that the discovery returned, so a
reference to a rule that it left out for its own fault is an error too.

#### A consequence

- **Given** two rules with the code `ARC001` in `demo`, which the discovery
  leaves out, and a stage that includes `demo.ARC001`.
- **When** `check_errors` runs.
- **Then** it returns the error of the discovery for the shared code and one
  error at the stage's entry that `demo.ARC001` names nothing.

### **AC-9** `wio config check` is unchanged by the move

Moving `join_path`, `item_path` and `find_cycles` to `wio.formats` changes
nothing that `wio config check` reports.

#### Every key path and cycle

- **Given** the configs that the acceptance scenarios of `wio config check` use,
  including cycles of rule presets and of `after`.
- **When** `wio config check` runs on each after the move.
- **Then** every diagnostic, with its place, and every exit code is what it was
  before.

### **AC-10** The errors do not depend on order and need no file

The same config and discovery give the same errors in the same order, whatever
the order of the tables and entries, and `check_errors` reads no file.

#### Two orders

- **Given** the config and the discovery of AC-3 to AC-7 declared in two orders,
  and no file system.
- **When** `check_errors` runs on each.
- **Then** the results are equal.

## Additional context

- `join_path` and `item_path` are in `src/wio/config/messages.py` and
  `find_cycles` in `src/wio/config/pipelines.py` today; `wio.rules` may not
  import `wio.config`, so the delivery moves them, as `cyeth5` moves
  `parse_reference`.
- The place `…#rule_presets.local.rules_include[0]` is the form that C-6 of
  [wio rules](../../README.md) states.
