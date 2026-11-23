<!-- wio
id = "cyeth5"
template = "feature.leaf"
roots = ["wio"]
depends_on = ["8zn10d", "zq07av"]
-->

# Rule presets

## Purpose

A rule preset names a selection of rules that nothing can expand yet, so a root,
a stage and the always fields cannot say which rules they select, or by which
route.

## Goals

- A list of includes and excludes, written in the config or in a manifest,
  expands to the set of rules it selects, nested rule presets included.
- Each rule of an expansion carries the routes by which it was selected or
  removed, so `--explain` can show where it came from.
- What cannot be expanded is returned as a problem and selects nothing, and
  expanding never raises or loops.
- Every ruleset has a rule preset `all`, and the rulesets that the include
  entries of an expansion name are returned, so the roots that reach a ruleset
  can be known.
- The grammar of references is the one that `wio config check` uses, from
  `zq07av`, so the two never disagree about what a reference is.

## Non-Goals

- The four layers and the roots that apply, which `cm25z9` and `5yb4tz` build on
  this expansion.
- Reporting a problem as a diagnostic, and judging a manifest's preset called
  `all`, which `wio rules check` does with the problems this returns.
- Reading files: the expansion takes values.

## Assumptions

### A-1

The rulesets, their aliases and the rule presets of the config reach the
expansion as values, and the references of the config are already valid, as A-1
of [wio rules](../README.md) says; the references of a manifest are not, so the
expansion handles any text.

### A-2

Every ruleset has a rule preset `all` that holds all its rules, so a preset that
a manifest defines under that name is ignored, and `wio rules check` reports it.

## Mechanisms

The names of the types and the functions below are provisional.

- **`expand(include, exclude, scope, catalog) -> Expansion`** — in `wio.rules`,
  with `include` and `exclude` as `Sequence[str]` of references as written, a
  `Scope` and `RuleCatalog`; the includes are expanded, then the excludes are
  expanded and removed from them.
- **`Scope`** — `ConfigScope()`, where a bare name is a rule preset of the
  config and an item of a ruleset is written `<ruleset>.<item>`, or
  `RulesetScope(name: str)`, where a bare name is a family, a code or a rule
  preset of that ruleset; both are frozen dataclasses.
- **`RuleCatalog`** — frozen, the lookup that the references of an expansion are
  resolved in, with `rulesets: Mapping[str, LoadedRuleset]` by canonical name,
  `aliases: Mapping[str, str]` from an alias to a canonical name, and
  `presets: Mapping[str, RulePreset]` of the config.
- **`Expansion`** — frozen, with `rules: Mapping[Rule, Routes]` of the rules
  selected, `removed: Mapping[Rule, Routes]` of the rules an exclude took out,
  `rulesets: frozenset[str]` of the canonical names of the rulesets that an
  include entry named, and `problems: tuple[Problem, ...]` sorted by route, then
  reference, then kind; an exclude removes from the includes of its own list,
  and that of a nested rule preset is recorded in `removed` without reaching
  outside that preset, so a rule is in both `rules` and `removed` when one entry
  includes it and an exclude inside another entry's rule preset names it, each
  with its own routes.
- **`Route` and `Routes`** — in `wio.models.rules`, which this Work turns from
  `rules.pyi` into `rules.py` with `Decision` and `Selection` left as they are,
  because a stub and its code never coexist, and because a `Decision` holds
  them and a model may not import a component, where a `Route` is a
  `tuple[str, ...]` of the canonical references from the outermost rule preset
  to the entry that named the rule, such as
  `("backend", "demo.recommended", "demo.ARC")`, `Routes` is a sorted
  `tuple[Route, ...]`, and the route of a removal ends with the exclude entry.
- **`Problem`** — frozen, with `kind`, one of `unknown`, `malformed`,
  `qualified-in-manifest` and `cycle`, the `reference` as written, and the
  `route` of the rule presets it was found in; for a cycle the route ends with
  the rule preset that closes it.
- **The shared grammar** — `parse_reference` and `item_kind` for the entries of
  the config and `parse_own_item` for the bare entries of a manifest, all of
  `wio.formats` and built by `zq07av`, so a bare upper-case name stays
  malformed in the config scope, as `wio config check` says today.
- **`LoadedRuleset`, `Rule` and `RulePreset`** — of `wio.models.rule` and
  `wio.models.config`, the values the expansion reads.

