<!-- wio
id = "1gs341"
template = "feature.leaf"
roots = ["wio"]
depends_on = ["cyeth5"]
-->

# Rules selected anywhere

## Purpose

Whether any entry of the config includes a rule is asked by `wio rules list` and
by `wio rules new` and answered by no code, so neither can say which rules
nothing selects or whether a new rule is selected.

## Goals

- Every rule that some include entry of the config delivers is known, with the
  entries that deliver it.
- A rule that no include entry delivers is known to be unselected, so the
  listing of unselected rules and the report of `wio rules new` read one answer.
- The rules that an exclude of a rule preset took out are known with the entries
  that did, so a listing can say what removed a rule that nothing selects.

## Non-Goals

- Applying a rule to a stage, a root or a Work, which `select` of `5yb4tz` does,
  and whether a root reaches the rule's ruleset, which `785y9k` warns about.
- Listing the rules or reporting for `wio rules new`, which `wio rules list` and
  `wio rules new` do with this answer.
- The question whether a session would ever receive the rule, which a later view
  of the decisions could answer.

## Assumptions

### A-1

An include entry delivers the rules that it expands to after the excludes of the
rule presets it names, because a named rule preset is a resolved set; a stage's
`rules_exclude` and `rules_always_exclude` remove rules from a view and do not
unselect them, as the reasons `excluded` and `vetoed` of a decision say.

### A-2

An entry counts whatever the roots, so an entry that names a ruleset that no
root reaches still delivers its rules, and a stage counts even when no pipeline
uses it.

### A-3

An entry that cannot be expanded delivers nothing and is no error here, as A-9
of [wio rules](../../README.md) says; `wio rules check` reports it.

## Mechanisms

The names of the types and the functions below are provisional.

- **`selected_anywhere(config, rulesets) -> SelectedAnywhere`** — in
  `wio.rules`, where `config` is the `Config` and `rulesets` is a
  `Mapping[str, LoadedRuleset]`; a `SelectedAnywhere` holds
  `selected: Mapping[Rule, tuple[Source, ...]]`, only the rules that some entry
  delivers, so a rule that is not a key of it is unselected, and
  `removed: Mapping[Rule, tuple[Source, ...]]`, the rules that an exclude of a
  rule preset took out, with the entries; it does no input or output, and the
  criteria below speak of the keys and sources of `selected` unless they say
  `removed`.
- **`Source`** — frozen, with `layer`, one of `root`, `stage` and
  `always-include`, `name`, the root or the stage or none, and `routes`, the
  routes of `cyeth5` that led from the entry to the rule.
- **The sources** — the rule presets of each root, the `rules_include` of each
  stage and `rules_always_include`, each expanded with `expand` of `cyeth5` and
  no excludes of its own layer.

## Acceptance criteria

### **AC-1** A rule that an entry delivers is selected, with its sources

Each rule that a root's rule presets, a stage's `rules_include` or
`rules_always_include` expands to is a key, with a source that names the layer
and the root or the stage, and a rule that no entry delivers is not.

#### One of each kind

- **Given** a ruleset `demo` that declares `ARC` and `PAY` and holds `ARC001`,
  `ARC002`, `PAY001` and `PAY002`, a rule preset `recommended` that includes
  `ARC` and excludes `ARC002`, a root `api` with
  `rule_presets = ["demo.recommended"]`, a stage `s` whose `rules_include` has
  `demo.PAY001`, a root-independent ruleset `process` with `FIX001`, and
  `rules_always_include = ["process.all"]`.
- **When** `selected_anywhere` runs.
- **Then** the keys are `demo.ARC001`, `demo.PAY001` and `process.FIX001`, with
  the sources root `api`, stage `s` and always-include, each with its routes,
  `demo.ARC002` and `demo.PAY002` are not keys, and `removed` holds
  `demo.ARC002` with the source root `api` and the route `demo.recommended`,
  `demo.ARC002`.

### **AC-2** A rule with several sources has all of them in order

A rule that several entries deliver has one source for each, sorted by layer,
then name, then route.

#### Several entries

- **Given** the repository of AC-1, a root `web` whose rule preset also includes
  `demo.ARC001`, and stages `s` and `t` whose `rules_include` has `demo.ARC001`.
- **When** `selected_anywhere` runs.
- **Then** `demo.ARC001` has the sources root `api`, root `web`, stage `s` and
  stage `t`, in that order.

### **AC-3** Excludes of a layer and the veto do not unselect

A stage's `rules_exclude` and `rules_always_exclude` leave a rule selected.

#### Removed in a view, still selected

- **Given** the repository of AC-1, a stage `s` whose `rules_exclude` has
  `demo.PAY001`, and `rules_always_exclude = ["demo.ARC001"]`.
- **When** `selected_anywhere` runs.
- **Then** `demo.ARC001` and `demo.PAY001` are still keys.

### **AC-4** An entry that no root reaches still delivers

An entry counts whatever the roots.

#### A ruleset no root reaches

- **Given** a ruleset `py` that no root reaches, and a stage whose
  `rules_include` has `py.review`.
- **When** `selected_anywhere` runs.
- **Then** the rules of `py.review` are keys with the source of that stage.

### **AC-5** What cannot be expanded delivers nothing and raises nothing

An entry that names nothing, is malformed or closes a cycle selects nothing, and
the rest are still found.

#### Bad entries

- **Given** the repository of AC-1 with a stage whose `rules_include` has
  `demo.ZZZ`, `Docs`, `demo.loop` and `demo.PAY001`, where `loop` is a rule
  preset of `demo` that includes itself.
- **When** `selected_anywhere` runs.
- **Then** it raises nothing, `demo.PAY001` is a key with the source of that
  stage, and the bad entries add no key.

### **AC-6** An alias gives the canonical name

A ruleset's alias works in an entry and a source shows the canonical name.

#### An alias

- **Given** a ruleset `demo` with the alias `d` and a stage whose
  `rules_include` has `d.PAY001`.
- **When** `selected_anywhere` runs.
- **Then** the key is `demo.PAY001` and its routes name `demo` and not `d`.

### **AC-7** The answer is deterministic and needs no file

The same config and rulesets give the same mapping in the order of C-2 of
[wio rules](../../README.md), whatever the order of the tables and entries, and
a config with no roots, stages or always fields gives an empty mapping.

#### Two orders and an empty config

- **Given** the repository of AC-2 declared in two orders, and a config with no
  roots, stages or always fields, with no file system.
- **When** `selected_anywhere` runs on each.
- **Then** the first two mappings are equal and the last is empty.

## Additional context

- The question "would any session receive this rule?" differs from this one for
  an entry that names a ruleset no root reaches; `785y9k` warns about such an
  entry, and a listing of the rules that no session receives could be added
  later from the decisions of `5yb4tz`.
