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
  joined by the configured separator, inserted as written, `"\n\n"` by default.
- A rule is named by its ruleset's canonical name and never by a bare code.
- The text of a rule does not say why it was selected.

## Non-Goals

- The order and the grouping of the items, and the text of the group and family
  lines, which their Works do; this Work takes them as given, so it does not
  depend on them.
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

### A-3

Where the concepts and the scope document put the configured separator between
rules, it is right to read it as between every item of the rules section, and
the docs stage corrects both documents and the description of
`Bundle.separator`, which says "the text between the parts of a bundle".

## Mechanisms

- **The rule's text** — `<ruleset>.<CODE> <name>`, a `"\n"` and the body,
  such as `mattpocock.ERR003 errors-carry-context`; a rule with an empty body is
  its line alone, with no trailing line ending.
- **The separator** — `separator` of the config's bundle settings, `"\n\n"` by
  default.
- **The rendering of a rule** — provisional: a function of the rule alone,
  `render_rule(rule: Rule) -> str`.

## Acceptance criteria

### **AC-1** A rule is its qualified line and its body

The rule's text is the line with its canonical ruleset name, its code and its
name, one line ending `"\n"`, and then its body as the reader returns it, and
nothing else, so it says nothing of why the rule was selected; a rule with an
empty body is the line alone.

#### A rule with two paragraphs, and an empty body

- **Given** a rule `ERR003` named `errors-carry-context` in the ruleset
  `mattpocock`, whose body has two paragraphs, and a rule with an empty body.
- **When** each is rendered.
- **Then** the first is `mattpocock.ERR003 errors-carry-context`, one line
  ending and the body unchanged, and the second is its line with no line ending
  after it.

### **AC-2** Every item is joined by the separator as written

The group lines, the family lines and the rules of a section are joined by the
configured separator, inserted as written between every two adjacent items and
not before the first or after the last, and by `"\n\n"` when none is set.

#### Default and configured

- **Given** the items `Rules for root api (services/api):`,
  `mattpocock: Error handling (ERR)` and two rules, with one config that sets no
  separator and one that sets `"\n---\n"`.
- **When** they are joined.
- **Then** the first has `"\n\n"` between every two items and the second has
  `"\n---\n"` between every two, so the group line is separated from the family
  line by `"\n---\n"` too, and neither begins or ends with the separator.
