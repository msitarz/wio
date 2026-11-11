<!-- wio
id = "d2ytdf"
template = "feature.leaf"
roots = ["wio"]
depends_on = ["7anq34", "xtgz9z", "sz1zsq", "mb4q2g"]
-->

# Checking the body of a contract

## Purpose

A person or an agent that edits a contract needs to be told what is wrong with
its body: a missing required section, too few items, a missing or repeated id,
a section that is misspelled. The checks must come from the template the
contract follows, so a contract cannot loosen them, and must be reported in the
same run as the problems of the Works' metadata.

## Goals

- The body of a contract is checked against the directives of its template, or
  against its own headings when it names none, in the `wio contracts check` run.
- A section that is misspelled is told by the closest section of the template.
- A contract that follows a template cannot loosen the template's checks.
- The directives of a template are read once, however many contracts follow it.

## Glossary

- **Section of a contract**: a `##` heading of its body with what follows it up
  to the next heading of level 2 or above.

## Non-Goals

- The items and the sections that a contract inherits, whose ids are not the
  Work's own.
- Judging the template itself, which `wio templates check` does, and the
  metadata, which the check-works leaf does.
- Sections deeper than level 2, which are free and carry no directives.
- Judging whether every criterion is covered, or what a section says.

## Assumptions

- **A-1**: The items, discovery, command and check-works leaves are delivered,
  so the finder and the judge of items, the Works, the catalog and the `check`
  command exist.
- **A-2**: `read_outline` and `read_directive_heading` give the headings of a
  body with their lines and the directives of a heading, and the directive
  parser's error carries a line and a column, as `wio templates check` already
  relies on.
- **A-3**: When the body is checked, a template that the catalog gives is one
  that `wio templates check` accepts, and any other has been reported already.

## Mechanisms

- A function in `wio.contracts` that, for each Work, finds its directive source,
  matches the sections and runs one function for each concern, and returns the
  diagnostics. It is called by the `check` command of the check-works leaf.
- The finder and the judge of items from the items leaf, and `closest_key` from
  the shared leaf.
- `read_outline` and `read_directive_heading` for the headings and directives,
  `read_metadata_block` for the body, and the catalog port and `FileSystem` to
  find and read a template.
- The names and the signatures above are provisional, for the architecture stage
  to decide.

## Constraints

- **One source of directives.** A contract that names a template takes them from
  that template, and a directive list in the contract is ignored with a warning.
  A contract that names none takes them from its own `##` headings, and only
  from those.
- **Sections are matched by text.** A contract's `##` heading matches the
  template's by its text, ignoring case, surrounding whitespace and a trailing
  directive comment, and nothing else is normalized.
- **The first heading counts.** When a `##` heading is repeated, the first is
  the section, the repeat is a warning, and it carries no items.
- **Every finding is at a line.** It is at `<file>:<line>` of the heading, with
  `:<column>` for an error of the directive parser, and a section that is
  missing is at the file.
- **Nothing is reported twice.** A contract whose template is missing or
  rejected gets no body check, because the check-works leaf has reported it.
- **A template is read once per run.** Its directives are found once and shared
  by every contract that follows it.
- **Nothing is written.** The body is read through `FileSystem`.

## Acceptance criteria

### **AC-1** A required section that is missing is an error

A section that the template marks `required` and the contract lacks is an error,
and a section that is not required may be absent.

#### Matching and missing

- **Given** a template `t` with `## Purpose <!-- wio: required -->`,
  `## Goals <!-- wio: required -->` and `## Notes`, and a contract that follows
  it with `##  purpose` and no other section.
- **When** `wio contracts check` runs.
- **Then** there is one error at the contract's file, ``The section `Goals` is
  required by the template `t` ``, none for `Purpose`, which matches in another
  case, and none for `Notes`.

### **AC-2** Items and their ids are judged as the items leaf judges them

The sections that the template gives `items` and `pattern` are counted and their
ids are checked.

#### Count and ids

- **Given** a template with `## Goals <!-- wio: items>=1 -->` and
  `## Acceptance criteria <!-- wio: pattern=AC-\d+ -->`, and a contract whose
  `## Goals` holds only an authoring comment and whose criteria are
  `### **AC-1** First`, `### **AC-1** Second` and `### Third`.
