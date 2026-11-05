<!-- wio
id = "s1aqzm"
template = "feature.leaf"
roots = ["wio", "repo"]
depends_on = ["mcn1xg"]
-->

# Checking rule selection in the config

## Purpose

The rule references in the config must name rulesets, presets and families
that exist, in the forms the config accepts, before a stage selects rules by
them.

## Goals

- A reference to a ruleset, an alias or a rule preset that does not exist is an
  error that says what exists.
- A name of the wrong form is an error that says the form.
- A rule preset that refers to itself, directly or through others, is an error.
- A field that takes a kind of name it does not accept is an error: a family or
  a code in a root's `rule_presets`, and a preset in the final veto.
- A ruleset directory without a manifest, and a clashing alias, are errors.
- A note tells a driver what every session receives.

## Glossary

- **Reference**: an entry of `rule_presets`, `rules_include`, `rules_exclude`,
  `rules_always_include` or `rules_always_exclude`: a bare name of a rule
  preset of the config, or `<ruleset>.<item>`, where `<ruleset>` is a ruleset's
  directory name or alias and `<item>` is a family, a code or a preset
  ([the concepts](../../../../../../docs/concepts.md#names-and-references)).

## Non-Goals

- Whether the family, code or preset after the dot exists: it needs the rule
  files, which the rules Work reads.
- The hint for a misplaced `rules_*` key, which the loader gives from the
  schema, and a `rules_*` key on a template or a contract, which the templates
  and contracts Works check.
- A qualified reference inside a `ruleset.toml`, a `ruleset.toml`'s contents,
  unselected rules, dead selections and a root that reaches a root-independent
  ruleset: also the rules Work's.

## Assumptions

- **A-1**: The rulesets are the directories of `.agents/wio/rules/`, and a
  ruleset is known by its directory name or its alias.
- **A-2**: The config's rule presets contain bare names and qualified ones, and
  a bare name is a rule preset of the config.

## Mechanisms

- `FileSystem.list_dir` of `.agents/wio/rules`, for the names of the rulesets
  and whether each has a `ruleset.toml`.
- Checks added to the ordered list of the loader.
- A depth-first search for a cycle among the config's rule presets.

## Acceptance criteria

### **AC-1** Names have the form of their kind

A bare name, a ruleset name, an alias and the parts of a qualified reference
follow the forms of the concepts: a family is upper-case letters, a code is a
family and digits, and a preset, a ruleset and an alias are a lower-case
letter, then lower-case letters, digits, `-` and `_`.

#### Wrong forms

- **Given** the entries `Docs.DOC`, `docs.Doc1`, `docs.DOC001.x` and a
  directory `My Rules`, holding a `ruleset.toml`, under `.agents/wio/rules`.
- **When** the checks run.
- **Then** each is an error that names the form that part should have, and the
  directory's error names its name.

### **AC-2** Every reference resolves to a ruleset or a preset

The first part of a qualified reference is the name or alias of a ruleset
directory, and a bare name is a rule preset of the config.

#### Unknown ruleset and preset

- **Given** a stage `define` with `rules_include = ["docz.DOC", "mine",
  "docs.DOC"]` where there is a ruleset `docs` and no rule preset `mine`.
- **When** the checks run.
- **Then** an error at `stages.define.rules_include[0]` names `docz` and lists
  the rulesets and aliases, one at `stages.define.rules_include[1]` lists the
  config's rule presets, and the third passes.

#### In a root and an always field

- **Given** a root `wio` with `rule_presets = ["docz.all"]`, where there is no
  ruleset or alias `docz`, and `rules_always_include = ["nope"]`.
- **When** the checks run.
- **Then** an error at `roots.wio.rule_presets[0]` names `docz` and one at
  `rules_always_include[0]` lists the config's rule presets.

#### An alias

- **Given** `[rulesets.docs] alias = "d"` and the entry `d.DOC`.
- **When** the checks run.
- **Then** the entry passes.

### **AC-3** Rule presets do not form a cycle

A cycle among the config's rule presets is an error that names the presets on
it.

#### A cycle

- **Given** presets `a` including `b`, and `b` including `a`, and a preset `s`
  including `s`.
- **When** the checks run.
- **Then** one error names `a` and `b`, and one names `s`.

### **AC-4** Each field takes only the kinds of name it needs

A root's `rule_presets` take rule presets only, and `rules_always_exclude`
takes qualified codes and families only; the other fields take every kind.

#### A family in a root and a preset in the veto

- **Given** a ruleset `docs`, a root `wio` with
  `rule_presets = ["docs.DOC", "docs.all"]`, and
  `rules_always_exclude = ["docs.recommended", "mine", "docs.DOC001"]` where
  `mine` is a config rule preset.
- **When** the checks run.
- **Then** an error at `roots.wio.rule_presets[0]` says a root takes rule
  presets only, the second entry passes, errors at `rules_always_exclude[0]` and
  `rules_always_exclude[1]` say only qualified codes and families are allowed
  there, and the third passes.

### **AC-5** Rulesets and aliases are consistent

Every `[rulesets.<name>]` entry has a ruleset directory, every directory has a
`ruleset.toml`, and aliases are unique and do not clash with a ruleset's name.

#### The errors

- **Given** `[rulesets.ghost]` with no directory, a directory `bare` without a
  `ruleset.toml`, and two rulesets with the alias `d`, and an alias equal to
  another ruleset's name.
- **When** the checks run.
- **Then** each is an error that names the ruleset and what is wrong.

### **AC-6** A note lists what every session gets

When `rules_always_include` is not empty, a note at it lists its entries.

#### The note

- **Given** a ruleset `process` and
  `rules_always_include = ["process.fix-the-cause"]`.
- **When** `wio config check` runs.
- **Then** a note lists the entry, and the command exits 0 when no other
  diagnostic is an error.

## Additional context

- [Checking rules](../../../../../../docs/concepts.md#checking-rules) lists the
  checks and the ones left to the rules Work.
