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