- **When** `wio contracts check` runs.
- **Then** there is one error at `## Goals` for the missing item, one that names
  `AC-1` and the lines of both criteria, and one at `### Third` for its missing
  id.

### **AC-3** A misspelled section is a warning with a suggestion

A `##` heading that the template does not have is a warning at its line, and it
names the closest template section when there is one.

#### Close and far

- **Given** a template with `## Constraints <!-- wio: inherit -->`, and a
  contract with `## Constraint`, `## Zzz` and a `### Detail` heading below one
  of them.
- **When** `wio contracts check` runs.
- **Then** there is a warning
  ``The section `Constraint` is not in the template `t`. Did you mean `Constraints`?``
  at its line, a warning ``The section `Zzz` is not in the template `t` `` at
  its line, none for `### Detail`, and the command exits 0 for these alone.

#### No template

- **Given** a contract that names no template and has sections of its own.
- **When** `wio contracts check` runs.
- **Then** there is no warning about a section.

### **AC-4** A directive list in a contract that follows a template is ignored

Such a list gives a warning and changes nothing, so a contract cannot loosen the
template's checks.

#### A list in a contract

- **Given** a template that requires `## Goals`, and a contract that follows it,
  lacks `## Goals` and has `## Notes <!-- wio: required -->`.
- **When** `wio contracts check` runs.
- **Then** there is a warning at the line of `## Notes` that says the directive
  list is ignored because the contract follows the template, and the error for
  the missing `Goals` is still reported.

### **AC-5** A contract without a template is checked by its own headings

Its directive lists are read, and a list that cannot be read is an error at the
parser's line and column.

#### Own directives

- **Given** a contract with no template whose headings are
  `## Purpose <!-- wio: required -->`, `## Goals <!-- wio: items>=2 -->` over
  one item, `## Bad <!-- wio: mandatory -->` and
  `### Deep <!-- wio: required -->`.
- **When** `wio contracts check` runs.
- **Then** there is an error for too few items in `Goals`, an error at the line
  and column of the parser for `mandatory`, an error at the heading of `Deep`
  that says directives are read on level-2 headings only, and none for
  `Purpose`.

#### No directives

- **Given** a contract with no template and no directive list.
- **When** `wio contracts check` runs.
- **Then** there is no diagnostic about its body.

### **AC-6** A repeated section and a missing title are warnings

A `##` heading that repeats is a warning and carries nothing, and a contract
with no heading is a warning.

#### Repeats and no title

- **Given** a contract with `## Goals` twice, the first holding one item and the
  second two, under a template that requires `items>=2` for it, and a second
  contract whose body has no heading.
- **When** `wio contracts check` runs.
- **Then** there is a warning at the second `## Goals`,
  ``The section `Goals` is repeated; the first one counts``, an error for the
  too few items of the first, and a warning ``The contract has no title`` at the
  file of the second contract.

### **AC-7** A template that cannot be used gets no body check, and is read once

A contract whose template is missing or rejected gets no body diagnostic, and a
template that several contracts follow is read once.

#### Skipped and shared

- **Given** a contract that names a template the catalog does not have, a
  contract whose template is rejected, and three contracts that follow one good
  template, over a file system that counts reads.
- **When** `wio contracts check` runs.
- **Then** the first two have no diagnostic about their bodies, and the good
  template's file was read once for the three.

### **AC-8** What an entry template requires decides what a fresh Work needs

A contract fresh from a template that requires only headings passes, and one
from a template that requires an item does not until it has one.

#### Fresh Works

- **Given** a template that requires `## Purpose` and a contract made from it
  with its Purpose written, and a template that requires `items>=1` on
  `## Goals` and a contract made from it whose Goals holds only the authoring
  comment.
- **When** `wio contracts check` runs.
- **Then** the first passes, and the second gives one error at `## Goals` for
  the missing item until a first item is written.

## Additional context

- [Checking a contract against its template](../../../../../docs/concepts.md#checking-a-contract-against-its-template)
  says how sections are matched and what a stray heading is.
- The suggestion on a misspelled section extends that warning with the closest
  section, as the check-works leaf does for a key.
- This leaf adds its checks to the `check` command that the check-works leaf
  owns, so it is delivered after it.
