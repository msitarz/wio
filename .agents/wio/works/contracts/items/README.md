<!-- wio
id = "7anq34"
template = "feature.leaf"
roots = ["wio"]
depends_on = []
-->

# Items of a section

## Purpose

A contract's items, such as its criteria, carry ids that records and reviews
cite, so every command that reads a contract must find the items of a section
and their ids by one rule. The directive grammar says only that a section holds
items and that a pattern gives their ids, and leaves what counts as an item to
this Work.

## Goals

- The items of a section are found by one rule, from the Markdown of the body.
- The id of an item is found by its section's `pattern`.
- A contract's items are judged: their number, their ids, and the uniqueness of
  the ids.
- The rule lives in `wio.formats`, so `wio contracts check` and, later,
  `wio trailers` use the same one.

## Glossary

- **Item**: a heading one level below its section when the section has one,
  and otherwise a top-level list item of the section, bulleted or numbered.
- **Item text**: the Markdown of an item as written: a heading's text, or the
  first line of a list item after its marker.
- **Id**: the match of the section's `pattern` at the start of the item text.
  The start is the first character that is not `*`, `_`, a backtick or a space.

## Non-Goals

- Reading the directives of a template or a contract, and matching a contract's
  sections to a template's, which the check-body leaf does.
- Judging whether the ids cited by a record exist or are covered, which
  `wio trailers` and a workflow do.
- Items of other shapes, such as table rows, nested list items or the headings
  two levels below a section.
- A directive that says which shape the items have, or flags for a pattern.
- Marking an item inheritable and tracking items of a parent.

## Assumptions

- **A-1**: The directive parser returns `Items` and `Pattern` for a heading, and
  `read_outline` returns the real headings of a body with their lines, as they
  are delivered.
- **A-2**: The Markdown parser that `read_outline` uses reports a top-level list
  item and its line, keeps the source text of an inline, and reports a list in a
  quote, a code block or a comment as something else than a top-level list.

## Mechanisms

- A finder of the items of one section in `wio.formats`, which takes the body,
  its start line, the section's heading and its directives and returns the
  items, each with its text, its id or none, and its line.
- A judge of a contract's items in `wio.formats`, which takes the sections with
  their items and directives and returns diagnostics.
- `read_outline` of `wio.formats`, whose headings give the extent of a section
  and the headings that are its items, and its Markdown parser, whose tokens
  give the list items.
- `wio.models`, which gains the item type, and which already holds `Items`,
  `Pattern` and `Heading`.
- The names and the signatures above are provisional, for the architecture
  stage to decide.

## Constraints

- **One rule.** Only `wio.formats` finds items, and no other package derives
  them from the Markdown again.
- **A section runs to the next heading of level 2 or above.** Its items are its
  headings one level below it, and only when it has none, its top-level list
  items. A list item is one item with its nested lists and paragraphs.
- **Only the content of the body counts.** An HTML comment, a code block and a
  quote hold no items, so the authoring example of a template is never counted.
- **The id is exactly the match.** It is not trimmed or changed in case, and an
  item without a match at its start has no id.
- **Every finding is an error at the line of the item.** Every error names the
  item, its section and the directive that it breaks, and the finder and the
  judge give the same order for the same body.
- **Nothing is imported before it is needed.** The Markdown parser loads on the
  first call, as `read_outline` does, and no module outside `wio.formats`
  imports it.

## Acceptance criteria

### **AC-1** The items of a section are its subheadings, or else its list items

The finder returns the headings one level below a section when it has some, and
otherwise the top-level list items, each with its text and its line in the file.

#### Subheadings win

- **Given** a body, starting at line 10 of a file, with `## Acceptance criteria`
  holding an intro bullet `- intro`, `### **AC-1** First`, a `#### Scenario`
  heading, and `### **AC-2** Second`, followed by `## Next` with a `### X`.
- **When** the items of `## Acceptance criteria` are found.
- **Then** they are `**AC-1** First` and `**AC-2** Second`, each at its line of
  the file, and the intro bullet, the `####` heading and `### X` are not items.

#### List items

- **Given** a body whose `## Goals` holds `- one` with a nested `- sub`,
  `1. two`, a quoted `> - quoted`, a comment that holds `- hidden`, and a fenced
  block that holds `- code`, in a file with CRLF line endings.
- **When** the items of `## Goals` are found.
- **Then** they are `one` and `two`, each at its line, and nothing else.

#### No items

- **Given** a section that holds only prose, and one that holds only an
  authoring comment.
- **When** the items of each are found.
- **Then** both have none.

### **AC-2** The id is the pattern's match at the start of the item text

An item has an id when the section's pattern matches at the start of its text,
after leading `*`, `_`, backticks and spaces.

#### Where the id is

- **Given** the pattern `AC-\d+` and items `**AC-1** First`, `` `AC-2` Second``,
  `Replaces AC-3`, `AC-12 twelve` and `First AC-4`.
- **When** the items are found.
- **Then** the ids are `AC-1`, `AC-2`, none, `AC-12` and none.

#### A list item

- **Given** the pattern `A-\d+` and the list items `- **A-1**: first` and
  `2. A-2 second`.
- **When** the items are found.
- **Then** the ids are `A-1` and `A-2`.

#### No pattern

- **Given** a section with items and no pattern.
- **When** the items are found.
- **Then** none has an id.

### **AC-3** The number of items and the missing ids are errors

A section with fewer items than `items>=N`, and an item without an id in a
section that has a pattern, are errors at the line they belong to.

#### Too few

- **Given** `items>=3` on a section with two items, and `items>=1` on a section
  that holds only an authoring comment.
- **When** the items are judged.
- **Then** each is an error at its section's heading that says how many items
  the section holds and how many it needs.

#### An item without an id

- **Given** the pattern `AC-\d+` on a section whose second item is
  `Replaces AC-3`.
- **When** the items are judged.
- **Then** there is one error at that item's line that says it has no id
  matching `AC-\d+`, and none for the others.

#### Unmarked items are free

- **Given** a section with items and neither `items` nor `pattern`.
- **When** the items are judged.
- **Then** there is no diagnostic.

### **AC-4** Ids are unique and hold no whitespace or comma

An id that appears twice in a contract, in one section or in two, and an id that
holds whitespace or a comma, are errors.

#### A repeated id

- **Given** the pattern `AC-\d+` and `AC-1` on two items of one section and on
  an item of `## Other`, which has the same pattern.
- **When** the items are judged.
- **Then** one error names `AC-1` and the three lines it is on.

#### A bad id

- **Given** the patterns `AC \d` and `A,\d`, and the items `AC 1` and `A,1`.
- **When** the items are judged.
- **Then** each is an error at its item's line that says the id holds
  whitespace or a comma.

### **AC-5** The Markdown parser loads on first use

Importing `wio.formats` does not import the Markdown parser, and finding items
does.

#### A fresh interpreter

- **Given** a new Python process.
- **When** `wio.formats` is imported and `sys.modules` is read, then the items
  of a section are found and it is read again.
- **Then** `markdown_it` is not there the first time and is there the second.

## Additional context

- [Item ids](../../../../../docs/concepts.md#item-ids) in the concepts say what
  an id is for, and this leaf settles the open point there on how items are
  found.
- The check-body leaf calls the finder and the judge with the sections and
  directives of a contract. `wio trailers` will use the ids to check what a
  record cites.
