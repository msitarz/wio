<!-- wio
id = "yahzr6"
template = "feature.leaf"
roots = ["wio"]
depends_on = []
-->

# Ordering and topics

## Purpose

The rules of a group must be in an order that nothing but their names decides,
and a reader needs to see which topic a family of rules is about.

## Goals

- The rules of a group are ordered by ruleset, then family, then code.
- Each family is introduced in a group once by a line with its ruleset, its
  topic and its letters.
- A rule is placed by its family, never by the rule preset that brought it.

## Non-Goals

- Grouping by roots, which the grouping does.
- Printing the rule, which the rendering does.

## Assumptions

### A-1

The manifest of a ruleset gives a topic for every family that one of its rules
uses, which the discovery of the rules in `wio.rules` guarantees by rejecting a
rule whose family the manifest does not declare.

### A-2

The topic of each family reaches `wio.context` through a port that `wio.rules`
satisfies from its manifests, because a `Selection` holds rules and decisions
and no topic.

## Mechanisms

The concepts give `mattpocock: Error handling (ERR)` as the form of a family
line, which is binding; any other wording is provisional.

- **The family line** — `<ruleset>: <topic> (<FAMILY>)`, with the canonical name
  of the ruleset and the topic from its manifest.
- **The order of codes** — by the number of the code and then by its text, so
  `ARC999` comes before `ARC1000` and `ARC001` before `ARC01`, as `wio rules`
  orders them.

## Acceptance criteria

### **AC-1** The order depends only on names

Within a group the rules are ordered by the name of their ruleset, then by
family, then by the number of the code and then its text, whatever the order in
which the group is given.

#### Two rulesets, codes that a text sort misorders, and an unsorted group

- **Given** in one group, in this order, the rules `python.API002`,
  `mattpocock.ERR010`, `mattpocock.ERR002`, `python.API001`,
  `mattpocock.ARC1000`, `mattpocock.ARC01`, `mattpocock.ARC999` and
  `mattpocock.ARC001`.
- **When** the group is ordered.
- **Then** the order is `mattpocock.ARC001`, `mattpocock.ARC01`,
  `mattpocock.ARC999`, `mattpocock.ARC1000`, `mattpocock.ERR002`,
  `mattpocock.ERR010`, `python.API001`, `python.API002`.

### **AC-2** A family has one topic line in a group

The first rule of a family in a group is preceded by the family line, and no
other rule of that family in the group is.

#### Two families

- **Given** the rules `mattpocock.ERR002`, `mattpocock.ERR010` and
  `mattpocock.ARC001` in one group, and a manifest whose topics are
  `Error handling` for `ERR` and `Architecture` for `ARC`.
- **When** the group is ordered.
- **Then** `mattpocock: Architecture (ARC)` precedes `mattpocock.ARC001`, and
  `mattpocock: Error handling (ERR)` precedes `mattpocock.ERR002` and appears
  once.

### **AC-3** The route of a rule moves nothing

The order and the family lines do not change when a rule reaches the selection
through another rule preset or with other layer effects.

#### Two selections that differ only in how the rules were selected

- **Given** two selections that include the same rules, one through a rule
  preset `recommended` and one through a rule preset `strict`, so that the
  routes and the layer effects of their decisions differ.
- **When** the group is ordered for each.
- **Then** the two orders and the family lines are equal.
