<!-- wio
id = "785y9k"
template = "feature.leaf"
roots = ["wio"]
depends_on = ["cm25z9", "5qgs79", "w3k7vd"]
-->

# Warnings of rules and rulesets

## Purpose

A selection that no root can reach, a rule that both always fields name and a
heading in a rule's body do nothing wrong at first sight and fail silently, so
nothing tells the author that a rule will never reach a session or that the
bundle will break.

## Goals

- Every warning that `wio rules check` owns is found and placed: the warnings of
  the discovery, a selection that no root reaches, a rule that both always
  fields name, and a Markdown heading in a rule's body.
- The warning about a selection or about both always fields says what is wrong
  and how to fix it, and each warning is placed at the key or the file the
  author has to edit.
- Each warning is reported once.

## Non-Goals

- The errors, which `5qgs79` builds, and the report that joins them, which the
  parent builds.
- Listing the rules that nothing selects, which `wio rules list --not-selected`
  does, so no warning is given for them.
- Reporting the note on `rules_always_include`, which `wio config check` does.

## Assumptions

### A-1

The config is valid, as A-1 of [wio rules](../../README.md) says, so every
reference in it is well-formed and names a ruleset that exists; what needs the
rule files is which rulesets an entry names and which roots reach them.

### A-2

A root reaches a ruleset when the include entries of its rule presets name it,
as the concepts say, and a stage selects the roots of its own `roots`, with
`@work` standing for the Work's roots, which are not known here and so stand for
any root of the config, as does a stage with no `roots`, and as do the entries
of `rules_always_include`, which belong to no stage.

## Mechanisms

The names of the functions below are provisional.

- **`check_warnings(config: Config, discovery: Discovery) -> tuple[Diagnostic, ...]`**
  — in `wio.rules`; it does no input or output. It returns the warnings of the
  discovery as they are, and judges each entry on its own with `expand` of
  `cyeth5`, over the `Sources` that `build_sources` of `w3k7vd` gives from the
  `ruleset_map` of the discovery, and writes its places with `join_path` and
  `item_path` that `5qgs79` moves to `wio.formats`.
- **The rulesets an entry names** — the `rulesets` of the `Expansion` that
  `expand` returns for an entry, nested rule presets included; a ruleset that
  the discovery left out is not among them, so it gives no warning.
- **The reach of the roots** — the rulesets that the roots of the config reach,
  from `apply_layers` of `cm25z9` with no roots and no stage, and the
  `root_independent` setting of each ruleset in the config.
- **Both always fields** — the entries of `rules_always_include` and of
  `rules_always_exclude` expanded with `expand`, and the rules that an include
  entry and an exclude entry both deliver.
- **The headings of a body** — `read_outline` of `wio.formats`, called with the
  body of a `Rule` and its `body_line`, which finds the real headings of a
  Markdown body and ignores those in code, comments, quotes and lists.

## Acceptance criteria

### **AC-1** The warnings of the discovery are shown

Every warning of the discovery is returned as it is, and its errors are not.

#### Pass-through

- **Given** a discovery with an unknown key in a rule's block, an unknown key in
  a manifest and a manifest that does not parse.
- **When** `check_warnings` runs.
- **Then** it returns the two warnings with their places and messages unchanged,
  and not the error.

### **AC-2** A selection that no root reaches is a warning with a fix

An entry in a stage's `rules_include` that names a ruleset that is not
root-independent, and that none of the roots the stage selects reaches, is one
warning at the entry's key path, which names the ruleset and says how to fix it.

#### Stages

- **Given** a root `api` that reaches `demo`, a ruleset `py` that is not
  root-independent and that no root reaches, a root-independent ruleset
  `process`, a stage `s` with no `roots` and a stage `t` with `roots = ["api"]`
  that each include `py.review`, a stage `u` with `roots = []` and a stage `w`
  with `roots = ["web"]`, where the root `web` reaches nothing, that each
  include `demo.ARC`, and a stage `x` that includes `process.all`.
- **When** `check_warnings` runs.
- **Then** it returns warnings at `stages.s.rules_include[0]`,
  `stages.t.rules_include[0]`, `stages.u.rules_include[0]` and
  `stages.w.rules_include[0]`, none for the stage `x`, and each message names
  the ruleset, says that it is not root-independent and that none of the roots
  reaches it, and says to mark it `root_independent` or to name it in a root's
  `rule_presets`.

### **AC-3** A stage on the Work's roots and the always field count every root

A stage with no `roots`, or with `@work` among them, and the entries of
`rules_always_include` count a ruleset as reached when any root of the config
reaches it.

