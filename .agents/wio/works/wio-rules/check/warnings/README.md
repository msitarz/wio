<!-- wio
id = "785y9k"
template = "feature.leaf"
roots = ["wio"]
depends_on = ["cm25z9"]
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
- A warning says what is wrong and how to fix it, and is placed at the key or
  the file the author has to edit.
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
any root of the config.

## Mechanisms

The names of the functions below are provisional.

- **`check_warnings(config, discovery) -> tuple[Diagnostic, ...]`** — in
  `wio.rules`, with the `Config` and the `Discovery` of `8zn10d`; it does no
  input or output.
- **The rulesets an entry names** — the `rulesets` of the `Expansion` that
  `expand` of `cyeth5` returns for an entry, nested rule presets included.
- **The reach of the roots** — `reach` of `apply_layers` of `cm25z9`, and the
  `root_independent` setting of each ruleset in the config.
- **The headings of a body** — `read_outline` of `wio.formats`, which finds the
  real headings of a Markdown body and ignores those in code, comments, quotes
  and lists.

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

An entry in a stage's `rules_include` or in `rules_always_include` that names a
ruleset that is not root-independent, and that none of the roots the stage
selects reaches, is one warning at the entry's key path, which names the ruleset
and says how to fix it.

#### Stages and always fields

- **Given** a root `api` that reaches `demo`, a ruleset `py` that is not
  root-independent and that no root reaches, a root-independent ruleset
  `process`, a stage `s` with no `roots` and a stage `t` with `roots = ["api"]`
  that each include `py.review`, a stage `u` with `roots = []` and a stage `w`
  with `roots = ["web"]`, where `web` reaches nothing, that each include
  `demo.ARC`, and `rules_always_include` with `py.FIX` and `process.all`.
- **When** `check_warnings` runs.
- **Then** it returns warnings at `stages.s.rules_include[0]`,
  `stages.t.rules_include[0]`, `stages.u.rules_include[0]`,
  `stages.w.rules_include[0]` and `rules_always_include[0]`, none for the
  entries that name `process`, and each message names the ruleset, says that it
  is not root-independent and that none of the roots reaches it, and says to
  mark it `root_independent` or to name it in a root's `rule_presets`.

### **AC-3** A stage that selects the Work's roots is judged against every root

A stage with no `roots`, or with `@work` among them, counts a ruleset as reached
when any root of the config reaches it.

#### Any root

- **Given** a root `api` that reaches `demo` and no root that reaches `py`, a
  stage `v` with `roots = ["contract", "@work"]` that includes `demo.ARC` and
  `py.review`.
- **When** `check_warnings` runs.
- **Then** it returns one warning at `stages.v.rules_include[1]` for `py` and
  none for `demo.ARC`.

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

### **AC-6** A rule that both always fields name is a warning

An entry of `rules_always_include` whose rules an entry of
`rules_always_exclude` vetoes is one warning at the include entry, which names
the exclude entry and the rules, and says that the veto wins.

#### An include and an exclude

- **Given** `rules_always_include = ["demo.ARC", "demo.PAY001"]` and
  `rules_always_exclude = ["demo.ARC001", "demo.ARC002"]`, in a ruleset `demo`
  that holds `ARC001`, `ARC002`, `ARC003` and `PAY001`.
- **When** `check_warnings` runs.
- **Then** it returns one warning at `rules_always_include[0]` that names the
  exclude entries and `demo.ARC001` and `demo.ARC002`, in that order, and that
  the veto wins, and none for `rules_always_include[1]`.

### **AC-7** A heading in a rule's body is a warning

A rule whose body has a real Markdown heading is one warning at its file, which
names the heading, and a heading in code is not one.

#### Real headings only

- **Given** a rule `demo.ARC001` whose body has `## Notes`, a rule `demo.ARC002`
  whose body has `# not a heading` in a fenced code block, and a rule in the
  `+++` front matter form whose body has a real heading.
- **When** `check_warnings` runs.
- **Then** it returns one warning for each rule with a real heading, at the
  rule's file, that names the heading text, none for `demo.ARC002`, and it does
  not matter which block form the rule has.

### **AC-8** The warnings are reported once and do not depend on order

Each warning is returned once, in the shared order, whatever the order of the
tables and entries, and `check_warnings` reads no file.

#### Two orders

- **Given** the config and the rules of AC-2 to AC-7 declared in two orders, and
  no file system.
- **When** `check_warnings` runs on each.
- **Then** the results are equal and no warning is repeated.

## Additional context

- The concepts call a selection that no root reaches a "dead" reference, because
  the layers select its rules and the roots then always cut them; this contract
  calls it by what it is, so that the message can say what to do.
- A rule that nothing selects is not a fault, so it is listed by
  `wio rules list --not-selected`, as the top Work says in AC-12.
