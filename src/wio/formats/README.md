# `wio.formats`

The pure codecs between text and the shared types. A codec reads or writes
text, touches no file and raises a `WioError` when the text is wrong, so a model
in `wio.models` never raises.

## The TOML decoder

`decode_toml` in [`toml.py`](toml.py) is the one door for TOML: every file wio
reads goes through it, so a person or an agent learns where a syntax error is
without searching. Its docstring and that of
[`TomlSyntaxError`](errors.py) say what it returns and raises.

- The decoder reads TOML and writes none. Writing TOML,
  and banning `tomlkit` outside this package the way `tomllib` is banned, belong
  to the Work that adds the first writer. The
  [v0.1 scope](../../../docs/v0.1-scope.md#wioformats-internal) lists what the
  package will hold.
- The decoder does not judge the data: whether a value is a date or a string is
  the caller's.
- Only `wio.formats` may import `tomllib`. Ruff's `banned-api` table in
  [`pyproject.toml`](../../../pyproject.toml) reports `TID251` for every form of
  the import, `lazy` forms included, in `src/wio` outside this package. Tests
  and scripts are exempt through ruff's per-file ignores, so they can read
  TOML without the decoder.

## The metadata block reader

`read_metadata_block` in [`block.py`](block.py) is the one reader of the
metadata block that opens a file, so no command has its own idea of where a
block starts and ends. It takes the text of a file and returns a
[`MetadataBlock`](../models/block.py), and its docstring and that of
[`MetadataBlockError`](errors.py) say what it returns and raises.

- The block is on the first line of the text, after an optional leading U+FEFF:
  a `<!-- wio` comment that ends at the first `-->`, or `+++` front matter that
  ends at the next line that is `+++`. CRLF and LF read alike.
- The marker is the key `wio`, and its only value is the integer 1. A comment
  may leave it out, and its version is then 1. Front matter needs it, and no
  other value is accepted.
- The body is the text from its start line on, byte for byte. It starts on the
  line after the one that holds the closing delimiter, or on that same line
  when text follows a closing `-->`.
- A text with no block gives `None`, and so does `+++` front matter with no
  `wio =` in it, closed or not, because it is not wio's.
- A block that claims to be wio's and cannot be read raises
  `MetadataBlockError` with the line in the text that the reader was given: a
  comment or front matter that does not close, TOML that does not parse, or a
  marker that is not 1.
- The reader decodes the TOML with `decode_toml`, which loads `tomllib` on its
  first call, so a text with no block never loads it.
- The reader does not judge the keys of the data, and it reads no file and
  names none in an error: the caller does both.
