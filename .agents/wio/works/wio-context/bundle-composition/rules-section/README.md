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
- Labelling the section and joining it to the other parts of the bundle, which
  the assembly does.

## Assumptions

None.

## Mechanisms

The names below are provisional.

- **The rules section builder** — in `wio.context`, which turns a `Selection`
  into the text of the section by the three children below.
- **`Selection` and `Decision`** — in `wio.models.rules`, which hold every rule
  considered, with the roots of an included rule or the reason a rule is out.
- **The topics of the families** — in the manifest of each ruleset, which the
  ordering reads.

## Visuals

Before, a selection is a map of rules to decisions. After, the rules that apply
become one section: the grouping places each rule under the roots that reach it,
the ordering sorts each group, and the rendering prints each rule.

## Acceptance criteria

### **AC-1** A selection becomes one section

Each included rule of a selection appears once in the section, grouped by the
roots that reach it, ordered and rendered as the children specify.

#### Rules of every kind of reach

- **Given** a selection that includes a root-independent rule, a rule that one
  root reaches and a rule that two roots reach.
- **When** the section is built.
- **Then** each of the three rules appears exactly once, and the section equals
  the one that the grouping, the ordering and the rendering give for them.
