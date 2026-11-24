<!-- wio
id = "yahzr6"
template = "feature.leaf"
roots = ["wio"]
depends_on = ["v2vecy"]
-->

# Ordering and topics

## Purpose

The rules of a group must be in an order that nothing but their names decides,
and a reader needs to see which topic a family of rules is about.

## Goals

- The rules of a group are ordered by ruleset, then family, then code.
- Each family is introduced once by a line with its ruleset, its topic and its
  letters.
- A rule is placed by its family, never by the rule preset that brought it.

## Non-Goals

- Grouping by roots, which the grouping does.
- Printing the rule, which the rendering does.

## Assumptions

### A-1

The manifest of a ruleset gives a topic for every family it declares, which the
`families` of its manifest holds.

## Mechanisms

The wording of the family line is provisional.

- **The family line** — `<ruleset>: <topic> (<FAMILY>)`, such as
  `mattpocock: Error handling (ERR)`.
- **The order of codes** — by the number of the code and then by its text, so
  `ARC999` comes before `ARC1000` and `ARC001` before `ARC01`, as `wio rules`
  orders them.

## Acceptance criteria

### **AC-1** The order depends only on names

Within a group the rules are ordered by the name of their ruleset, then by
family, then by the number of the code and then its text.

#### Two rulesets

- **Given** the rules `py.API002`, `mp.ERR010`, `mp.ERR002`, `py.API001` and
  `mp.ARC001` in one group.
- **When** the group is ordered.
- **Then** the order is `mp.ARC001`, `mp.ERR002`, `mp.ERR010`, `py.API001`,
  `py.API002`.

### **AC-2** A family has one topic line

The first rule of a family is preceded by the family line, and no other rule is.

#### Two families

- **Given** the rules `mp.ERR002`, `mp.ERR010` and `mp.ARC001` of a ruleset
  whose topics are `Error handling` for `ERR` and `Architecture` for `ARC`.
- **When** the group is ordered.
- **Then** `mp: Architecture (ARC)` precedes `mp.ARC001`, and
  `mp: Error handling (ERR)` precedes `mp.ERR002` and appears once.

### **AC-3** Moving a rule between rule presets moves nothing

The order and the family lines do not change when a rule reaches the selection
through another rule preset.

#### Two presets, one rule

- **Given** two configs that select the same rules, one through the rule preset
  `recommended` and one through `strict`.
- **When** the group is ordered for each.
- **Then** the two orders and the family lines are equal.
