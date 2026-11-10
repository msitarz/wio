<!-- wio
id = "1n1p8j"
template = "feature.draft"
roots = []
depends_on = []
-->

# The directive grammar

## Purpose

A template's sections need one grammar that says what each section must hold.

## Intent

Parse a heading's directives into typed values in `wio.formats`, with the
optional quoted `pattern`, and keep one table of the directives (name, syntax,
meaning and an example taken from this repository's templates) that the parser
and `wio templates directives` share. A unit test parses every example in the
table with the parser, so the table cannot drift from the grammar. Document the
grammar in `src/wio/formats/README.md`. Finding items in a section is deferred
to the contracts Work.
