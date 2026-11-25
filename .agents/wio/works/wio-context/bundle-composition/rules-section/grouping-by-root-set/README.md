<!-- wio
id = "v2vecy"
template = "feature.leaf"
roots = ["wio"]
depends_on = []
-->

# Grouping by root set

## Purpose

A rule applies to the roots that reach its ruleset, and a session reads the
rules for its code best when it can see which roots and paths each group is
about.

## Goals

- The rules that need no root come first, under one line that says so.
- The other rules are grouped by the exact set of roots they apply to, each
  group under one line that names the roots and the paths they have.
- The groups are in an order that depends only on the names of their roots.
- A rule is in one group, however many roots reach its ruleset.
- Only the rules that apply are grouped.

## Non-Goals

- The order of the rules inside a group, which the ordering does.
- The text of a rule, which the rendering does.
- The label of the section, which the assembly does.

## Assumptions

### A-1

A `Decision` of an included rule holds the roots that were applied and that
[reach](../../../../../../../src/wio/rules/GLOSSARY.md) its ruleset, sorted by
name, and is empty for a root-independent rule, and a Work with no roots gets a
selection that includes no rule, as the selector gives it, so it gives no group;
the link says what reach is, because the glossary binds only its own directory.

### A-2

The paths of a root come from the config.

### A-3

A root may have no path, because the config requires the `paths` key for a root
and accepts an empty list, and such a root is a named set of rules.

### A-4

Where
[the concepts](../../../../../../../docs/concepts.md#11-the-context-compiler)
and the scope document say that a group line names the roots and their paths, it
is right for a line to show the paths that its roots have and none when they
have none, and the docs stage corrects both documents.

## Mechanisms

The concepts fix `Rules for every root:` and the form of
`Rules for root api (services/api):`; the group line for several roots is
provisional, and the criteria below quote it in that provisional form. What is
binding is that a group line names the roots and the paths they have.

- **The group line for no root** — `Rules for every root:`.
- **The group line for roots** — `Rules for root <name> (<paths>):` for one root
  and `Rules for roots <name>, <name> (<paths>):` for several, where the paths
  are those of the roots in the order of their names, joined by `, `.
- **The group line for roots with no path** — `Rules for root <name>:` and
  `Rules for roots <name>, <name>:`, without parentheses, when none of the
  group's roots has a path.

## Acceptance criteria

### **AC-1** Rules that need no root come first

The rules of root-independent rulesets are the first group, under
`Rules for every root:`, and there is no such line when there are none.

#### With and without

- **Given** a selection with a root-independent rule and a rule of `api`, and
  another with the rule of `api` only.
- **When** the groups are built.
- **Then** the first begins with `Rules for every root:` and then
  `Rules for root api (services/api):`, and the second has no
  `Rules for every root:` line.

### **AC-2** A group is the exact set of roots

Rules that apply to the same set of roots share a group, and a rule that two
roots reach is in the group of both.

#### One root and two roots

- **Given** rules of `api`, rules of `web`, and rules that both reach.
- **When** the groups are built.
- **Then** there are three groups, one for `api` at `services/api`, one for
  `api` and `web` at `services/api, apps/web`, and one for `web` at `apps/web`,
  in the provisional wording of their lines, and each rule is in exactly one.

### **AC-3** The order does not depend on the config

The groups are sorted by their root names, compared as tuples element by
element with a shorter prefix first, and the paths of a group are in the order
of the roots' names and then, for one root, of the config, whatever the order of
the config's tables.

#### Two orders, and a root with two paths

- **Given** the same selection with the roots declared in two orders in the
  config, a root `web` whose paths are `apps/web` and `apps/admin` in that
  order, and a root `api` at `services/api`, with `web` declared before `api` in
  one of the configs.
- **When** the groups are built from each.
- **Then** both give the same groups in the same order, and the line of the
  group of both roots is
  `Rules for roots api, web (services/api, apps/web, apps/admin):` in the
  provisional wording.

### **AC-4** Only the rules that apply are grouped

A rule that the selection excludes, vetoes, cuts by the roots or did not select
is in no group, and a selection that includes no rule gives no group.

#### Four ways out, and none included

- **Given** a selection with one rule of each way out and no included rule, and
  another that adds one included rule.
- **When** the groups are built.
- **Then** the first gives no group, and the second gives one group that holds
  only the included rule.

### **AC-5** A root with no path is named alone

A group line names every root of the group and shows the paths of those that
have one, and has no parentheses when none of them has a path.

#### Roots with and without a path

- **Given** a root `api` at `services/api`, roots `x` and `y` whose `paths` are
  empty, and rules that apply to `x`, to `x` and `y`, and to `api` and `x`.
- **When** the groups are built.
- **Then** their lines are `Rules for roots api, x (services/api):`,
  `Rules for root x:` and `Rules for roots x, y:`, in that order and in the
  provisional wording.
