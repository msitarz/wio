<!-- wio
id = "4h73tb"
template = "feature.parent"
roots = ["@descendants"]
depends_on = []
-->

# Rules section

## Purpose

The rules that a stage selects reach the session only as a selection, so nothing
yet groups them by where they apply, puts them in a fixed order and prints them
as written.

## Goals

- The rules that apply to a stage are printed grouped by the roots they apply
  to.
- The rules of a group are in an order that depends only on their names.
- Each rule is printed with its qualified name and its body as written.

## Non-Goals

- Selecting the rules, which `wio rules` does.
- Saying why a rule was selected, which `wio rules list --explain` does.

## Assumptions

None.

## Visuals

Before, a selection is a map of rules to decisions. After, the rules that apply
become one section: the grouping places each rule under the roots that reach it,
the ordering sorts each group, and the rendering prints each rule.

## Acceptance criteria

### **AC-1** A selection becomes one section

The included rules of a selection are printed under the groups of their roots,
the rules for every root first, in the order of their names, each with its
family's topic, its qualified name and its body.

#### Four rules in two rulesets

- **Given** a selection that includes a root-independent rule, a rule of the
  root `api`, a rule of the root `web` and a rule that both `api` and `web`
  reach.
- **When** the section is built.
- **Then** the groups are `Rules for every root:`, then the group of `api`, then
  that of `api` and `web`, then that of `web`, as the grouping orders them, and
  each rule is once in its group, in the order and the form of the ordering and
  the rendering.

### **AC-2** A rule that is out never appears

A rule that the selection excludes, vetoes, cuts by the roots or did not select
is not in the section, and no rule means an empty section.

#### Excluded rules, and no included rule

- **Given** a selection with one rule of each kind of out and none included.
- **When** the section is built.
- **Then** the section is empty and prints no label and no group.
