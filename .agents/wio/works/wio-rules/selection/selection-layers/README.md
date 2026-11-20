<!-- wio
id = "cm25z9"
template = "feature.leaf"
roots = ["wio"]
depends_on = ["cyeth5"]
-->

# Selection layers

## Purpose

The rules that a root, a stage and the always fields select are four separate
lists that nothing applies in order, so no rule has a reason to be in or out of
a stage's rules.

## Goals

- The four layers apply in their order to the expansions of their references,
  for the roots and the stage that are given.
- Every rule of every ruleset keeps the effects of the layers that added it or
  that an exclude named it in, so the reason it is in or out is known.
- The rulesets that each root reaches are returned, for the roots to be applied.

## Non-Goals

- Cutting a rule by the roots and the `Decision` of a rule, which `5yb4tz` does
  with what this returns.
- Finding the roots of a Work, a stage or a file, which `ndwemw` does.
- Reporting a problem as a diagnostic, which `wio rules check` does with the
  problems that the expansions return.

## Assumptions

### A-1

A layer is applied only when its input is given: the layer of the roots when
roots are given, the layer of the stage when a stage is given, and the two
always fields in every call, as the concepts' table of views says.

### A-2

A layer works on the set of rules that the layers before it built: the stage's
excludes take out what the roots and the stage's includes added, the always
includes add rules over any earlier exclude, and the always excludes are the
final veto, which wins over the always includes.

### A-3

An exclude records an effect for every rule it names, whether or not the rule
was in the set, because the author decided about it and a listing can then say
that it was excluded or vetoed and not that nothing selected it; the effects
live in the result of one call and are written nowhere.

## Mechanisms

The names of the types and the functions below are provisional, except that the
field sets of `Layered`, `RuleLayers` and `LayerEffect` are required, because
`5yb4tz`, `1gs341` and `qxfpg9` read them.

- **`apply_layers(roots, stage, config, rulesets) -> Layered`** — in
  `wio.rules`, where `roots` is a `tuple[str, ...]` of root names or `None`,
  `stage` is a stage name or `None`, `config` is the `Config` and `rulesets` is
  a `Mapping[str, LoadedRuleset]`. It calls `expand` of `cyeth5` for the
  includes of each layer, and for an exclude list, such as `rules_exclude` of
  the stage, it expands the entries as a set of rules to remove from everything
  that the earlier layers added, with an effect for each rule the entries name.
- **`Layered`** — frozen, with `rules: Mapping[Rule, RuleLayers]` for every rule
  of every ruleset, `reach: Mapping[str, frozenset[str]]` from each root of the
  config to the rulesets that it reaches, and `problems: tuple[Problem, ...]` of
  the expansions.
- **`RuleLayers`** — frozen, with `selected: bool`, whether the rule is in the
  set after the last layer, and `effects: tuple[LayerEffect, ...]` in the order
  the layers applied.
- **`LayerEffect`** — frozen, with
  `layer: Literal["root", "stage", "always-include", "always-exclude"]`,
  `action: Literal["adds", "removes"]`, `root: str | None`, the root of the
  `root` layer, and `routes: Routes`, the routes of `cyeth5` that led to the
  rule; the `removes` of an include entry's own preset excludes come from the
  `removed` of its `Expansion`, in the layer of that entry.

## Constraints

### C-1

`apply_layers` does no input or output and every ordering in what it returns is
that of C-2 of [wio rules](../../README.md), with the effects in the order the
layers applied and, inside the layer of the roots, by root name. AC-8 verifies
it.

## Acceptance criteria

### **AC-1** The four layers apply in order

A rule is selected when the last layer leaves it in the set, and its effects say
which layers added it and which excludes named it.

#### Every layer

- **Given** a ruleset `demo` that declares `ARC` and `PAY` and holds `ARC001`,
  `ARC002`, `PAY001` and `PAY002` with a rule preset `recommended` that includes
  `ARC`, a root `api` with `rule_presets = ["demo.recommended"]`, a stage `s`
  with `rules_include = ["demo.PAY001"]` and `rules_exclude = ["demo.ARC001"]`,
  `rules_always_include = ["demo.ARC001"]` and
  `rules_always_exclude = ["demo.PAY001"]`.
- **When** `apply_layers` runs for the roots `("api",)` and the stage `s`.
- **Then** `ARC001` is selected with the effects root adds, stage removes and
  always-include adds, `ARC002` is selected with the effect root adds, `PAY001`
  is not selected with the effects stage adds and always-exclude removes,
  `PAY002` is not selected and has no effect, and all four rules are present.

### **AC-2** An exclude takes out what the layers so far added

The stage's excludes remove rules that the roots and the stage's own includes
added, and an exclude of a layer reaches no later layer's includes.

#### Excludes after includes

