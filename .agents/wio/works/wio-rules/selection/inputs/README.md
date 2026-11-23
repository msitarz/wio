<!-- wio
id = "w3k7vd"
template = "feature.leaf"
roots = ["wio"]
depends_on = ["cyeth5", "8zn10d"]
-->

# Inputs of the selection

## Purpose

Every function that expands a reference, applies the layers or checks the rules
needs the rulesets by canonical name, the aliases and the rule presets of the
config, and every output that names where a rule came from needs the same chain
of labels, so each would build them again and could differ.

## Goals

- The rulesets of a discovery, and the config's aliases and rule presets, are
  put in the shapes that `expand` takes by one function each, so that the
  layers, the rules selected anywhere, the checks and the commands share them.
- An alias is resolved to its ruleset's canonical name in one place.
- The labels of a layer and the chain of a rule's origin are written by one
  function each, so `wio rules list --explain` and `wio rules new` print the
  same text and JSON.

## Non-Goals

- Expanding a reference, which `expand` of `cyeth5` does, and the types that it
  declares.
- Finding which layers selected a rule, which `cm25z9` does, and what a chain
  means, which `qxfpg9` explains to a reader.
- Reading the files of a discovery, which `8zn10d` does.

## Assumptions

### A-1

The config is valid, as A-1 of [wio rules](../../README.md) says, so no two
rulesets share an alias, no alias is the name of another ruleset, and every
ruleset of the config that the discovery returned is a key of the mapping.

### A-2

A ruleset that the config does not mention has no alias and is not
root-independent, and a ruleset of the config that the discovery does not return
is not in the mapping, because no rule of it was read.

## Mechanisms

The names of the functions below are provisional, except that they live in
`wio.rules`.

- **`ruleset_map(discovery: Discovery) -> Mapping[str, LoadedRuleset]`** — the
  rulesets of a `Discovery` by canonical name, in the order of C-2 of
  [wio rules](../../README.md).
- **`build_rule_catalog(config, rulesets) -> RuleCatalog`** — over the `Config`
  and the `Mapping[str, LoadedRuleset]` of `ruleset_map`, the `RuleCatalog` of
  `cyeth5`: the rulesets as given, the aliases from the `alias` of each ruleset
  of the config, and its rule presets.
- **`resolve_ruleset(name: str, catalog: RuleCatalog) -> str | None`** — the
  canonical name of a ruleset that `name` names, as a name or as an alias, or
  none; the commands turn none into a refusal that names it.
- **`layer_label(layer: str, name: str | None) -> str`** — `root api`,
  `stage s`, `rules_always_include` or `rules_always_exclude`, where `layer` is
  `root`, `stage`, `always-include` or `always-exclude` and `name` is none for
  the always layers.
- **`chain_labels(label: str | None, route: Route) -> tuple[str, ...]`** — the
  label, when there is one, followed by the elements of the route, the array of
  the JSON; a listing of references has no layer and so no label.
- **`chain_text(code: str, labels: tuple[str, ...]) -> str`** — the qualified
  code and the labels joined by ` ← `, the text of a `from:`, `by:` or
  `selected:` line.

## Constraints

### C-1

Every consumer calls these functions and none builds the same shapes itself.
`uv run jscpd src tests` verifies that no copy exists, and the criteria of the
consumers, which name the functions, that each one calls them.

## Acceptance criteria

### **AC-1** The rulesets are keyed by canonical name

`ruleset_map` has one entry for each ruleset of the discovery, keyed by its
canonical name, in the order of C-2.

#### Two rulesets

- **Given** a `Discovery` that holds the rulesets `web` and `demo`, in that
  order.
- **When** `ruleset_map` runs.
- **Then** the keys are `demo` and `web`, in that order, and each value is the
  `LoadedRuleset` of that name.

### **AC-2** The catalog carries the aliases and the rule presets of the config

`build_rule_catalog` holds the rulesets as given, an alias for each ruleset of
the config that has one, and the config's rule presets.

#### Aliases and presets

- **Given** a config with a ruleset `demo` with the alias `d`, a ruleset `web`
  with none, a rule preset `backend`, and the discovery of `demo` and `web`.
- **When** `build_rule_catalog` runs.
- **Then** the aliases are `{"d": "demo"}`, the rulesets are those of the
  discovery, and the presets are `backend` only.

### **AC-3** A ruleset that the discovery lacks is not in the catalog

A ruleset of the config whose files were not read is left out.

#### A ruleset with no files

- **Given** the config of AC-2 and a discovery that returns only `demo`.
- **When** `build_rule_catalog` runs.
- **Then** its rulesets have only `demo`, and its aliases still hold `d`.

### **AC-4** A name or an alias is resolved to the canonical name

`resolve_ruleset` gives the canonical name for a name or an alias and none for
anything else.

#### Three names

- **Given** the catalog of AC-2.
- **When** `resolve_ruleset` runs for `demo`, `d` and `nope`.
- **Then** it returns `demo`, `demo` and none.

### **AC-5** The labels and the chain are one text for text and JSON

The label of a layer, the chain of labels and the text of a chain are the forms
that `wio rules list --explain` and `wio rules new` print.

#### Each layer

- **Given** the layers `root` named `api`, `stage` named `s`, `always-include`
  and `always-exclude`, and the route `("demo.recommended", "demo.ARC")`.
- **When** `layer_label` runs for each, `chain_labels` for the first with the
  route, and `chain_text` for `demo.ARC001` with those labels.
- **Then** the labels are `root api`, `stage s`, `rules_always_include` and
  `rules_always_exclude`, the chain is `("root api", "demo.recommended",
  "demo.ARC")`, and the text is
  `demo.ARC001 ← root api ← demo.recommended ← demo.ARC`.

### **AC-6** A chain of references has no layer label

`chain_labels` with no label gives the route alone, and `chain_text` joins it
with the code.

#### References only

- **Given** the route `("demo.recommended", "demo.ARC")`.
- **When** `chain_labels` runs with no label and `chain_text` runs for
  `demo.ARC001` with the result.
- **Then** the labels are `("demo.recommended", "demo.ARC")` and the text is
  `demo.ARC001 ← demo.recommended ← demo.ARC`.

### **AC-7** The functions are deterministic and need no file

The same inputs give equal results whatever the order of the inputs, and no
function reads a file.

#### Two orders

- **Given** the config and the discovery of AC-2 declared in two orders, with no
  file system.
- **When** each function runs on each.
- **Then** the results are equal.

## Additional context

- The function that the consumers call is the one place that knows what a
  `RuleCatalog` is made of, so a change to `RuleCatalog` is made here and in
  `expand` only.
