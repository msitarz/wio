<!-- wio
id = "1n1p8j"
template = "feature.leaf"
roots = ["wio", "repo"]
depends_on = []
-->

# The directive grammar

## Purpose

A template's sections need one grammar that says what each section must hold,
and anyone who writes or checks a template needs one place that says what that
grammar is.

## Goals

- A heading's directive list is read into typed directives, with the heading's
  text and level.
- A directive list that is wrong is an error that says what is wrong and where,
  so a misspelled directive cannot drop a requirement.
- A pattern can hold a comma, written without escapes of wio's own.
- Every directive, with its syntax, its meaning and its examples, is in one
  table that the parser and `wio templates directives` share.
- The grammar is documented where the codecs are.

## Non-Goals

- Finding the items of a section, and what `items` and `pattern` count, which
  the contracts Work decides.
- Applying a directive to a contract, and matching a contract's headings to a
  template's.
- Allowing directives only on level-2 headings, which the checks that use the
  parser do.
- Printing the table, which the directives reference leaf does.

## Assumptions

- **A-1**: Headings are ATX headings, one to six `#` and a space before the
  text, and a setext heading is not one.
- **A-2**: The regular expressions are those of Python's `re` module, the one
  dialect wio uses.

## Mechanisms

- A function in `wio.formats` that takes one line of text, with a name and a
  signature that the architecture stage fixes.
- A `Directive` type in `wio.models` with one variant for each of `required`,
  `items`, `pattern` and `inherit`, and a result `DirectiveHeading` with the
  text, the level and the directives, or `None` for a line that is not a
  heading, both provisional for the architecture stage; the outline's `Heading`
  is a different type.
- A table of the directives in `wio.formats`, in the order `required`, `items`,
  `pattern`, `inherit`, each entry with its name, its syntax, its meaning and
  its examples, each example a whole heading line.
- The `re` module, which compiles a pattern to check it.
- An error in `wio.formats.errors` that extends `WioError` and carries the
  column of the first problem.

## Constraints

- **The opener is `<!--`, whitespace, `wio:`, whitespace.** A directive list
  opens with `<!--`, zero or more whitespace characters, the lowercase `wio:`
  with the colon right after it, and zero or more whitespace characters, and
  ends at the first `-->`; any other comment, such as `<!-- wio :` or
  `<!-- WIO:`, is a note and not a list, and spaces are also allowed before the
  `-->`, around the commas, and around the `>=` and the `=`.
- **Names are exact.** A directive name is lowercase.
- **A name takes what its syntax says.** `required` and `inherit` take no value,
  `items` takes `>=` and a count, and `pattern` takes `=` and a pattern; a
  recognized name with another operator, with none, or followed by anything else
  before the next comma, is a wrong value, and a name that is not one of the
  four is an unknown name.
- **A list is on one line and ends the heading.** It opens and closes on its
  heading's line with nothing after it, and there is one to a heading, though a
  note may come before it, so a heading too long for the Markdown line limit is
  shortened or has the limit suppressed on the line above it, and a list split
  over two lines is an error.
- **A pattern has two forms.** Written plainly, it runs from after the `=` to
  the next comma or the end of the list, trimmed of surrounding spaces, with
  inner spaces kept and no `"` in it; written between double quotes, it runs to
  the closing quote, may hold commas, and only spaces and a comma or the end of
  the list may follow it; an empty pattern in either form is an error.
- **A literal `"` or `>` in a pattern is written `\x22` or `\x3e`.** wio has no
  escape of its own, so `-->` cannot occur inside a list.
- **An error names a column.** It is counted from 1 on the heading's line and is
  the first character of the offending token: the name, the operator or the
  value, the opener of a list that does not close or of a second list, or the
  first character after the list.
- **The parser touches no file.** It takes a line and returns data or raises,
  which its signature, fixed at the architecture stage, shows and its review
  judges.
- **Verification.** What is read is verified by AC-1, AC-2 and AC-3, the errors
  by AC-4 and AC-5, the level by AC-6, the table by AC-7 and the documents by
  AC-8.

## Acceptance criteria

### **AC-1** A directive list is read into typed directives in order

A level-2 heading with a directive list gives the heading's text, its level and
its directives in the order written.

#### A full list

- **Given** the line
  `## Acceptance criteria <!-- wio: required, items>=1, pattern=AC-\d+ -->`.
- **When** the parser reads it.
- **Then** the text is `Acceptance criteria`, the level is 2, and the
  directives are `required`, at least 1 item and the pattern `AC-\d+`, in that
  order.

#### Spaces

- **Given** the lines `## Glossary <!-- wio: inherit   -->`,
  `## Goals <!--wio:required ,items>=2 -->`,
  `## H <!--  wio:  inherit -->` and
  `## C <!-- wio: items >= 2, pattern = AC-\d+ -->`.
- **When** the parser reads each.
- **Then** the first gives `inherit`, the second gives `required` and at least 2
  items, the third gives `inherit`, and the fourth gives at least 2 items and
  the pattern `AC-\d+`.

### **AC-2** A pattern can be written plainly or between quotes

A plain pattern runs to the next comma, trimmed, and a quoted pattern runs to
the closing quote.

#### Plain and quoted

- **Given** the lines `## A <!-- wio: pattern=AC-\d+, inherit -->`,
  `## B <!-- wio: pattern="AC-\d{1,3}", required -->` and
  `## C <!-- wio: pattern=a b -->`.