#### Any root

- **Given** a root `api` that reaches `demo` and no root that reaches `py`, a
  stage `v` with `roots = ["contract", "@work"]` that includes `demo.ARC` and
  `py.review`, and `rules_always_include` with `py.FIX` and `demo.ARC`.
- **When** `check_warnings` runs.
- **Then** it returns one warning at `stages.v.rules_include[1]` for `py` and
  one at `rules_always_include[0]` for `py`, with the same fix, and none for
  `demo.ARC` in either.

### **AC-4** An entry that names several rulesets is judged for each

An entry that reaches several rulesets through a rule preset is one warning for
each ruleset that no root reaches, and none for the others.

#### A preset of two rulesets

- **Given** a rule preset `mixed` of the config that includes `demo.ARC` and
  `py.review`, a root `api` that reaches `demo`, and a stage that includes
  `mixed`.
- **When** `check_warnings` runs.
- **Then** it returns one warning at the stage's entry that names `py`, and none
  for `demo`.

### **AC-5** Excludes and the entries of the roots are not judged

An exclude entry and an entry of a root's `rule_presets` are not warned about.

#### Entries left alone

- **Given** the config of AC-2 and a stage whose `rules_exclude` has
  `py.review`, and a root whose `rule_presets` has `process.all`.
- **When** `check_warnings` runs.
- **Then** it returns no warning for the exclude or for the root's entry.

### **AC-6** A rule that both always fields name is a warning with a fix

An entry of `rules_always_include` whose rules an entry of
`rules_always_exclude` vetoes is one warning at the include entry, which names
the exclude entry and the rules with their names, says that the veto wins, and
says to remove one of the two entries.

#### An include and an exclude

- **Given** `rules_always_include = ["demo.ARC", "demo.PAY001"]` and
  `rules_always_exclude = ["demo.ARC001", "demo.ARC002"]`, in a ruleset `demo`
  that holds `ARC001` named `first-rule`, `ARC002` named `second-rule`, `ARC003`
  and `PAY001`.
- **When** `check_warnings` runs.
- **Then** it returns one warning at `rules_always_include[0]` that names the
  exclude entries and `demo.ARC001 first-rule` and `demo.ARC002 second-rule`, in
  that order, that the veto wins and that one of the two entries should go, and
  none for `rules_always_include[1]`.

### **AC-7** A heading in a rule's body is a warning

A rule whose body has a real Markdown heading is one warning at the line of its
first heading, which names the rule with its name and the heading, and a heading
in code is not one.

#### Real headings only

- **Given** a rule `demo.ARC001` named `keep-it-small` whose block takes lines 1
  to 4, followed by a blank line and a body whose first line, line 6, is
  `## Notes`, followed later by `### More`, a rule `demo.ARC002` whose body has
  `# not a heading` in a fenced code block, and a rule in the `+++` front matter
  form whose body has a real heading.
- **When** `check_warnings` runs.
- **Then** it returns one warning for each rule with a real heading, at
  `.agents/wio/rules/demo/ARC001-keep-it-small.md:6` for the first, that names
  `demo.ARC001 keep-it-small` and the heading `## Notes` and not `### More`,
  none for `demo.ARC002`, and it does not matter which block form the rule has.

### **AC-8** The warnings are reported once and do not depend on order

Each warning is returned once, in the order of C-2 of
[wio rules](../../README.md), whatever the order of the tables and entries, and
`check_warnings` reads no file.

#### Two orders

- **Given** the config and the rules of AC-2 to AC-7 declared in two orders, and
  no file system.
- **When** `check_warnings` runs on each.
- **Then** the results are equal and no warning is repeated.

### **AC-9** A ruleset that was left out gives no warning

An entry that names a ruleset that the discovery left out for its own fault gets
no warning about reach.

#### A ruleset left out

- **Given** a ruleset `broken` whose manifest does not parse, which the
  discovery leaves out, and a stage that includes `broken.ARC001`.
- **When** `check_warnings` runs.
- **Then** it returns no warning for that entry.

## Additional context

- The concepts call a selection that no root reaches a "dead" reference, because
  the layers select its rules and the roots then always cut them; this contract
  calls it by what it is, so that the message can say what to do.
- A rule that nothing selects is not a fault, so it is listed by
  `wio rules list --not-selected`, as the top Work says in AC-12.
- The line of a heading is `body_line` of the `Rule` plus the heading's line in
  the body, which is why `ht39xt` gives a `Rule` that field.
