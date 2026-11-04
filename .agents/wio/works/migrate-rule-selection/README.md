<!-- wio
id = "7s2sxm"
template = "feature.leaf"
roots = ["repo"]
depends_on = []

[actions]
deliver = ["promote-docs", "docs-review"]
-->

# Migrate wio's config to rule presets

## Purpose

wio's own config, rule files and `docs/workflow.md` still select rules by tags,
which the design no longer has, so they should use rule presets and stage
excludes, without changing the rules any stage gets.

## Goals

- wio's config is a working example of the design in `docs/concepts.md`, the
  first consumer the `config` Work (`hwn995`) reads.
- Every stage gets exactly the rules it gets today, so the migration changes no
  session's guidance.
- A reader of the config sees `rules_exclude` used where a root brings more
  than one of its stages needs, with the reason next to it.
- `docs/workflow.md` explains the rule selection of wio's workflow without
  tags.

## Glossary

- **Today's rules**: the rules a stage gets under the tag design, for a Work
  whose roots are `wio`, `repo` or both, as the table under Constraints lists
  them.

## Non-Goals

- Changing the rules any stage gets, such as giving the code reviews the
  `contract-upkeep` rules; such a change is a later decision of its own.
- Changing a rule's body, a stage's goal, an action or a stage preset's stages.
- Implementing rule selection or `wio rules list`, which belong to `hwn995`.
- Changing any design in `docs/concepts.md` beyond the rename of its example
  preset.

## Assumptions

- **A-1**: Nothing reads `.agents/wio/config.toml` yet, as its header says, so
  it can change shape without breaking a command.
- **A-2**: Every Work that has roots today names only `wio` and `repo`, and only
  the define, amend and ratify stages and their gates select the `contract`
  root, so today's rules need to hold only for those roots.
- **A-3**: The repository's only rulesets are `contracts`, `contract-upkeep`,
  `docs` and `writing`, and none needs an alias or `root_independent`.

## Mechanisms

- `.agents/wio/config.toml` declares `[stage_presets]` in place of
  `[presets]`, `rule_presets` on each root in place of `rulesets`, and
  `rules_include` and `rules_exclude` on stages in place of `tags`.
- `.agents/wio/rules/contracts/ruleset.toml` declares the rule presets
  `authoring`, `review`, `amend` and `ratify`, so the contract root and the
  contract stages select its rules by name.
- `promote-docs` writes these files, and `docs-review` judges them against this
  contract.

## Constraints

- `promote-docs` writes `.agents/wio/config.toml`, the files under
  `.agents/wio/rules/`, `docs/workflow.md` and `docs/concepts.md`, beyond the
  README and GLOSSARY files its goal names, because those are where this Work's
  guarantees live.
- The selection is read as section 10 of `docs/concepts.md` states it: the
  presets of the roots the stage selects, then the stage's `rules_include` and
  `rules_exclude`, then the always fields, and a rule applies only when its
  ruleset is reached by a root the stage selects.
- Today's rules, with **contract set** meaning every rule of `contracts` except
  `ACC009`, `ACC010`, `CON011`, `CON012` and `CON013`:

  | Stage | Today's rules |
  | --- | --- |
  | `define` | the contract set, `WRT001`, `WRT002` |
  | `review-contract` | the contract set, `ACC009`, `ACC010`, `CON011`, `WRT001`, `WRT002` |
  | `amend` | the contract set, `CON012`, `WRT001`, `WRT002` |
  | `review-amendment` | the contract set, `ACC009`, `ACC010`, `CON011`, `CON012`, `WRT001`, `WRT002` |
  | `ratify` | the contract set, `CON013`, `WRT001`, `WRT002` |
  | `review-ratify` | the contract set, `ACC009`, `ACC010`, `CON011`, `CON013`, `WRT001`, `WRT002` |
  | `architecture`, `wiring`, `implementation`, `integration` | `UPK001`, `UPK002` |
  | `architecture-review`, `wiring-review`, `implementation-review`, `system-review` | none |
  | `promote-docs`, `docs-review` | `DOC001`, `DOC002`, `DOC003`, `WRT001`, `WRT002` |

- The roots select whole rulesets or the `contracts` presets: `contract` takes
  `contracts.authoring` and `writing.all`, `wio` takes `contract-upkeep.all`,
  and `repo` takes `contract-upkeep.all`, `docs.all` and `writing.all`.
