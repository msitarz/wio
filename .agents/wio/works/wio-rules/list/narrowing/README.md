<!-- wio
id = "9r1zpd"
template = "feature.leaf"
roots = ["wio"]
depends_on = ["fjvj3x", "1gs341", "cyeth5", "cm25z9", "w3k7vd"]
-->

# Narrowing a listing

## Purpose

A listing of a root, a stage or a Work shows every rule that applies, so a
person cannot ask about one family or rule preset, or which rules nothing
selects, without reading it all.

## Goals

- References narrow any listing to the rules that they deliver, so a listing of
  a rule preset, a family or a code is a listing like any other.
- `--not-selected` limits a listing to the rules that no include entry of the
  config delivers, among the rules that the view's roots can reach.
- A reference that cannot be used is refused, and the header says what narrowed
  the listing.

## Non-Goals

- Building the listing and rendering it, and declaring the arguments, which
  `fjvj3x` does, and explaining its rules, which `qxfpg9` does.
- Deciding which rules are selected anywhere, which `1gs341` does.
- Expanding a reference, which `expand` of `cyeth5` does.

## Assumptions

### A-1

A reference delivers what `expand` of `cyeth5` returns for it in the config
scope, so a rule preset delivers its includes minus its own excludes, and a
family, a code and `all` deliver the rules they name.

### A-2

Several references together keep the rules that any of them delivers, because
the person asked about each.

### A-3

The candidates of `--not-selected` are those that A-3 of
[wio rules list](../README.md) states.

### A-4

A reference whose expansion returns any problem is refused, at any depth: a
name that names nothing, a malformed one, a cycle, and a bad entry inside a rule
preset that the reference reaches, because the person asked about it and a
partial listing would hide that part of it was not read.

## Mechanisms

The names of the functions below are provisional.

- **`narrow(listing, references, not_selected, config, rulesets, anywhere) ->
  Listing`** — in `wio.rules`, with `listing: Listing` of `fjvj3x`,
  `references` as a `Sequence[str]`, `not_selected: bool`, `config: Config`,
  `rulesets: Mapping[str, LoadedRuleset]` and `anywhere: SelectedAnywhere`,
  which the caller computes and the criteria take as that of the repository
  given, and it does no input or output.
- **The rows that narrowing keeps** — the rows whose rule a reference delivers,
  and with `not_selected` the rows of the candidates that `selected_anywhere`
  does not select, shown although they are out.
- **The header and `via`** — `narrow` returns a listing whose header names the
  references and `--not-selected`, and whose rows hold in `via`, a `Routes`, the
  routes by which the references delivered the rule.
- **The references** — `expand` of `cyeth5` for each, in the config scope, over
  the `RuleCatalog` that `build_rule_catalog` of `w3k7vd` gives.
- **Selected anywhere** — the `SelectedAnywhere` of `1gs341` that the caller
  gives, whose `selected` has as keys the rules that some entry delivers.
- **The reach of the roots** — the `reach` of `apply_layers(None, None, config,
  rulesets)` of `cm25z9`, a second call that answers only the reach, which does
  not depend on the roots or the stage, and that C-2 of the selection Work does
  not forbid, because it forbids a second computation of the decisions.
- **The refusal** — a `WioError` that names the reference, which `wio.cli` turns
  into exit 2; the scope of the expansion decides the wording, so a name that
  names nothing in a ruleset is said to name nothing in it, and a bare name that
  is not a rule preset of the config is said to be none.

## Acceptance criteria

### **AC-1** A reference narrows to the rules it delivers

A listing narrowed by a reference holds the rules that the reference expands to
and no others, and its header names the reference as it was written.

#### Four kinds of reference

- **Given** a ruleset `demo` that declares `ARC` and `PAY` and holds `ARC001`,
  `ARC002`, `PAY001` and `PAY002`, a rule preset `recommended` that includes
  `ARC` and excludes `ARC002`, and the listing of every rule with no layers.
- **When** `narrow` runs for the references `demo.recommended`, `demo.ARC`,
  `demo.PAY001` and `demo.all`, each alone.
- **Then** the rows are `ARC001`; `ARC001` and `ARC002`; `PAY001`; and all four,
  each header names its reference, and the row of `ARC001` for the first records
  the route `demo.recommended`, `demo.ARC`.

### **AC-2** Several references keep the rules that any delivers

A listing narrowed by several references holds each rule that at least one of
them delivers, once, in the order of C-2 of [wio rules](../../README.md).

