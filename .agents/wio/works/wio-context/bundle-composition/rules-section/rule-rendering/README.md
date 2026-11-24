<!-- wio
id = "np51h3"
template = "feature.leaf"
roots = ["wio"]
depends_on = []
-->

# Rule rendering

## Purpose

A session must read each rule as its author wrote it and cite it by a name that
no other rule shares, and the section must join its group lines, family lines
and rules in one way that a project can configure.

## Goals

- Each rule is a line with its qualified canonical name and its name, followed
  by its body as the rules reader returns it.
- The items of the rules section, its group lines, family lines and rules, are
  joined by the configured separator, a blank line by default.
- A rule is named by its ruleset's canonical name and never by a bare code.
- The text of a rule does not say why it was selected.

## Non-Goals

- The order and the grouping of the items, and the text of the group and family
  lines, which their Works do.
- Joining the parts of the bundle, which the assembly does with a blank line of
  its own.
- Explaining a selection, which `wio rules list --explain` does.

## Assumptions

### A-1

The body of a rule is `Rule.body`, the body of its file without the blank lines
at its start and end and without the final line ending, which is what "as
written" means in the concepts.

### A-2

`Rule.ruleset` is the canonical name of the ruleset, so a rule is never given an
alias to print.

## Mechanisms

- **The rule's line** — `<ruleset>.<CODE> <name>`, such as
  `mattpocock.ERR003 errors-carry-context`.
- **The separator** — `separator` of the config's bundle settings, `"\n\n"` by
  default.

## Acceptance criteria

### **AC-1** A rule is its qualified line and its body

The rule's text is the line with its canonical ruleset name, its code and its
name, and then its body as the reader returns it.

#### A rule with two paragraphs

- **Given** a rule `ERR003` named `errors-carry-context` in the ruleset
  `mattpocock`, whose body has two paragraphs.
- **When** it is rendered.
- **Then** the first line is `mattpocock.ERR003 errors-carry-context` and the
  body follows unchanged.

### **AC-2** Every item is joined by the separator

The group lines, the family lines and the rules of a section are joined by the
configured separator, and by a blank line when none is set.

#### Default and configured

- **Given** the items `Rules for root api (services/api):`,
  `mattpocock: Error handling (ERR)` and two rules, with one config that sets no
  separator and one that sets `---`.
- **When** they are joined.
- **Then** the first puts a blank line between every two items and the second
  puts `---` between every two.

### **AC-3** The text does not depend on why a rule was selected

A rule is rendered from the rule alone, so the same rule with another decision
gives the same text.

#### Two decisions

- **Given** the same rule included through two different routes.
- **When** it is rendered for each.
- **Then** the two texts are equal.

## Additional context

- The description of `Bundle.separator` in `wio.models.config` says "the text
  between the parts of a bundle", while the concepts and the scope document put
  the separator between rules. This Work gives the setting the meaning of the
  concepts, for the items of the rules section, and the assembly joins the parts
  of the bundle with its own blank line.