- **When** the parser reads each.
- **Then** the first gives the pattern `AC-\d+` and `inherit`, the second gives
  the pattern `AC-\d{1,3}` and `required`, and the third gives the pattern
  `a b`.

#### A literal quote and angle bracket

- **Given** the line `## D <!-- wio: pattern=a\x22b\x3ec -->`.
- **When** the parser reads it.
- **Then** the pattern is `a\x22b\x3ec`, which `re` reads as `a"b>c`.

### **AC-3** A line with no directive list gives no directives and no error

A heading without a directive list gives its text and no directives, a heading
with a note before a list gives its text with the note and the list's
directives, and a line that is not a heading gives `None`.

#### Lines that carry none

- **Given** the lines `## Purpose`, `## Purpose <!-- a note -->`,
  `## T <!-- wio -->`, `## T <!-- WIO: required -->`,
  `## T <!-- wio : required -->` and the non-heading line
  `Some text <!-- wio: required -->`.
- **When** the parser reads each.
- **Then** the first gives the text `Purpose` and no directives, the next four
  give their text with the comment kept and no directives, and the last gives
  `None`; none raises an error.

#### A note before a list

- **Given** the line `## Both <!-- a note --> <!-- wio: required -->`.
- **When** the parser reads it.
- **Then** the text is `Both <!-- a note -->`, the level is 2 and the directive
  is `required`.

### **AC-4** A list with a wrong name or shape is an error with its column

An unknown name, a name in the wrong case, a name written twice, an empty list,
a list that does not close on its line, text after a list and two lists on one
heading are errors.

#### The wrong lists

- **Given** these level-2 headings: `## A <!-- wio: mandatory -->`,
  `## B <!-- wio: Required -->`, `## D <!-- wio: required, required -->`,
  `## E <!-- wio: -->`, `## S <!-- wio: required,`,
  `## T <!-- wio: required --> tail` and
  `## U <!-- wio: required --> <!-- wio: inherit -->`.
- **When** the parser reads each.
- **Then** each raises an error that says what is wrong and names, in turn,
  columns 16, 16, 26, 16, 6, 29 and 29; the one for the unclosed list says that
  a list must close on the line of its heading, the one for text after the list
  that a list must end its heading, and the one for two lists that there is one
  list to a heading.

### **AC-5** A directive with a wrong value is an error with its column

An `items` without a count of 1 or more, a name with an operator it does not
take, and a `pattern` that is empty, has a `"` in a plain form, does not
compile, has text after its closing quote or is quoted without its closing
quote, are errors.

#### The wrong values

- **Given** these level-2 headings, each of the form `## I <!-- wio: ... -->`
  with these directives: `items`, `items>=`, `items>=0`, `items>=-1`,
  `items>=1.5`, `items=2`, `items>2`, `required=1`, `required inherit`,
  `pattern=`, `pattern=(`, `pattern=""`, `pattern=a"b`, `pattern="a"b` and
  `pattern="AC-`.
- **When** the parser reads each.
- **Then** each raises an error that says what is wrong and names, in turn,
  columns 16, 21, 23, 23, 23, 21, 21, 24, 25, 23, 24, 24, 25, 27 and 24, and the
  one for `pattern=(` carries the message of `re`.

### **AC-6** The level is returned and not restricted

A directive list on a heading of any level is read, and its level is returned.

#### A level-3 heading

- **Given** the line `### Notes <!-- wio: required -->`.
- **When** the parser reads it.
- **Then** the text is `Notes`, the level is 3 and the directive is `required`.

### **AC-7** The table lists every directive in order and its examples parse

The table has, in the order `required`, `items`, `pattern`, `inherit`, an entry
for each directive with its name, its syntax, its meaning and its examples, one
for each form it can be written in, so two for `pattern`, and each example is a
whole heading line that the parser reads into the directive it documents.

#### The entries

- **Given** the table.
- **When** its entries are read in order.
- **Then** the names are `required`, `items`, `pattern` and `inherit`, `pattern`
  has a plain and a quoted example and the others have one, and each entry has a
  syntax and a meaning.

#### Each example

- **Given** the table.
- **When** the parser reads the example of each entry.
- **Then** it gives the directives that the entry documents and raises no error.

### **AC-8** The documents describe the grammar

`src/wio/formats/README.md` states where a directive list sits and that it opens
with `<!--`, whitespace and `wio:`, the four directives with their syntax, that
names are lowercase and exact, what a name takes, the plain and quoted forms of
`pattern`, with the way to write a literal `"` or `>` as `\x22` or `\x3e`, which
wrong lists are errors and the column an error names, that the parser returns
the level and the checks that use it allow directives on level-2 headings only,
that a list closes on its heading's line and ends it, and how a long heading is
kept within the line limit with `<!-- rumdl-disable-next-line MD013 -->`.
`docs/concepts.md` describes the opener and the two forms of `pattern` in
its Directives section, no longer says in the open points that writing a
`pattern` that holds a comma or `-->` is open, and says that finding items is
left to the contracts Work.

## Additional context

- [Directives](../../../../../docs/concepts.md#directives) in the concepts says
  what each directive means, and
  [Item ids](../../../../../docs/concepts.md#item-ids) says why items are not
  found here.
- [The `wio.formats` README](../../../../../src/wio/formats/README.md) is where
  the grammar is documented.
- The [check](../check/README.md) and
  [directives reference](../directives-reference/README.md) leaves use the
  parser and the table.
