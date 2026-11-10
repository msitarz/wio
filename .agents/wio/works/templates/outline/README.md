<!-- wio
id = "vyjmpc"
template = "feature.leaf"
roots = ["wio", "repo"]
depends_on = ["p8vtzx"]
-->

# The outline of a Markdown body

## Purpose

The skeleton, the check of a template and later the contracts command must agree
on which lines of a Markdown body are headings, so one codec finds them.

## Goals

- The real headings of a Markdown body are returned by one function.
- A heading gives its level, its text, its raw line and its line in the file.
- A line that only looks like a heading is not one.
- Only `wio.formats` knows which parser finds the headings.

## Glossary

- **Real heading**: an ATX heading at the top level of the body, outside code
  and comments, which the check and `wio contracts` treat as a section heading.

## Non-Goals

- The extent and the content of a section, and its items, which the contracts
  Work decides.
- Reading the directives of a heading, which the directives leaf does.
- Setext headings, which are text underlined with `=` or `-`.
- Matching a contract's headings to a template's.

## Assumptions

- **A-1**: `markdown-it-py`'s one dependency, `mdurl`, comes with it under the
  parent's assumption that it can be added.
- **A-2**: The CommonMark rules as `markdown-it-py` applies them are the
  definition of a heading, a fence, a code block and a comment block, apart from
  the exclusions this Work makes.
- **A-3**: The caller passes the body that the block reader returned, with its
  start line.

## Mechanisms

- A function in `wio.formats` that takes a body and its start line, with a name
  and a signature that the architecture stage fixes.
- `markdown_it.MarkdownIt` of `markdown-it-py`, whose `heading_open` tokens
  carry the level, the nesting and the lines of each heading.
- A plain immutable type in `wio.models` for a heading, provisional for the
  architecture stage to fix.
- Ruff's `banned-api` table, which gains `markdown_it` so that only
  `wio.formats` may import it.

## Constraints

- **One parser.** Only `wio.formats` imports `markdown_it`, as only it imports
  `tomllib`, and ruff's `banned-api` reports any other import.
- **The parser loads on first use.** Importing `wio.formats` does not import
  it.
- **The outline touches no file.** It takes text and returns headings, as every
  codec of `wio.formats` does.
- **Verification.** The fields are verified by AC-1 and AC-2, what is not a
  heading by AC-3, the line endings by AC-4, the one parser by AC-5, the lazy
  import by AC-6, the documents by AC-7, and that the outline touches no file by
  its signature, which takes text, fixed at the architecture stage and judged in
  its review.

## Acceptance criteria

### **AC-1** The headings come with their level, text, raw line and file line

Each real heading of a body is returned in the order it appears, with its level
from 1 to 6, its text, its raw line and its line in the file counted from the
body's start line.

#### Headings of several levels

- **Given** the body `# A`, an empty line, `## B <!-- wio: required -->`, an
  empty line and `###### F`, each on its own line, starting on line 10.
- **When** the outline reads it.
- **Then** it returns three headings: level 1, text `A`, raw line `# A`, line
  10; level 2, text `B <!-- wio: required -->`, raw line
  `## B <!-- wio: required -->`, line 12; and level 6, text `F`, raw line
  `###### F`, line 14.

#### No heading

- **Given** a body of two paragraphs.
- **When** the outline reads it.
- **Then** it returns no headings.

### **AC-2** The text leaves out the marks around it

The text of a heading has neither the leading `#` marks nor a closing sequence
of `#` marks, nor the spaces around it, and the raw line keeps all of them.

#### A closed heading

- **Given** the lines `## Title ##` and `##   Spaced  ##` in a body, the second
  followed by two spaces.
- **When** the outline reads it.
- **Then** the texts are `Title` and `Spaced`, and each raw line is the whole
  line without its line ending, the trailing spaces included.

### **AC-3** A line that only looks like a heading is not one

A heading inside a fenced code block, an HTML comment, an indented code block, a
blockquote or a list item, and a setext heading, is not returned, and a real
heading after it is still found on its own line.

#### Lines that only look like headings

- **Given** seven bodies, each of which starts on line 1 and holds, in turn, a
  heading inside a block fenced by ` ``` `, one inside a block fenced by `~~~`,
  one inside a comment that spans several lines, one indented by four spaces,
  `> ## Quoted`, `- ## Listed`, and a paragraph underlined with `====`, and
  after it a blank line and `## Real`.
- **When** the outline reads each.
- **Then** each returns the one heading `Real`, whose line is the line it is on
  in that body.

### **AC-4** Line endings do not change the headings

A body with CRLF line endings gives the same headings and lines as the same body
with LF, and a raw line never ends in a carriage return.

#### The same body twice

- **Given** one body written with LF and with CRLF.
- **When** the outline reads both.
- **Then** the two results are equal, and no raw line ends in a carriage
  return.

### **AC-5** Only `wio.formats` imports the parser

No module of `wio` other than `wio.formats` imports `markdown_it`.

#### A module that imports it

- **Given** a module of `wio.templates` that imports `markdown_it`.
- **When** `ruff check` runs on `src/wio`.
- **Then** it reports `TID251` for the import.

### **AC-6** The parser loads when the outline first reads a body

Importing `wio.formats` does not import `markdown_it`, and the first reading of
a body does.

#### A fresh interpreter

- **Given** a new Python process.
- **When** `wio.formats` is imported and `sys.modules` is read, then the outline
  reads one body and `sys.modules` is read again.
- **Then** `markdown_it` is not there the first time and is there the second.

### **AC-7** The README of `wio.formats` describes the outline

`src/wio/formats/README.md` states what a real heading is and what is not, the
four fields the outline returns, that headings are the only structure it
returns, that the parser is `markdown-it-py` and that only `wio.formats`
imports it.

## Additional context

- [The `wio.formats` README](../../../../../src/wio/formats/README.md) is where
  the outline is documented.
- The [skeleton](../skeleton/README.md) and [check](../check/README.md) leaves
  read headings through it, and `wio contracts` will.
- The dependency on the [block reader](../block-reader/README.md) is one of data
  flow: the outline reads the body and start line it returns.
