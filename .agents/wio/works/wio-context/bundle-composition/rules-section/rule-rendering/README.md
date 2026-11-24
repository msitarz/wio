<!-- wio
id = "np51h3"
template = "feature.leaf"
roots = ["wio"]
depends_on = ["yahzr6"]
-->

# Rule rendering

## Purpose

A session must read each rule as its author wrote it and cite it by a name that
no other rule shares, and the bundle must not clutter the rule with why it was
selected.

## Goals

- Each rule is a line with its qualified canonical name and its name, followed
  by its body exactly as written.
- Rules are separated by the configured separator, a blank line by default.
- A rule is never named by its ruleset's alias or by a bare code.
- The bundle does not say why a rule was selected.

## Non-Goals

- The order and the grouping of the rules, which their Works do.
- Explaining a selection, which `wio rules list --explain` does.

## Assumptions

None.

## Mechanisms

- **The rule's line** — `<ruleset>.<CODE> <name>`, such as
  `mattpocock.ERR003 errors-carry-context`, with the ruleset's canonical name.
- **The separator** — `separator` of the config's bundle settings, `"\n\n"` by
  default.

## Acceptance criteria

### **AC-1** A rule is its qualified line and its body as written

The rule's text is the line with its canonical ruleset name, its code and its
name, and then its body byte for byte.

#### A rule with an alias

- **Given** a rule `ERR003` named `errors-carry-context` in the ruleset
  `mattpocock`, which the config aliases as `mp`, with a two-paragraph body.
- **When** it is rendered.
- **Then** the first line is `mattpocock.ERR003 errors-carry-context` and the
  body follows unchanged.

### **AC-2** Rules are joined by the separator

Rules are separated by the configured separator, and by a blank line when none
is set.

#### Default and configured

- **Given** two rules, one config with no separator and one with `---`.
- **When** they are rendered.
- **Then** the first separates them with a blank line and the second with the
  configured text.

### **AC-3** The rendering gives no reason

The rendering of a rule holds nothing about the layer, rule preset or root that
selected it, so the text is the same when the rule presets are reorganised.

#### Two routes

- **Given** the same rule selected through two different routes.
- **When** it is rendered for each.
- **Then** the two texts are equal.
