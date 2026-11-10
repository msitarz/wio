# `wio.formats`

The pure codecs between text and the shared types. A codec reads or writes text,
touches no file and raises a `WioError` when the text is wrong, so a model in
`wio.models` never raises. The
[v0.1 scope](../../../docs/v0.1-scope.md#wioformats-internal) lists what the
package will hold.

## The TOML decoder

`decode_toml` in [`toml.py`](toml.py) is the one door for TOML: every file wio
reads goes through it, so a person or an agent learns where a syntax error is
without searching. It reads TOML and does not judge the data: whether a value is
a date or a string is the caller's. Its docstring and that of
[`TomlSyntaxError`](errors.py) say what it returns and raises.

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
`wio templates directives` share. The table `DIRECTIVES` in the same file lists
every directive with its syntax, its meaning and its examples, and the
[concepts](../../../docs/concepts.md#directives) say what each means.

- **Where a list sits.** At the end of a heading's line, as a comment that opens
  with `<!--`, whitespace and the lowercase `wio:`. Any other comment, such as
  `<!-- wio :` or `<!-- WIO:`, is a note and stays in the heading's text.
- **The directives.** `required` and `inherit` take no value, `items>=N` takes a
  count of 1 or more and `pattern=<regex>` takes a regular expression, separated
  by commas, with spaces allowed around the commas, `>=` and `=`.
- **Names are exact.** A name is lowercase and written once in a list.
- **Two forms of a pattern.** Plain, it runs to the next comma or the end of the
  list, trimmed, and holds no `"`. Between double quotes, it runs to the closing
  quote and may hold commas. wio has no escape of its own, so a literal `"` or
  `>` is written `\x22` or `\x3e`, which `re` reads, and `-->` cannot occur
  inside a list.
- **One list that ends its heading.** It closes on its heading's line, nothing
  follows it, and a heading has one. A note may come before it. A heading too
  long for the line limit of Markdown is shortened, or has the limit suppressed
  by `<!-- rumdl-disable-next-line MD013 -->` on the line above it.
- **Errors name a column.** An unknown name or one in the wrong case, a name
  written twice, an empty list, a trailing comma, a list that does not close,
  text or a second list after it and a wrong value are errors, and each names
  the first character of the offending token, counted from 1 on the line.
- **The level is returned, not restricted.** The parser reads a list on a
  heading of any level, and the checks that use it allow directives on level-2
  headings only.