#### A union

- **Given** the repository of AC-1.
- **When** `narrow` runs for `demo.PAY` and `demo.ARC001` together.
- **Then** the rows are `ARC001`, `PAY001` and `PAY002`, in that order, and the
  header names both references.

### **AC-3** A reference narrows a listing that applied layers

A reference keeps, among the rows of a layered listing, those whose rule it
delivers, and a result that shows nothing is not an error.

#### Within a view

- **Given** the repository of AC-1 with a root `api` whose rule preset
  `demo.recommended` includes `ARC`, and the listing of the root `api`, which
  holds every rule with its decision.
- **When** `narrow` runs for `demo.ARC001`, and for `demo.PAY`.
- **Then** the first holds the row of `ARC001`, included and with its roots, and
  the second holds only the out rows of `PAY001` and `PAY002`, so nothing is
  shown, and neither is an error.

### **AC-4** `--not-selected` keeps the rules that no entry delivers

`--not-selected` limits the listing to the rules that `selected_anywhere` does
not select, shows them although they are out, and marks the header.

#### Unselected rules

- **Given** the repository of AC-1 with a root `api` whose rule preset
  `demo.recommended` is its only one, a stage `s` whose `rules_include` has
  `demo.PAY001`, a ruleset `web` with `WEB001` that no root reaches, and the
  listing of every rule with no layers.
- **When** `narrow` runs with `--not-selected` and no references.
- **Then** the rows are `ARC002`, `PAY002` and `WEB001`, the header is marked
  `not selected`, and neither `ARC001` nor `PAY001`, which entries deliver, is
  held.

### **AC-5** The candidates follow the roots of the view

With a view that applies roots, `--not-selected` considers only the rules that
the roots can reach and the root-independent ones, and without roots every rule.

#### Roots applied and not

- **Given** the repository of AC-4 and a root-independent ruleset `process` with
  `FIX001` and `FIX002`, of which `rules_always_include` names `FIX001`.
- **When** `narrow` runs with `--not-selected` for the listing of the root `api`
  and for the listing of the stage `s` with no roots.
- **Then** the first holds `ARC002`, `PAY002` and `FIX002` and not `WEB001`, and
  the second holds `ARC002`, `PAY002`, `FIX002` and `WEB001`.

### **AC-6** A reference and `--not-selected` together

`--not-selected` keeps, of the rules that the references deliver, those that no
entry delivers, so it says whether a rule preset or a family is in use.

#### Is a rule preset in use

- **Given** the repository of AC-4 and a rule preset `spare` of `demo` that
  includes `PAY` and that no root, stage or always field names.
- **When** `narrow` runs with `--not-selected` for `demo.spare`, for
  `demo.recommended` and for `demo.PAY`.
- **Then** the first holds `PAY002`, the second holds no row, because a root
  names it, and the third holds `PAY002`.

### **AC-7** A reference that cannot be used is refused

A reference that names nothing, is not in the form of a reference, closes a
cycle, or reaches a rule preset with a bad entry is refused with its name, and
no listing is returned.

#### Refusals

- **Given** the repository of AC-1, a rule preset `loop` of `demo` that includes
  itself, and a rule preset `bad` of `demo` that includes `ZZZ`.
- **When** `narrow` runs for `demo.ZZZ`, `demo.ARC999`, `demo.none`, `Docs`,
  `recommended`, `demo.loop` and `demo.bad`, each alone.
- **Then** each raises a `WioError` that names the reference and says why: that
  it names nothing in its ruleset, is not a reference, is not a rule preset of
  the config, is a cycle, or reaches the entry `ZZZ` that names nothing.

### **AC-8** The result is deterministic and needs no file

The same listing, references, config and rulesets give the same result whatever
the order of the references and of the tables, and `narrow` reads no file.

#### Two orders

- **Given** the repository of AC-6 declared in two orders and the references
  given in two orders, with no file system.
- **When** `narrow` runs on each.
- **Then** the results are equal, except that the header names the references in
  the order given.

## Additional context

- A rule that is out is shown by `--not-selected` although the renderer of
  `fjvj3x` hides out rows otherwise; the header's `not selected` mark is what
  tells it to show them, which AC-5 of that Work and AC-4 of this one verify
  from both sides.
- Whether any session would receive an unselected rule, for example because the
  only entry that names it is one that no root reaches, is not asked here; it is
  the warning of `785y9k` and a possible later view.