## Constraints

### C-1

`expand` does no input or output and raises nothing for a reference or a cycle:
every criterion below runs it on values alone.

## Acceptance criteria

### **AC-1** A family, a code and a rule preset expand to rules

A reference to a family, a code or a rule preset of a ruleset expands to the
rules it names, and a rule preset takes its includes and then removes its
excludes.

#### Three kinds of reference

- **Given** a ruleset `demo` that declares `ARC` and `PAY`, holds `ARC001`,
  `ARC002` and `PAY001`, and whose manifest has a rule preset `recommended` with
  `rules_include = ["ARC"]` and `rules_exclude = ["ARC002"]`.
- **When** `expand` expands `demo.recommended`, `demo.PAY001` and `demo.PAY`,
  each as the only include in the config scope.
- **Then** the first selects `ARC001` by the route
  `("demo.recommended", "demo.ARC")` and removes `ARC002` by
  `("demo.recommended", "demo.ARC002")`, the second selects `PAY001` by
  `("demo.PAY001",)`, and the third selects `PAY001` by `("demo.PAY",)`.

### **AC-2** An exclude reaches only its own level

The excludes of a rule preset take rules out of that preset's includes and never
out of a rule preset that includes it, and an exclude list removes from the
includes of its own list.

#### An outer include brings it back

- **Given** the ruleset of AC-1 and a rule preset `backend` of the config with
  `rules_include = ["demo.recommended", "demo.ARC002"]` and
  `rules_exclude = ["demo.ARC001"]`.
- **When** `expand` expands `backend` in the config scope.
- **Then** it selects `ARC002` by `("backend", "demo.ARC002")`, although
  `recommended` excluded it, and not `ARC001`; `removed` holds `ARC001` by
  `("backend", "demo.ARC001")` and `ARC002` by
  `("backend", "demo.recommended", "demo.ARC002")`.

#### An exclude list

- **Given** the ruleset of AC-1.
- **When** `expand` expands the includes `demo.ARC` and the excludes
  `demo.ARC001` in the config scope.
- **Then** it selects `ARC002` and removes `ARC001`.

### **AC-3** The scope says what a bare name is

In the config scope a bare name is a rule preset of the config, and in a
ruleset's scope it is a family, a code or a rule preset of that ruleset.

#### In the config

- **Given** a ruleset `demo` that declares `ARC`, holds `ARC001` and has a rule
  preset `recommended` that includes `ARC`, and a rule preset `backend` of the
  config with `rules_include = ["demo.recommended"]`.
- **When** `expand` expands `backend`, `recommended` and `ARC001`, each as an
  include in the config scope.
- **Then** `backend` selects `ARC001` by the route
  `("backend", "demo.recommended", "demo.ARC")`, `recommended` is one `unknown`
  problem, and the bare upper-case `ARC001` is one `malformed` problem, as
  `wio config check` judges it, and neither selects anything.

#### In a manifest

- **Given** a ruleset `demo` that declares `ARC` and `PAY`, holds `ARC001` and
  `PAY001`, and whose manifest has a rule preset `local` with
  `rules_include = ["PAY"]` and a rule preset `mixed` with
  `rules_include = ["ARC001", "local"]`.
- **When** `expand` expands `demo.mixed`.
- **Then** it selects `ARC001` by `("demo.mixed", "demo.ARC001")` and `PAY001`
  by `("demo.mixed", "demo.local", "demo.PAY")`.

### **AC-4** An alias names its ruleset

An alias works wherever the ruleset's name does, and a route always shows the
canonical name.

#### An alias

- **Given** a ruleset `demo` with the alias `d` and the manifest of AC-1.
- **When** `expand` expands `d.recommended` and `demo.recommended`.
- **Then** both select and remove the same rules, and every route names `demo`
  and never `d`.

### **AC-5** Every ruleset has a rule preset `all`

`all` holds every rule of its ruleset, whatever the manifest says about it.

#### `all` and a manifest that defines it

- **Given** the ruleset of AC-1, and a ruleset `other` that declares `ARC` and
  holds `ARC001` and `ARC002`, whose manifest defines a rule preset `all` with
  `rules_include = ["ARC001"]`.
- **When** `expand` expands `demo.all`, and expands `all` in the scope of the
  ruleset `demo`, and expands `other.all` for the third.
