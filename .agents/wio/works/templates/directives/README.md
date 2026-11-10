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
- Every directive, with its syntax, its meaning and an example, is in one table
  that the parser and `wio templates directives` share.
- The grammar is documented where the codecs are.

## Glossary

- **Directive list**: the comment `<!-- wio: ... -->` at the end of a heading,
  holding directives separated by commas.

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
  `items`, `pattern` and `inherit`, and a type for what the function returns,
  both provisional for the architecture stage.
- A table of the directives in `wio.formats`, each with its name, its syntax,
  its meaning and an example.
- The `re` module, which compiles a pattern to check it.
- An error in `wio.formats.errors` that extends `WioError` and carries the
  column of the first problem.

## Constraints

- **Names are exact.** A directive name is lowercase, and spaces around the
  `:` and the commas are allowed.
- **A pattern has two forms.** Written plainly, it runs to the next comma;
  written between double quotes, it runs to the closing quote and may hold
  commas, and neither form has an escape of wio's own.
- **The parser touches no file.** It takes a line and returns data or raises.
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

- **Given** the lines `## Glossary <!-- wio:inherit -->` and
  `## Goals <!--  wio: required ,items>=2 -->`.
- **When** the parser reads each.
- **Then** the first gives `inherit`, and the second gives `required` and at
  least 2 items.

### **AC-2** A pattern can be written plainly or between quotes

A plain pattern runs to the next comma, and a quoted pattern runs to the closing
quote.

#### Plain and quoted

- **Given** the lines `## A <!-- wio: pattern=AC-\d+, inherit -->` and
  `## B <!-- wio: pattern="AC-\d{1,3}", required -->`.
- **When** the parser reads each.
- **Then** the first gives the pattern `AC-\d+` and `inherit`, and the second
  gives the pattern `AC-\d{1,3}` and `required`.

### **AC-3** A line with no directive list gives no directives and no error

A heading without a directive list gives its text and no directives, and a line
that is not a heading gives nothing.

#### Lines that carry none

- **Given** the lines `## Purpose`, `## Purpose <!-- a note -->`, and the
  non-heading line `Some text <!-- wio: required -->`.
- **When** the parser reads each.
- **Then** the first gives the text `Purpose` and no directives, the second
  gives its text with the note kept and no directives, and the third gives
  nothing; none raises an error.

### **AC-4** A list with a wrong name or shape is an error with its column

An unknown name, a name in the wrong case, a name written twice and an empty
list are errors.

#### The wrong lists

- **Given** the lists `mandatory`, `Required`, `required, required`, and an
  empty list `<!-- wio: -->`, each on a level-2 heading.
- **When** the parser reads each.
- **Then** each raises an error that says what is wrong and names the column
  where it starts.

### **AC-5** A directive with a wrong value is an error with its column

An `items` without a count of 1 or more, and a `pattern` that is empty, does not
compile or is quoted without its closing quote, are errors.

#### The wrong values

- **Given** the directives `items>=`, `items>=0`, `items>=-1`, `items>=1.5`,
  `pattern=`, `pattern=(`, and `pattern="AC-`, each on a level-2 heading.
- **When** the parser reads each.
- **Then** each raises an error that says what is wrong and names the column of
  the value, and the one for `pattern=(` carries the message of `re`.

### **AC-6** The level is returned and not restricted

A directive list on a heading of any level is read, and its level is returned.

#### A level-3 heading

- **Given** the line `### Notes <!-- wio: required -->`.
- **When** the parser reads it.
- **Then** the text is `Notes`, the level is 3 and the directive is `required`.

### **AC-7** The table lists every directive and its examples parse

The table has an entry for each of `required`, `items>=N`, `pattern=<regex>`
in its plain and quoted forms, and `inherit`, each with its syntax, its meaning
and an example heading, and the parser reads every example into the directive
it documents.

#### Each example

- **Given** the table.
- **When** the parser reads the example of each entry.
- **Then** it gives the directives that the entry documents and raises no error.

### **AC-8** The README of `wio.formats` describes the grammar

`src/wio/formats/README.md` states where a directive list sits, the four
directives with their syntax, that names are lowercase and exact, the plain and
quoted forms of `pattern`, with the way to write a literal `"` or `>` as `\x22`
or `\x3e`, which wrong lists are errors, that the parser returns the level and
the checks that use it allow directives on level-2 headings only, and that
finding items is left to the contracts Work.

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
