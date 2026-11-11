<!-- wio
id = "h3jhtw"
template = "feature.leaf"
roots = ["wio"]
depends_on = ["ces6tf", "sz1zsq"]
-->

# The resolved view of a Work

## Purpose

An agent should read one view of a Work that holds what its ancestors pass on,
and never open a whole parent contract. How the inherited sections sit next to
the Work's own must be settled once, and the text come from one function, so
that `wio contracts show` and the context bundle that comes later print the same
text.

## Goals

- The resolved view of a Work is known: its own contract and the inheritable
  sections of its ancestors.
- An inherited section cannot be mistaken for one of the Work's own: each is
  named by the ancestor it comes from.
- The view is one text, whose every byte is fixed by the Work's contract and its
  ancestors.

## Glossary

- **Inherited section**: a `##` section of an ancestor that the directive source
  of that ancestor marks `inherit`.
- **Directive source**: the template an ancestor names, or its own headings when
  it names none.

## Non-Goals

- Marking an individual item inheritable, and tracing items of a parent.
- The header of a bundle, the stage's goal and the rules, which `wio context`
  adds.
- Judging an ancestor's sections or a bad directive list, which the check-body
  leaf does, and an ancestor's template, which `wio templates check` does.
- Printing the actions, roots and dependents of a Work, which the show leaf
  adds.

## Assumptions

- **A-1**: The hierarchy leaf is delivered, so the ancestors of a Work come
  nearest first.
- **A-2**: The template catalog's `find` gives the template of a name, with its
  path, or none, and `is_rejected` says whether `wio templates check` rejects
  it. The template's file is read through `FileSystem`.
- **A-3**: `read_outline` gives the real headings of a body with their raw
  lines, and `read_directive_heading` reads the directives of a heading line, as
  they are delivered.

## Mechanisms

- `ResolvedContract` in `wio.models`, which replaces its stub with the Work and
  the inherited sections of each ancestor that passes any.
- A function in `wio.contracts` that resolves a Work, and one function that
  renders the view as text, with names and signatures that the architecture
  stage decides.
- The ancestors of the hierarchy leaf, the catalog's `find` and `is_rejected`,
  the `FileSystem` port and `Repository` for the root that paths are relative
  to, `read_metadata_block`, `read_outline`, `read_directive_heading` and
  `remove_directive_list`.

## Constraints

- **The layout is one document.** The Work's own contract comes first, without
  its metadata block and without the blank lines that followed it, and every
  comment is kept. Then, for each ancestor that passes anything, nearest first,
  come one blank line, the line `## Inherited from: <title> (<id>)` and one
  blank line, and then that ancestor's inherited sections in the ancestor's
  order, each demoted by one level and never below level 6, one blank line
  between them. A section is its heading line and its text without the blank
  lines that end it. The text ends in one line ending. An ancestor with no title
  is named `Inherited from: <id>`. An empty own contract leaves the view to
  begin with the first `## Inherited from:` line.
- **Directive comments are shown only when they cannot be read.** The directive
  list is taken off every heading of the view, the Work's and the ancestors',
  whatever its level, after `read_directive_heading` has read it. A list that it
  rejects is left in the heading as written, so `remove_directive_list` is not
  applied to it. The heading line is then right-trimmed.
- **An ancestor's source decides.** Its template's directives, found through the
  catalog and matched to its `##` sections by text, ignoring case, surrounding
  space and a trailing directive comment, or its own headings' directives when
  it names no template. Only level-2 sections inherit, a section runs to the
  next heading of level 1 or 2, and every section that matches a marked heading
  passes.
- **Nothing is invented.** An ancestor passes nothing when the catalog has no
  template of its name, when the template is rejected, when the template's file
  cannot be read, a `UnicodeDecodeError` or an `OSError` of `FileSystem`, or
  when the ancestor's own file cannot be read, the walk goes on to the ancestors
  above it, and no error is raised. A section that holds only comments and
  whitespace is not passed, and a deeper heading is content. A directive list
  that cannot be read marks nothing.
- **Own sections stay own.** The Work's own sections are not repeated, and the
  items of an inherited section are not the Work's items.
- **The output is deterministic.** Line endings are LF and the same Work gives
  the same text on every run.
- **Nothing is written.** Files are read through `FileSystem` only.

## Acceptance criteria

### **AC-1** The view holds the Work and what its parent passes on

The view is the Work's own contract followed by a section named for its parent
that holds the parent's inheritable sections, demoted by one level.

#### A child of a parent

- **Given** `hierarchy = "nesting"`, a parent titled `Parent` with the id
  `p5n2hv` from a template that marks `Glossary` and `Constraints` `inherit`,
  whose body is `# Parent`, `## Purpose` and the line `Why.`, `## Glossary` and
  the line `- **Term**: a word.`, and `## Constraints` and the line `A line.`
  with `### Detail` and the line `More.` under it, and a child with the body
  `# Child`, `## Purpose` and `Own text.`, and `## Constraints` and
  `Own constraint.`, each heading and each line separated by a blank line.
- **When** the view of the child is rendered.
- **Then** it is exactly this text, ending in one line ending:

  ```text
  # Child

  ## Purpose

  Own text.

  ## Constraints

  Own constraint.

  ## Inherited from: Parent (p5n2hv)

  ### Glossary

  - **Term**: a word.

  ### Constraints

  A line.

  #### Detail

  More.
  ```

### **AC-2** Ancestors come nearest first and the ones that pass nothing are skipped

Through several levels the sections of the nearest ancestor come first, an
ancestor that passes nothing has no section, and a Work without a parent has
none.

