# `wio.formats`

The pure codecs between text and the shared types. A codec reads or writes
text, touches no file and raises a `WioError` when the text is wrong, so a model
in `wio.models` never raises.

## The TOML decoder

`decode_toml` turns a TOML text into nested `dict`s, `list`s and scalars, with
every table and key as written, and an empty text into `{}`. It is the one door
for TOML: every file wio reads goes through it, so a person or an agent learns
where a syntax error is without searching.

- A text that is not valid TOML raises `TomlSyntaxError`, a `WioError` that
  carries `message`, `line` and `column` of the first problem, counted from 1.
  It names no file, because the decoder reads none: the caller adds the file.
  `str` of it is `<message> (line <line>, column <column>)`.
- The decoder reads TOML and writes none. Reading the metadata block of a
  Markdown file, and offsetting the position of an error inside it, belongs to
  the contracts Work, which decodes the block with this decoder. Writing TOML,
  and banning `tomlkit` outside this package the way `tomllib` is banned, belong
  to the Work that adds the first writer. The
  [v0.1 scope](../../../docs/v0.1-scope.md#wioformats-internal) lists what the
  package will hold.
- The position comes from `tomllib.TOMLDecodeError`, which carries `lineno`,
  `colno` and `msg`, so the decoder reads those attributes and never parses the
  message. `TomlSyntaxError` lives in `wio.formats.errors`, the module where a
  package declares an error of its own that extends `WioError`.
- Only the position of a syntax error is reported. The decoder keeps no
  comment, no position of a key or value, and does not judge the data: whether a
  value is a date or a string is the caller's.
- Only `wio.formats` may import `tomllib`. Ruff's `banned-api` table in
  [`pyproject.toml`](../../../pyproject.toml) reports `TID251` for every form of
  the import, `lazy` forms included, in `src/wio` outside this package. Tests
  and scripts are exempt through ruff's per-file ignores, so they can read
  TOML without the decoder.
- Importing `wio.formats` loads no TOML parser: the package and the decoder bind
  their imports with `lazy`, and `tomllib` loads on the first call of
  `decode_toml`, so a command that decodes nothing pays nothing.
