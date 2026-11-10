<!-- wio
id = "0nfz54"
template = "feature.leaf"
roots = ["wio", "repo"]
depends_on = ["p8vtzx", "1n1p8j", "vyjmpc"]
-->

# Preparing a contract skeleton

## Purpose

A template must become a contract skeleton the same way wherever one is needed,
so that what `wio templates show` prints is what `wio contracts new` will write,
apart from the id it adds.

## Goals

- A template's text becomes the skeleton of a contract that follows it, without
  an id.
- The skeleton has the block form of the template it came from.
- The skeleton keeps what the template's author wrote for the agent and drops
  what is only for wio.
- The same template always gives the same skeleton.
- `tomlkit` is the one writer of TOML, loaded only when a skeleton is prepared.

## Glossary

- **Template's own keys**: every key of a template's metadata outside its
  `[contract]` table, which describe the template and are not copied to a
  contract, as
  [from template to contract](../../../../../docs/concepts.md#from-template-to-contract)
  says, without the `name` key that a template no longer has.

## Non-Goals

- Carrying a Work's `id`, `depends_on`, roots or actions into a skeleton, which
  `--work` and `--keep` do and belong to the contracts Work.
- Writing a skeleton to a file, finding the template by its name or naming the
  file in an error, which the caller does.
- Judging whether the template is valid, which `wio templates check` does.

## Assumptions

- **A-1**: The caller passes the template's name, which is its file's name
  without `.md`, and its text.

## Mechanisms

- A function in `wio.formats` that takes a template's name and text and returns
  the skeleton's text, with a name and a signature that the architecture stage
  fixes.
- The block reader, the outline and the directive parser of `wio.formats`, which
  split the template, find its headings and read their directive lists.
- `tomlkit`, as a new runtime dependency, wrapped in one writer of `wio.formats`
  and imported by that writer when it is first called.
- Ruff's `banned-api` table, which gains `tomlkit` so that only `wio.formats`
  may import it, a requirement that the parent's AC-4 verifies.

## Constraints

- **The skeleton is the `[contract]` table and `template`.** It holds `template`
  first, then the keys of `[contract]` in the order the template wrote them,
  then its sub-tables, and never an `id`.
- **The block form is the template's.** A comment block gives a comment block,
  and `+++` front matter gives `+++` front matter with the marker `wio = 1` as
  its first key.
- **Only the template's authoring is kept.** The body is the template's own,
  except that the trailing `<!-- wio: ... -->` comment of a real heading's raw
  line, which is what the directive parser calls a list, is removed with the
  spaces before it.
- **The block and the body join plainly.** The block is written with the line
  ending of the template's first line, LF or CRLF, the body follows it as it
  was, and an empty body gives the block alone.
- **The function adds two things of its own.** It refuses a text with no
  metadata block, and it adds the line of the heading to a directive error,
  taken from the outline; every other error is the block reader's, unchanged.
- **Verification.** The two forms are verified by AC-1 and AC-2, the metadata by
  AC-3, the body by AC-4, the errors by AC-5, the lazy writer by AC-6 and the
  ban on `tomlkit` elsewhere by the parent's AC-4.

## Acceptance criteria

### **AC-1** A comment-form template gives a comment-form skeleton

The skeleton of a template that uses the comment block uses the comment block,
with the template's own keys, the directives and the metadata's comments gone,
and the same text every time.

#### A comment template

- **Given** the name `feature.leaf` and a template whose comment block holds
  `kind`, `shape`, `description`, `[actions]`, `[contract]` with `roots = []`
  and `depends_on = []`, and `[contract.x]` with `ticket = ""` and a comment,
  and whose body has `## Goals <!-- wio: required, items>=1 -->`.
- **When** the skeleton is prepared, and again.
- **Then** the block is a comment block with `template = "feature.leaf"`,
  `roots = []`, `depends_on = []` and a table `[x]` with `ticket = ""`, no
  `kind`, `shape`, `description`, `[actions]`, `[contract]` or comment, and no
  `wio` marker; the heading reads `## Goals`; and the two results are equal.

### **AC-2** A `+++` template gives a `+++` skeleton with the marker

The skeleton of a template that uses `+++` front matter uses `+++` front matter
whose first key is the marker.

#### A `+++` template

- **Given** the name `feature.leaf` and the same template written as `+++` front
  matter with `wio = 1`.
- **When** the skeleton is prepared.
- **Then** it is `+++` front matter whose first key is `wio = 1`, then
  `template = "feature.leaf"` and the same keys as the comment skeleton.

### **AC-3** The metadata is `template` and the contract's keys, and no id

The skeleton's metadata is `template`, then the keys of `[contract]` in the
template's order, then its sub-tables; wio sets `template` and never writes an
`id`, and any other key of the template is dropped.

#### The keys

- **Given** a template whose `[contract]` holds `id = "zzzzzz"`,
  `template = "other"`, `roots = ["wio"]` and a table `[contract.y]` with
  `n = 1`, and which has the keys `kind`, `shape` and `[actions]`.
- **When** the skeleton is prepared under the name `feature.leaf`.
- **Then** the metadata is `template = "feature.leaf"`, `roots = ["wio"]` and
  `[y]` with `n = 1`, in that order, with no `id` and none of `kind`, `shape`
  and `[actions]`.

#### No contract table

- **Given** a template with `kind` and `[actions]` and no `[contract]` table.
- **When** the skeleton is prepared.
- **Then** the metadata is `template` alone.

### **AC-4** The body keeps the author's text except the directive lists

Each directive list on a real heading is removed with the spaces before it, and
every other character of the body is kept as it was.

#### Lists out, the rest in

- **Given** a body with `## Purpose <!-- wio: required -->`, an authoring
  comment that spans several lines and quotes `## X <!-- wio: required -->`, a
  fenced block holding the same heading, `## Note <!-- a note -->`,
  `## Both <!-- a note --> <!-- wio: required -->`, and CRLF line endings.
- **When** the skeleton is prepared.
- **Then** the first heading reads `## Purpose`, the last reads
  `## Both <!-- a note -->`, and the comment, the fenced block, the note and the
  line endings are as they were.

#### The join

- **Given** a CRLF template, a template whose body is empty, and an LF
  template.
- **When** the skeleton is prepared from each.
- **Then** the first has CRLF line endings in its block as well as its body, the
  second is the block alone, and the third has LF endings throughout.

### **AC-5** A template that cannot be prepared is an error

A text with no metadata block is refused, and an unreadable block or a wrong
directive list raises the error of the block reader or of the directive parser.

#### The refusals

- **Given** a text with no block, a comment block that does not close, and a
  template with a heading whose list is `<!-- wio: mandatory -->`.
- **When** the skeleton is prepared from each.
- **Then** the first raises an error that says it is not a template, the second
  raises the block reader's error naming line 1, and the third raises the
  directive parser's error naming the column and the line of the heading.

### **AC-6** The writer loads when a skeleton is first prepared

Importing `wio.formats` and reading a block do not import `tomlkit`, and
preparing a skeleton does.

#### A fresh interpreter

- **Given** a new Python process.
- **When** `wio.formats` is imported and a block is read, and `sys.modules` is
  read, then a skeleton is prepared and it is read again.
- **Then** `tomlkit` is not there the first time and is there the second.

### **AC-7** The documents describe the skeleton

`GLOSSARY.md` defines Skeleton. `src/wio/formats/README.md` states what the
skeleton keeps and drops, its order, that it has the template's block form and
the marker for `+++`, that no `id` is written, and that `tomlkit` is the one
writer, loaded on first use and banned elsewhere. `docs/concepts.md` says the
same of preparing a template, without the `name` key among the template's own
keys.

## Additional context

- [From template to contract](../../../../../docs/concepts.md#from-template-to-contract)
  says how a skeleton is prepared and what `--work` carries over.
- The [show](../show/README.md) leaf prints the skeleton, and
  `wio contracts new` will write it.
- The [block reader](../block-reader/README.md), the
  [outline](../outline/README.md) and the [directives](../directives/README.md)
  leaves are what it reads through.
