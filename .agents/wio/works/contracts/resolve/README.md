<!-- wio
id = "h3jhtw"
template = "feature.leaf"
roots = ["wio"]
depends_on = ["ces6tf"]
-->

# The resolved view of a Work

## Purpose

An agent should read one view of a Work that holds what its ancestors pass on,
and never open a whole parent contract. How the inherited sections sit next to
the Work's own must be settled once, so that `wio contracts show` and the
context bundle that comes later print the same text.

## Goals

- The resolved view of a Work is known: its own contract and the inheritable
  sections of its ancestors.
- An inherited section cannot be mistaken for one of the Work's own: each is
  named by the ancestor it comes from.
- Every command that shows a Work shows the same text for it.

## Glossary

- **Inherited section**: a `##` section of an ancestor that the directive source
  of that ancestor marks `inherit`.
- **Directive source**: the template an ancestor names, or its own headings when
  it names none.

## Non-Goals

- Marking an individual item inheritable, and tracing items of a parent.
- The header of a bundle, the stage's goal and the rules, which `wio context`
  adds.
- Judging an ancestor's sections, which the check-body leaf does, and its
  template, which `wio templates check` does.
- Printing the actions, roots and dependents of a Work, which the show leaf
  adds.

## Assumptions

- **A-1**: The hierarchy leaf is delivered, so the ancestors of a Work come
  nearest first.
- **A-2**: The template catalog gives the template of a name, with its path, or
  none, and the template's file is read through `FileSystem`.
- **A-3**: `read_outline` gives the real headings of a body with their raw
  lines, and `read_directive_heading` reads the directives of a heading line, as
  they are delivered.

## Mechanisms

- `ResolvedContract` in `wio.models`, which replaces its stub with the Work and
  the inherited sections of each ancestor that passes any.
- A function in `wio.contracts` that resolves a Work, and one that renders the
  view as text, with names and signatures that the architecture stage decides.
- The ancestors of the hierarchy leaf, the template catalog port, the
  `FileSystem` port, `read_metadata_block`, `read_outline` and
  `read_directive_heading`.

## Constraints

- **The layout is one document.** The Work's own contract comes first, with the
  metadata block and the directive comments taken off its headings and every
  other comment kept. Then comes one `##` section for each ancestor that passes
  anything, nearest first, titled `Inherited from: <title> (<id>)`, holding that
  ancestor's inherited sections in the ancestor's order, each demoted by one
  level and never below level 6.
- **An ancestor's source decides.** Its template's directives, found through the
  catalog and matched to its `##` sections by text, ignoring case, surrounding
  space and a trailing directive comment, or its own headings' directives when
  it names no template. Only level-2 sections inherit, and a section runs to the
  next heading of level 2 or above.
- **Nothing is invented.** An ancestor whose template is missing or rejected
  passes nothing, the walk goes on to the ancestors above it, and no error is
  raised. A section that holds only comments and whitespace is not passed.
- **Own sections stay own.** The Work's own sections are not repeated, and the
  items of an inherited section are not the Work's items.
- **The output is deterministic.** Line endings are LF and the same Work gives
  the same text on every run.
- **Nothing is written.** Files are read through `FileSystem` only.

## Acceptance criteria

### **AC-1** The view holds the Work and what its parent passes on

The resolved view is the Work's own contract followed by a section named for its
parent that holds the parent's inheritable sections, demoted by one level.

#### A child of a parent

- **Given** `hierarchy = "nesting"`, a parent titled `Parent` with the id
  `p5n2hv` from a template that marks `Glossary` and `Constraints` `inherit`,
  whose contract has `## Purpose`, `## Glossary`, `## Constraints` with a
  `### Detail` heading under it, and a child titled `Child` that has its own
  `## Purpose` and `## Constraints`.
- **When** the view of the child is rendered.
- **Then** it is the child's contract as written, then `## Inherited from:
  Parent (p5n2hv)` holding `### Glossary`, `### Constraints` and
  `#### Detail` with the parent's text, and it holds the parent's `## Purpose`
  nowhere.

### **AC-2** Ancestors come nearest first and the ones that pass nothing are skipped

Through several levels the sections of the nearest ancestor come first, an
ancestor that passes nothing has no section, and a Work without a parent has
none.

#### Three levels

- **Given** a grandparent `g` with an inheritable `## Constraints`, a parent `p`
  whose source marks nothing, and a child `c`, and a Work `solo` with no parent.
- **When** the views of `c` and `solo` are rendered.
- **Then** the view of `c` has one `## Inherited from:` section, for `g`, and
  that of `solo` is its own contract only.

#### Two ancestors that pass

- **Given** `g` and `p` that both mark `## Constraints` inheritable.
- **When** the view of `c` is rendered.
- **Then** the section for `p` comes before the one for `g`.

#### Under flat

- **Given** `hierarchy = "flat"` and Works in the same directories.
- **When** their views are rendered.
- **Then** each is its own contract only.

### **AC-3** The directive source is the template or the ancestor's own headings

An ancestor passes the sections its template marks, matched by text, or, with no
template, the sections its own headings mark.

#### A template and a text match

- **Given** an ancestor from a template that marks `## Constraints`
  `inherit`, whose contract writes `## constraints` in other case and with a
  trailing space, and carries a stray `<!-- wio: inherit -->` on `## Purpose`.
- **When** the view of its child is rendered.
- **Then** the child's view holds `### constraints` and does not hold the
  Purpose.

#### No template

- **Given** an ancestor that names no template and has
  `## Rules <!-- wio: inherit -->` and `## Notes`.
- **When** the view of its child is rendered.
- **Then** it holds `### Rules` without its directive comment and no `Notes`.

### **AC-4** A template that cannot be used passes nothing and stops nothing

An ancestor whose template is missing from the catalog or cannot be read passes
nothing, and the ancestors above it still pass theirs.

#### A missing template and a bad file

- **Given** a grandparent `g` with an inheritable `## Constraints` that has two
  children, a parent `a` that names a template the catalog does not have and a
  parent `b` whose template file is not UTF-8, and a child under each, `c1`
  under `a` and `c2` under `b`.
- **When** the views of `c1` and `c2` are rendered.
- **Then** each view is the child's own contract plus one `## Inherited from:`
  section, for `g`, and nothing is raised.

### **AC-5** The text is cleaned and the same every time

The metadata block and the directive comments are taken off, other comments are
kept, a section with no content is not passed, and the text is the same on every
run, with LF endings.

#### Cleaning

- **Given** a child with `+++` front matter, an authoring comment that quotes
  `## X <!-- wio: required -->`, and a heading `## Goals <!-- wio: required -->`
  in a file with CRLF endings, and a parent whose inheritable `## Glossary`
  holds only a comment and whose `## Constraints` holds a line and a comment.
- **When** the view of the child is rendered, and rendered again.
- **Then** the view has no `+++` block, `## Goals` without its comment, the
  quoting comment as written, no `Glossary`, `### Constraints` with its line and
  its comment, only LF endings, and the two results are equal.

#### A deep heading

- **Given** an inheritable section with a heading of level 6 under it.
- **When** the view of a child is rendered.
- **Then** that heading stays at level 6.

## Additional context

- [Inheritance, computed](../../../../../docs/concepts.md#inheritance-computed)
  says what an ancestor passes on, and this leaf settles the open point there on
  how the sections are rendered.
- The show leaf prints this view, and `wio context` will show it in a bundle
  through a port.
- A parent's Glossary and Constraints are inherited by this Work, so the term
  Resolved view is defined by its parent.