- **Then** the first two select all three rules of `demo`, and the third selects
  `ARC001` and `ARC002` of `other`, not only `ARC001`.

### **AC-6** A rule reached twice has every route

A rule that two entries select has both routes, sorted, and is one rule.

#### Two routes

- **Given** the ruleset of AC-1 and a rule preset `backend` of the config with
  `rules_include = ["demo.recommended", "demo.ARC001"]`.
- **When** `expand` expands `backend`.
- **Then** `ARC001` is one rule with the routes `("backend", "demo.ARC001")` and
  `("backend", "demo.recommended", "demo.ARC")`, in that order.

### **AC-7** A cycle is a problem, not a loop

A rule preset that includes itself, directly or through others, is one `cycle`
problem, and the rest still expands.

#### Two presets that include each other

- **Given** a ruleset `demo` that holds `ARC001` and `ARC002`, and whose
  manifest has a rule preset `a` with `rules_include = ["ARC001", "b"]` and a
  rule preset `b` with `rules_include = ["ARC002", "a"]`.
- **When** `expand` expands `demo.a`.
- **Then** it returns one `cycle` problem whose route is `("demo.a", "demo.b",
  "demo.a")`, and selects `ARC001` and `ARC002`.

### **AC-8** What cannot be expanded is a problem

An entry that names nothing, is malformed, or is qualified inside a manifest is
one problem that names the reference and the rule presets it was found in,
selects nothing, and leaves the other entries expanded.

#### Each kind of problem

- **Given** a ruleset `demo` that declares `ARC` and holds `ARC001`, with a rule
  preset `broken` in its manifest whose `rules_include` is `["ARC001", "ZZZ",
  "ARC999", "none", "Docs", "demo.ARC"]`, and a config entry `nope.ARC`.
- **When** `expand` expands `demo.broken` and `nope.ARC`.
- **Then** the first selects `ARC001` and returns an `unknown` problem for
  `ZZZ`, `ARC999` and `none`, a `malformed` problem for `Docs` and a
  `qualified-in-manifest` problem for `demo.ARC`, each with the route
  `("demo.broken",)`, and the second returns an `unknown` problem for
  `nope.ARC`.

### **AC-9** A family that is declared but holds no rule is not a problem

A family that the manifest declares and that holds no rule selects nothing and
is no problem.

#### An empty family

- **Given** a ruleset `demo` whose manifest declares `ARC` and `PAY` and that
  holds only `ARC001`.
- **When** `expand` expands `demo.PAY`.
- **Then** it selects nothing and returns no problem.

### **AC-10** The result does not depend on the order of the inputs

The rules are in the order of C-2 of [wio rules](../README.md), the routes of a
rule are sorted, and the result is the same whatever the order of the tables of
the catalog and of the entries of a list.

#### Two orders

- **Given** the repository of AC-6 declared in two orders, with the rule presets
  of the config, the rulesets and the entries of `rules_include` each in a
  different order.
- **When** `expand` expands `backend` on each.
- **Then** the two expansions list their rules, removed rules, routes and
  problems in the same order.

### **AC-11** The rulesets that the includes name are returned

An expansion returns the canonical names of the rulesets that its include
entries name, nested rule presets included, even when its excludes leave none of
their rules, and an exclude entry or an entry that names nothing names no
ruleset.

#### Named rulesets

- **Given** the ruleset `demo` of AC-1 with the alias `d`, a ruleset `other`
  that declares `ARC` and holds `ARC001`, and a ruleset `third` that holds
  `ARC001`.
- **When** `expand` expands the includes `d.recommended` and `other.ARC` with
  the excludes `other.ARC001` and `third.ARC001`, then the include `nope.ARC`,
  and then the include `other.XYZ`.
- **Then** the first returns the rulesets `demo` and `other` and no rule of
  `other`, and not `third`, and the second and the third return no ruleset.

## Additional context

- `find_cycles` lives in `src/wio/config/pipelines.py` today and moves with
  `5qgs79`, the only user in `wio.rules`, because this expansion finds a cycle
  by its own route; the grammar of references moved earlier, with `zq07av`.
- The config's own references are well-formed and its rule presets do not cycle
  once `wio config check` passes, so a problem of the config scope arises only
  from a config the commands have refused already; the expansion still returns
  it, because `wio rules check` and tests give it any text.
