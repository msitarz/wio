# `wio.formats`

The pure codecs between text and the shared types. A codec reads or writes
text, touches no file and raises a `WioError` when the text is wrong, so a model
in `wio.models` never raises.

## The TOML decoder

`decode_toml` in [`toml.py`](toml.py) is the one door for TOML: every file wio
reads goes through it, so a person or an agent learns where a syntax error is
without searching. Its docstring and that of
[`TomlSyntaxError`](errors.py) say what it returns and raises.

- The decoder reads TOML and writes none. Reading the metadata block of a
  Markdown file, and offsetting the position of an error inside it, belongs to
  the contracts Work, which decodes the block with this decoder. Writing TOML,
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
