<!-- wio
id = "xxbge6"
template = "feature.draft"
roots = []
depends_on = []
-->

# Rule presets in place of tags

## Purpose

Tags are a global vocabulary that no ruleset owns and that means something
different on a rule, a stage and a template, so the design should select rules
by names that exist, before the config Work turns tags into code.

## Intent

From the brainstorm of 2026-11-04. Decisions are made unless marked open. Each
decision carries its reason, and the docs keep that reason in short form.

**Shape.** A leaf that changes the design docs and the architecture stubs:
`docs/concepts.md`, `GLOSSARY.md`, `docs/workflow.md`, `docs/v0.1-scope.md`,
`docs/split-exercises.md`, `README.md`, `docs/README.md`,
`src/wio/models/rules.pyi` and `src/wio/models/config.pyi`. Two follow-ups are
outside it: the `config` draft (hwn995) is updated to the design before it is
defined, and wio's own `config.toml` and rule files are migrated so that every
stage keeps the rules it gets today.

**Dropped.** Tags (the config's vocabulary, on rules and on stages), `types` on
rules, the `[rulesets.<name>]` keys `include`, `exclude`, `tags` and `types`,
effective tags and types, the family prefix-clash check, and `rulesets` on a
root. Selection moves to the consumer, which names what it wants, so a typo is
an unresolved name instead of a rule that never loads.

**Names.**

- `[presets]` becomes `[stage_presets]`, and the glossary defines a preset as a
  named, reusable selection of two kinds: stage preset and rule preset.
- `[rule_presets.<name>]` in the config and in a `ruleset.toml`, with
  `rules_include` and `rules_exclude`. A keyed table, so TOML rejects a
  duplicate name.
- `[rulesets.<name>]` holds only `alias` (at most one) and `root_independent`.
- `[[roots]]` gains `rule_presets`, which takes presets only.
- `[stages.<name>]` gains `rules_include` and `rules_exclude`.
- The config's top level gains `rules_always_include` and
  `rules_always_exclude`.

**References.**

- `<ruleset>.<item>` with exactly one dot names a family (uppercase letters), a
  code (a family and digits) or a preset (lowercase, letters, digits and `_`).
  A ruleset name or alias is lowercase and may use `-` and `_`. The form tells
  the kind, so wio never looks a name up to learn what it is.
- A bare name is a config preset.
- A `ruleset.toml` uses bare names for its own items only, because a ruleset is
  portable data.
- Every ruleset has a reserved `all` preset.
- An alias works wherever a ruleset prefix does, and records, bundles and
  `wio rules list` always show the canonical name.
- Names are case-sensitive, and a preset cycle is an error that names it.

**Selection.**

- Layers, in order: the presets of the roots the stage selects, then the
  stage, then `rules_always_include`, then `rules_always_exclude`. Within a
  layer the exclude runs after the include, and a preset resolves to a set
  first.
- `rules_always_include` overrides any layer's exclude; it is for project-wide
  rules, such as "fix the underlying problem". `rules_always_exclude` is the
  final veto and takes codes and families only, so editing a preset never
  widens it.
- No action, template or contract layer. An action runs different stages in
  different templates, type-specific guidance for writing a contract belongs in
  the template's authoring comments, a type-specific procedure is a stage of
  the template's pipeline, and rules that follow an area of code belong to a
  root (such as a `billing-legacy` root a Work lists). No inheritance down the
  Work tree.
- A rule applies when the layers select it and its ruleset is
  `root_independent` or reached by a root the stage selects. A root's presets
  reach a ruleset, so binding is implicit and eligibility is per ruleset: a
  stage can add a reviewer-only rule from a ruleset its roots reach. The docs
  show this with the four-row "applies" table from the brainstorm.

**Bundles.** Root-independent rules come first, under `Rules for every root:`,
then one group per set of roots, then ruleset, family (with its topic) and
code. A rule is shown by its qualified canonical name and its name, such as
`mattpocock.ERR003 errors-carry-context`, which is also how gates and events
cite it. A bundle does not say why a rule was selected.

**`wio rules list`.** `--preset`, `--root`, `--stage`, `--work` (with
`--stage`), `--path` and `--explain`. Each flag applies the layers its object
owns, the always fields apply whenever a layer does, and the header names the
layers applied. Roots that are not applied are shown per rule. `--explain`
gives each rule's source and why a rule is out.

**Checks.** Errors: an unresolved reference, a name of the wrong form, a
qualified reference in a `ruleset.toml`, a preset cycle, a preset in
`rules_always_exclude`, a preset named `all`, a clashing alias, a
`root_independent` ruleset reached by a root, and a `rules_*` key where none
belongs. Warnings: a rule nothing selects, a ruleset nothing reaches, a stage
selection that no root can reach, and a rule in both always fields. A note
lists `rules_always_include`.