- **Given** the repository of AC-1 with a stage `t` whose
  `rules_include = ["demo.PAY"]` and
  `rules_exclude = ["demo.PAY001", "demo.ARC"]`, and
  `rules_always_include = ["demo.ARC002"]`.
- **When** `apply_layers` runs for `("api",)` and the stage `t`.
- **Then** `PAY001` is not selected, `PAY002` is selected, `ARC001` is not
  selected, and `ARC002` is selected because the always include added it back,
  with the effects root adds, stage removes and always-include adds.

### **AC-3** The veto is final and records what it names

An always exclude removes a rule that an always include added, and records an
effect for a rule that nothing added.

#### Include and exclude of one rule

- **Given** the repository of AC-1 with `rules_always_include = ["demo.PAY001"]`
  and `rules_always_exclude = ["demo.PAY001"]`.
- **When** `apply_layers` runs for `None` roots and a stage with no rules.
- **Then** `PAY001` is not selected, with the effects always-include adds and
  always-exclude removes.

#### A veto of a rule that nothing added

- **Given** the repository of AC-1 with
  `rules_always_exclude = ["demo.PAY002"]`.
- **When** `apply_layers` runs for `("api",)` and the stage `s`.
- **Then** `PAY002` is not selected and has the one effect always-exclude
  removes.

### **AC-4** A layer is applied only when its input is given

Without roots there is no layer of the roots, without a stage there is no layer
of the stage, and the always fields apply in every call.

#### Inputs left out

- **Given** the repository of AC-1.
- **When** `apply_layers` runs for `None` roots and the stage `s`, for
  `("api",)` and `None`, and for `None` and `None`.
- **Then** the first has no effect of the root layer, the second has no effect
  of the stage layer, and the third has only effects of the two always layers,
  which are always-include adds for `ARC001` and always-exclude removes for
  `PAY001`; the rules of every ruleset are present in all three.

### **AC-5** Several roots add together

The layer of the roots adds the rules of each root, and a rule that two roots
add has an effect for each.

#### Two roots

- **Given** the ruleset of AC-1 with rule presets `one` that includes `ARC001`
  and `family` that includes `ARC`, a root `api` with
  `rule_presets = ["demo.one"]` and a root `web` with
  `rule_presets = ["demo.family"]`.
- **When** `apply_layers` runs for `("web", "api")` and no stage.
- **Then** `ARC001` has two root effects, for `api` and then `web`, and `ARC002`
  has one, for `web`.

### **AC-6** The roots that reach a ruleset are returned

A root reaches the rulesets that the include entries of its rule presets name,
even when the excludes leave none of their rules, and an exclude entry reaches
nothing; a preset's own exclude is recorded as an effect.

#### Reach

- **Given** rulesets `demo`, `other` and `third` that each declare `ARC` and
  hold `ARC001`, a rule preset `recommended` of `demo` that includes `ARC` and
  excludes `ARC`, a rule preset `base` of the config with
  `rules_include = ["demo.recommended", "other.ARC"]` and
  `rules_exclude = ["third.ARC001"]`, a root `api` with
  `rule_presets = ["base"]`, a second root `web` with no rule presets, and a
  stage that includes `third.ARC`.
- **When** `apply_layers` runs for `None` roots and that stage.
- **Then** `reach` has `api` reaching `demo` and `other` although no rule of
  `demo` is left, and not `third`, and has `web` reaching nothing, so every root
  of the config is a key; and with the roots `("api",)` the rule `demo.ARC001`
  has the effect root removes for `api` with the route
  `("base", "demo.recommended", "demo.ARC")`.

### **AC-7** An unknown name is refused, an unknown reference is a problem

An unknown stage or root raises `KeyError` that names it, and a reference that
cannot be expanded is a problem of the result that selects nothing.

#### Unknown names and references

- **Given** the repository of AC-1.
- **When** `apply_layers` runs for a stage `none`, for a root `none`, and for a
  stage whose `rules_include` has `demo.ZZZ` and `Docs`.
- **Then** the first two raise `KeyError` naming `none`, and the third returns
  an `unknown` and a `malformed` problem and the same rules as without those
  entries.

### **AC-8** The result does not depend on order and needs no file

The same config, rulesets and arguments give an equal result, whatever the order
of the tables of the config, of the entries of each list and of the roots
argument, and `apply_layers` reads no file.

#### Two orders

- **Given** the repository of AC-5 declared in two orders, with no file system,
  and the roots argument given as `("web", "api")` and as `("api", "web")`.
- **When** `apply_layers` runs on each.
- **Then** the results are equal, with the effects of the root layer in the
  order of the root names.

## Additional context

- The concepts' table of views names which layers each view applies, which `A-1`
  states for the function; the views themselves are `wio rules list`'s.
- `LayerEffect` and `Routes` move to `wio.models.rules` with `5yb4tz`, which
  completes `Decision` there, because a `Decision` holds them;
  `uv run tach check` verifies the direction of the imports.
