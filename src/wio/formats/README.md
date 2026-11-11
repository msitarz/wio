# `wio.formats`

The pure codecs between text and the shared types. A codec reads or writes text,
touches no file and raises a `WioError` when the text is wrong, so a model in
`wio.models` never raises. The
[v0.1 scope](../../../docs/v0.1-scope.md#wioformats-internal) lists what the
package holds.

## The TOML decoder

`decode_toml` in [`toml.py`](toml.py) is the one door for TOML: every file wio
reads goes through it, so a person or an agent learns where a syntax error is
without searching. It reads TOML and does not judge the data: whether a value is
a date or a string is the caller's. Its docstring and that of
[`TomlSyntaxError`](errors.py) say what it returns and raises.

`encode_toml` in [`writer.py`](writer.py) is the one writer. So only this
package imports `tomllib` and `tomlkit`, and ruff's `banned-api` reports an
import of either anywhere else.

## The metadata block reader

`read_metadata_block` in [`block.py`](block.py) is the one reader of the
metadata block that opens a file, so no command has its own idea of where a
block starts and ends. Its docstring, that of
[`MetadataBlock`](../models/block.py) and that of
[`MetadataBlockError`](errors.py) say what it reads, returns and raises, and its
[tests](../../../tests/unit/formats/test_block.py) say how each case reads.

- The reader judges the shape of the block and never its keys, which belong to
  the template and the contract, and it reads no file and names none in an
  error, so the caller does both.
- Whether a text is wio's is decided by the marker, so `+++` front matter that
  has no `wio =` in it belongs to another tool and gives nothing, while a block
  that does carry the marker and cannot be read is an error and is never
  skipped.
- A text with no block never loads `tomllib`, which the decoder loads on its
  first call, so reading an unmarked file stays cheap.

### What the reader accepts

- **Delimiters.** The block is on the first line of the text, after an optional
  leading U+FEFF: a `<!-- wio` comment that ends at the first `-->`, or `+++`
  front matter that ends at the next line that is `+++`. CRLF and LF read alike.
- **The marker.** The key `wio`, whose only value is the integer 1. A comment
  may leave it out, and its version is then 1. Front matter needs it, and no
  other value is accepted.
- **What it returns.** The form, the version, the data without the marker, and
  the body from its start line on, byte for byte.
- **What gives nothing.** A text with no block on its first line, and `+++`
  front matter with no `wio =` in it, closed or not.
- **What raises.** A block that has the marker or the comment opening and does
  not close, whose TOML does not parse, or whose marker is not 1. The error
  names the line of the text.

## The directive grammar

`read_directive_heading` in [`directives.py`](directives.py) reads one heading
line into its text, its level and its directives, so a template's sections say
what they must hold in one grammar that the checks and
`wio templates directives` share. The table `DIRECTIVES` beside it lists every
directive with its syntax, its meaning and its examples, `COMBINING` says how
several directives share one comment, the parser's docstring
and [`DirectiveSyntaxError`](errors.py) say what it reads and raises, and the
[concepts](../../../docs/concepts.md#directives) say what each directive means.

- A plain pattern runs to the next comma and a quoted one holds commas, because
  wio has no escape of its own. A literal `"` or `>` is written `\x22` or
  `\x3e`, which `re` reads, so `-->` never occurs inside a list.
- The parser returns the level and does not restrict it. The checks that use it
  allow directives on level-2 headings only.
- A heading too long for the line limit of Markdown is shortened, or has the
  limit suppressed by `<!-- rumdl-disable-next-line MD013 -->` on the line above
  it, because a list closes on its heading's line.

## The outline

`read_outline` in [`outline.py`](outline.py) finds the real headings of a
Markdown body, so the skeleton, the check of a template and `wio contracts`
agree on which lines are section headings. Its docstring and
[`Heading`](../models/heading.py) say what it takes and returns, and its
[tests](../../../tests/unit/formats/test_outline.py) say how each case reads.

- **A real heading is an ATX heading at the top level of the body.** A heading
  inside code, an HTML comment, a blockquote or a list item, and a setext
  heading, only looks like one, because the check and `wio contracts` treat a
  section heading as a heading of the body itself.
- **A heading carries four fields:** its level from 1 to 6, its text without the
  marks and spaces around it, its raw line as written, and its line in the file,
  counted from the start line of the body that the caller passes.
- **Headings are the only structure it returns.** What lies between them, the
  extent of a section and its items, is for the contracts Work to decide.
- **The parser is `markdown-it-py`,** whose CommonMark rules are the definition
  of a heading, a fence and a comment block, so wio has no grammar of its own to
  keep in step with Markdown. [`markdown.py`](markdown.py) builds it once for
  the outline and the items. Only `wio.formats` imports it, and it loads on the
  first reading, so a command that reads no body never pays for it.

## The items of a section

`find_items` and `judge_items` in [`items.py`](items.py) are the one rule for
what an item of a contract's section is, which id it carries and whether a
contract's items are sound, so every reader of a contract finds the same items.
Their docstrings say what each takes and returns, the types are in
[`item.py`](../models/item.py), and their
[tests](../../../tests/unit/formats/test_items.py) say how each case reads. The
[concepts](../../../docs/concepts.md#item-ids) say what an id is for.

- **Only `wio.formats` finds items.** No other package derives them from the
  Markdown again, because two readers would disagree about an edge case and a
  record would cite an id that one of them cannot see. A test reads the syntax
  trees of the sources to hold this, and ruff bans the parser outside the
  package.
- **A section's items are its subheadings, or else its list items.** This
  repository's criteria are `###` subheadings, and its assumptions and goals are
  lists, so both shapes count and the subheadings win. A list that comes after a
  deeper heading belongs to that part of the section and is not an item, and a
  list item is one item with everything nested in it.
- **Only the body's own content counts.** A comment, a code block and a quote
  hold no items, so the authoring example of a template is never counted as the
  contract's own.
- **The id is exactly what the pattern matches at the start of the text.** It
  skips the markup that a writer puts around an id, such as `**AC-1**`, and
  never trims or changes it, so what a record cites is what the contract shows.
  An item without a match has no id, and so does an empty match, because an id
  that is empty cites nothing.
- **A finding has a fixed place.** The judge reports a section's shortfall at
  its heading and an item's fault at the item, and a repeated id once, at its
  first use, so a person fixes one place and an editor can jump to it. It
  returns them in the order of `sort_diagnostics`, as the other checks do.
- **The block reader and the directive parser are not its business.** It takes
  the sections and their directives from the caller, so it never reads a
  template, and matching a contract's sections to a template's is for
  `wio contracts`.

## The skeleton

`prepare_skeleton` in [`skeleton.py`](skeleton.py) prepares a template as the
text of a contract that follows it, so that what `wio templates show` prints is
what `wio contracts new` writes, apart from the `id` it adds. Its docstring says
what it takes, returns and raises, and its
[tests](../../../tests/unit/formats/test_skeleton.py) say how each case reads.

- **It keeps what the author wrote for the agent and drops what is for wio.**
  The skeleton holds `template` and the keys and tables of the template's
  `[contract]` table in the order the template wrote them, and the body with the
  directive list taken off each real heading. The template's own keys, the
  comments of its metadata and any `id` are dropped, and wio writes no `id`.
- **The block form is the template's.** A comment block gives a comment block,
  and `+++` front matter gives `+++` front matter with the marker `wio = 1` as
  its first key.
- **The same template always gives the same skeleton,** so the output of
  `wio templates show` is stable.
- **The writer loads on first use.** `encode_toml` in [`writer.py`](writer.py)
  is the one writer of TOML, and `tomlkit` is imported when it is first called,
  so reading a block or a template never loads it.
