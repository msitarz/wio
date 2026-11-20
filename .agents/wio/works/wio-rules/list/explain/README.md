<!-- wio
id = "qxfpg9"
template = "feature.leaf"
roots = ["wio"]
depends_on = ["fjvj3x", "1gs341"]
-->

# Explaining a listing

## Purpose

A listing says which rules a view holds but not why each is there or why a rule
is missing, so a person cannot tell which root, rule preset or layer brought a
rule in or took it out.

## Goals

- With `--explain`, each rule shows where it came from: the layers and the
  routes that selected it for a layered view, or the routes of the references
  for a listing of references.
- A rule that is out is shown with the reason that decided it and what removed
  it.
- The text and the JSON carry the same explanation, and without `--explain`
  nothing is added.

## Non-Goals

- Building and rendering the listing, which `fjvj3x` does, and narrowing it,
  which `9r1zpd` does.
- Deciding why a rule is out, which `select` of `5yb4tz` does, and what the
  expansions removed, which `1gs341` records.

## Assumptions

### A-1

A chain reads from the rule outward, as the concepts write it: the rule, then
the layer, then the route from the outermost rule preset to the entry that named
the rule, each joined by `←`, so a rule came from what is on its right.

### A-2

The labels of a layer are `root <name>`, `stage <name>`, `rules_always_include`
and `rules_always_exclude`, and the reasons are written `not selected`,
`excluded by the root's rule preset`, `excluded by the stage`, `vetoed by
rules_always_exclude` and `cut by the roots`.

## Mechanisms

The names of the types and the functions below are provisional.

- **`Explanation`** — a protocol of `wio.models.rules`, declared by `fjvj3x`,
  with `lines()` for the detail lines of a block and `fields()` for the JSON
  fields of a rule; a `Row` of the listing holds one or none.
- **`explain(listing, anywhere) -> Listing`** — in `wio.rules`, where `anywhere`
  is the `SelectedAnywhere` of `1gs341`; it gives each row an explanation built
  from its decision, its routes through the references and what was removed, and
  does no input or output.
- **The explanation of a row** — frozen, with `sources`, the chains of the
  layers and routes that selected the rule, `reason`, the reason it is out or
  none, and `removed_by`, the chains of what removed it.
- **The lines and the fields** — `from:`, `out:` and `by:` lines under the
  block, and `sources`, `reason` and `removed_by` fields in the JSON of the
  rule.

## Acceptance criteria

### **AC-1** An included rule shows where it came from

Each rule of a layered listing shows one `from:` line for each source, which
names the rule, the layer and the route.

#### Three layers

- **Given** a ruleset `demo` that declares `ARC` and `PAY` and holds `ARC001`,
  `ARC002`, `PAY001` and `PAY002`, a rule preset `recommended` that includes
  `ARC`, a root `api` with `rule_presets = ["demo.recommended"]`, a stage `s`
  whose `rules_include` has `demo.PAY001`, a root-independent ruleset `process`
  with `FIX001`, `rules_always_include = ["process.all"]`, and a Work whose
  roots list `api`.
- **When** `wio rules list --work <id> --stage s --explain` runs.
- **Then** the blocks show `from: demo.ARC001 ← root api ← demo.recommended ←
  demo.ARC`, `from: demo.PAY001 ← stage s ← demo.PAY001` and
  `from: process.FIX001 ← rules_always_include ← process.all`.

### **AC-2** A rule with several sources shows all of them in order

A rule that several layers or routes selected has one `from:` line for each,
sorted by layer, then name, then route.

#### Two layers

- **Given** the repository of AC-1 with a stage `s` whose `rules_include` also
  has `demo.ARC001`.
- **When** `wio rules list --work <id> --stage s --explain` runs.
- **Then** `demo.ARC001` has two `from:` lines, root `api` first and stage `s`
  second.

### **AC-3** A rule that is out shows the reason and what removed it

A rule that is out is shown with an `out:` line that gives the reason, and with
a `by:` line for each layer that removed it, besides the `from:` lines of the
layers that added it.

#### Each reason

- **Given** the repository of AC-1 with a stage `s` whose `rules_exclude` has
  `demo.ARC002`, `rules_always_exclude = ["demo.PAY001"]`, a rule preset `extra`
  that includes `PAY` and excludes `PAY002` and that `api` names beside
  `demo.recommended`, and a ruleset `web` whose `WEB001` the stage includes.
- **When** `wio rules list --work <id> --stage s --explain` runs.
- **Then** `demo.ARC002` shows `out: excluded by the stage` with the line
  `by: stage s ← demo.ARC002`, `demo.PAY001` shows its `from:` line and
  `out: vetoed by rules_always_exclude` with a `by:` line, `demo.PAY002` shows
  `out: excluded by the root's rule preset` with its `by:` line, and
  `web.WEB001` shows its `from:` line and `out: cut by the roots`.

### **AC-4** A listing of references shows the routes of the references

A listing with no layers shows, for each rule, the routes by which the
references delivered it.

#### A rule preset

- **Given** the repository of AC-1.
- **When** `wio rules list demo.recommended demo.ARC --explain` runs.
- **Then** `demo.ARC001` has two `from:` lines,
  `demo.ARC001 ← demo.recommended ← demo.ARC` and `demo.ARC001 ← demo.ARC`.

### **AC-5** An unselected rule shows what removed it

With `--not-selected`, a rule that nothing selects shows `out: not selected`,
and a rule that an exclude of a rule preset removed shows that exclude.

#### Not selected and removed

- **Given** the repository of AC-1 with a rule preset `recommended` that
  includes `ARC` and excludes `ARC002`.
- **When** `wio rules list demo.ARC demo.PAY --not-selected --explain` runs.
- **Then** `demo.ARC002` shows `out: not selected` and
  `by: root api ← demo.recommended ← demo.ARC002`, and `demo.PAY002` shows
  `out: not selected` and no `by:` line.

### **AC-6** The JSON carries the same explanation

`--json` gives each rule the fields `sources`, `reason` and `removed_by`, with
the chains as arrays of labels and the reason as a kind and a layer, and nothing
the text lacks.

#### Text and JSON

- **Given** the repository of AC-3.
- **When** `wio rules list --work <id> --stage s --explain` runs as text and
  with `--json`.
- **Then** each rule's object has `sources` as arrays such as
  `["root api", "demo.recommended", "demo.ARC"]`, `reason` as `null` or such as
  `{"kind": "excluded", "layer": "stage"}`, and `removed_by` as arrays, and they
  state what the text states.

### **AC-7** Without `--explain` nothing is added

A listing without `--explain` has no `from:`, `out:` or `by:` line and no
explanation field.

#### The default listing

- **Given** the repository of AC-1.
- **When** `wio rules list --work <id> --stage s` runs as text and as JSON.
- **Then** no block has a `from:`, `out:` or `by:` line and no object has the
  explanation fields.

### **AC-8** The explanation is deterministic and needs no file

The same listing, config and rulesets give the same explanations, whatever the
order of the tables and entries, and `explain` reads no file.

#### Two orders

- **Given** the repository of AC-2 declared in two orders, with no file system.
- **When** `explain` runs on each.
- **Then** the explanations are equal.

## Additional context

- `Explanation` is a protocol that `fjvj3x` declares so that its renderer prints
  a row's extra lines and fields without knowing how they were made; this Work
  supplies the implementation, which is why it depends on `fjvj3x` and not the
  other way round.