#### Three levels

- **Given** `hierarchy = "nesting"`, a stub catalog that has the template
  `t.marks`, which marks `## Constraints` inherit, and the template `t.plain`,
  which marks nothing, a grandparent `g/README.md` titled `G` that follows
  `t.marks` and has a `## Constraints`, a parent `g/p/README.md` that follows
  `t.plain`, a child `g/p/c/README.md`, and a Work `solo/README.md` with no
  parent.
- **When** the views of `c` and `solo` are rendered.
- **Then** the view of `c` has one `## Inherited from:` section, the one for
  `G`, and that of `solo` is its own contract only.

#### Two ancestors that pass

- **Given** the same tree with `p` following `t.marks` too, and having a
  `## Constraints`.
- **When** the view of `c` is rendered.
- **Then** the section for `p` comes before the one for `g`.

#### Under flat

- **Given** `hierarchy = "flat"` and the same tree, with `g` and `p` following
  `t.marks`.
- **When** the views of `g`, `p` and `c` are rendered.
- **Then** each is its own contract only.

### **AC-3** The directive source is the template or the ancestor's own headings

An ancestor passes the sections its template marks, matched by text, or, with no
template, the sections its own headings mark, and every section that matches
passes.

#### A template and a text match

- **Given** an ancestor from a template that marks `## Constraints`
  `inherit`, whose contract writes `## constraints` in other case and with a
  trailing space, and carries a stray `<!-- wio: inherit -->` on `## Purpose`.
- **When** the view of its child is rendered.
- **Then** the child's view holds `### constraints` and does not hold the
  Purpose.

#### No template and a repeated section

- **Given** an ancestor that names no template and has
  `## Rules <!-- wio: inherit -->` twice and `## Notes`.
- **When** the view of its child is rendered.
- **Then** it holds `### Rules` twice, in the ancestor's order and without the
  directive comment, and no `Notes`.

### **AC-4** A template that cannot be used passes nothing and stops nothing

An ancestor whose template is missing from the catalog, is rejected, or cannot
be read passes nothing, and the ancestors above it still pass theirs.

#### Three ancestors

- **Given** a stub catalog and a grandparent `g` with an inheritable
  `## Constraints` that has three children, `a` that names a template the stub
  does not have, `b` whose template the stub gives and `is_rejected` rejects,
  and `c` whose template the stub gives and does not reject but whose file, read
  through a fake `FileSystem`, raises a `UnicodeDecodeError`, and a child under
  each of them.
- **When** the three views are rendered.
- **Then** each view is the child's own contract plus one `## Inherited from:`
  section, for `g`, and nothing is raised.

### **AC-5** The text is cleaned and the same every time

The metadata block and the directive comments are taken off every heading, other
comments are kept, a section with no content is not passed, and the text is the
same on every run, with LF endings.

#### Cleaning

- **Given** a child with `+++` front matter, in a file with CRLF endings, whose
  body is `# Child`, the comment `<!-- Write ## X here. -->` and
  `## Goals <!-- wio: required -->` with the line `Goal text.`, each separated
  from the next by a blank line, and a parent titled `Parent` with the id
  `p5n2hv` from a template that marks `Glossary` and `Constraints` `inherit`,
  whose `## Glossary` holds only a comment, whose `## Constraints` holds the
  line `A line.` and the comment `<!-- c -->` with
  `### Detail <!-- wio: required -->` and the line `Deep.` under it, each
  separated from the next by a blank line, and whose `## Purpose` carries a
  stray `<!-- wio: inherit -->`.
- **When** the view of the child is rendered, and rendered again.
- **Then** both results are equal and exactly this text, with LF endings only:

  ```text
  # Child

  <!-- Write ## X here. -->

  ## Goals

  Goal text.

  ## Inherited from: Parent (p5n2hv)

  ### Constraints

  A line.

  <!-- c -->

  #### Detail

  Deep.
  ```

#### A deep heading and a bad list

- **Given** an ancestor from a template that marks `Constraints` and `Rules`
  inheritable, whose `## Constraints` holds a level-6 heading, and which has a
  heading `## Rules <!-- wio: mandatory -->`.
- **When** the view of a child is rendered.
- **Then** the level-6 heading stays at level 6, and the `Rules` section is
  passed with its bad directive list left in its heading as written.

### **AC-6** The name of an ancestor and the extent of a section

An ancestor with no title is named by its id, and a section runs to the next
heading of level 1 or 2, with a deeper heading as content.

#### No title and a section that holds a deeper heading

- **Given** a parent with the id `p5n2hv` and no heading at the top of its body,
  from a template that marks `Constraints` and `Notes` inheritable, whose
  `## Constraints` holds only `### Detail` and the line `More.`, then a `# Next`
  heading that ends it, and whose `## Notes` ends at the next `##`; and a child
  with an empty own contract.
- **When** the view of the child is rendered.
- **Then** it begins with `## Inherited from: p5n2hv`, holds `### Constraints`
  with `#### Detail` and `More.` and nothing from `# Next`, and the `Notes`
  section.

#### A trailing space

- **Given** an ancestor whose inheritable section is written `## constraints`
  with a trailing space.
- **When** the view of its child is rendered.
- **Then** the heading is `### constraints` with no trailing space.

## Additional context

- [Inheritance, computed](../../../../../docs/concepts.md#inheritance-computed)
  says what an ancestor passes on, and this leaf settles the open point there on
  how the sections are rendered.
- The show leaf prints this view, and `wio context` will show it in a bundle
  through a port.