- Where a root brings rules a stage does not get today, the stage excludes
  them by family, and a comment says why: the code reviews exclude
  `contract-upkeep.UPK`, `docs.DOC` and `writing.WRT`; the four authoring
  stages of `deliver` exclude `docs.DOC` and `writing.WRT`; and `promote-docs`
  and `docs-review` exclude `contract-upkeep.UPK`.
- `contracts.authoring` includes the families `CON`, `ACC`, `CST` and `VIS` and
  excludes the presets `review`, `amend` and `ratify`, which hold `ACC009`,
  `ACC010` and `CON011`, then `CON012`, then `CON013`.
- The comments of the config and of each `ruleset.toml` describe presets and
  excludes, and none describes tags or binding by a root's `rulesets`.
- The last commit of `promote-docs` retires this contract once the driver
  confirms it is spent.

## Visuals

Before: a rule carries tags, a root's `rulesets` binds rulesets, and a stage's
`tags` pick the rules whose tags it has all of. After: a root's `rule_presets`
selects and reaches rulesets, a stage adds a `contracts` preset or excludes
families its roots bring, and a rule file carries no tags. The table under
Constraints is the same before and after.

## Acceptance criteria

### **AC-1** Every stage keeps today's rules

For each stage of `.agents/wio/config.toml` and each Work roots of `["wio"]`,
`["repo"]` and `["wio", "repo"]`, the rules that the selection of
`docs/concepts.md` gives are the rules the table under Constraints lists.

#### The stages traced

- **Given** the delivered config and rulesets.
- **When** a reviewer traces the layers for every stage and those roots.
- **Then** each stage's rules equal its row of the table, with no rule more or
  less.

### **AC-2** The config uses only the rule-preset design

`.agents/wio/config.toml` has no `tags` key and no `[presets]` or `rulesets`
key, declares `[stage_presets]` with the same stage presets and stages, gives
each root `rule_presets`, and gives the stages the `rules_include` and
`rules_exclude` the Constraints list. Every reference names an existing
ruleset, family, code or preset in the form that section 10 of
`docs/concepts.md` gives, and each `rules_exclude` has a comment that says why.

#### The config

- **Given** the delivered `.agents/wio/config.toml`.
- **When** a reviewer reads it against section 10 of `docs/concepts.md`.
- **Then** no key of the tag design remains, every reference resolves and has
  a valid form, and every exclude carries its reason.

### **AC-3** The rule files carry no tags and the manifests no name

No rule file under `.agents/wio/rules/` has a `tags` or `types` key, no
`ruleset.toml` has a `name` key, and `contracts/ruleset.toml` declares
`[rule_presets.authoring]`, `[rule_presets.review]`, `[rule_presets.amend]` and
`[rule_presets.ratify]` as the Constraints describe.

#### The rulesets

- **Given** the delivered `.agents/wio/rules/`.
- **When** a reviewer reads each rule file and manifest.
- **Then** only `code` and `name` remain in a rule's metadata, each manifest
  holds `description`, `[families]` and, for `contracts`, its four presets.

### **AC-4** The workflow explains selection by presets

`docs/workflow.md` explains which roots bring which rulesets, which stages add
a `contracts` preset, and which stages exclude what their roots bring and why,
says "stage preset" where it means a list of stages, and links to
`docs/concepts.md` for the design instead of restating it.

#### The workflow

- **Given** the delivered `docs/workflow.md`.
- **When** a reviewer reads its sections on the contract root and on delivery.
- **Then** it agrees with the config, names no tag, and every "preset" names
  its kind.

### **AC-5** The concepts example names the authoring preset

The examples of `docs/concepts.md` that name the contract ruleset's presets use
`contracts.authoring` and `[rule_presets.authoring]` in place of `writing`, and
nothing else in `docs/concepts.md` changes.

#### The example

- **Given** the delivered `docs/concepts.md`.
- **When** a reviewer compares it with the commit before this Work.
- **Then** only the example's preset name differs.

### **AC-6** No trace of tags remains in the workflow's files

A search of `.agents/wio/config.toml`, `.agents/wio/rules/` and
`docs/workflow.md` for the word `tag` or `tags` finds nothing, and
`make check` passes.

#### The search

- **Given** the delivered branch.
- **When** a reviewer runs
  `ggrep -rniwE 'tags?' .agents/wio/config.toml .agents/wio/rules docs/workflow.md`
  and `uv run make check` in a clean clone.
- **Then** the search prints nothing and every check passes.
