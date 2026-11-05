<!-- wio
id = "wxwwnt"
template = "feature.leaf"
roots = ["wio", "repo"]
depends_on = []
-->

# The TOML decoder

## Purpose

Every TOML file wio reads must pass through one decoder that tells where a
syntax error is, so that a person or an agent can fix it without searching.

## Goals

- A TOML text becomes plain Python data, or fails with the line and column of
  the first problem.
- No module of `src/wio` outside `wio.formats` can import `tomllib`; tests and
  scripts may.
- Importing the decoder costs nothing until a file is decoded.

## Non-Goals

- Reading the metadata block of a Markdown file, which the contracts Work does
  with this decoder and offsets the position of.
- Writing TOML, and banning `tomlkit` outside `wio.formats`: the Work that adds
  the first writer does both.
- Keeping comments, or the position of a key or a value: only a syntax error has
  a position.
- Judging the data: whether a value is a date or a string is the caller's.

## Assumptions

- **A-1**: `tomllib.TOMLDecodeError` carries `lineno`, `colno` and `msg` in
  Python 3.15, so the decoder can report the position without parsing the
  message.
- **A-2**: Ruff's `TID251` banned-api rule flags `import tomllib`,
  `from tomllib import x`, a submodule import and the `lazy` forms.

## Mechanisms

- `tomllib.loads`, imported with `lazy import` in `wio.formats`.
- `wio.formats.errors`, the module where a package declares an error of its own
  that extends `WioError`.
- Ruff's `flake8-tidy-imports` `banned-api` table in `pyproject.toml`, with a
  per-file ignores for `src/wio/formats/**`, `tests` and `scripts`.
- `ruff check --stdin-filename`, so a probe can be linted as if it lived at a
  given path without being written there.

## Acceptance criteria

### **AC-1** A TOML text becomes plain data

`decode_toml` returns the document as nested `dict`s, `list`s and scalars, with
every table and key as written.

```python
def decode_toml(text: str) -> dict[str, object]: ...
```

#### A valid document

- **Given** the text `a = 1` followed by a newline, a table `[t]` holding
  `s = "x"` and `l = [1, 2]`.
- **When** `decode_toml` runs.
- **Then** it returns `{"a": 1, "t": {"s": "x", "l": [1, 2]}}`, and an empty
  text gives `{}`.

### **AC-2** A syntax error carries its position

Text that is not valid TOML raises `TomlSyntaxError`, a `WioError`, with a
message, a line and a column, and no file name.

```python
class TomlSyntaxError(WioError):
    message: str
    line: int
    column: int
```

#### An invalid value

- **Given** the text `a = 1` and `b = = 2` on two lines.
- **When** `decode_toml` runs.
- **Then** it raises `TomlSyntaxError` with line 2 and column 5, a message that
  names the problem, and `str` of the error holds the message, the line and the
  column.

#### A duplicate key and an unterminated string

- **Given** the text `a = 1` and `a = 2` on two lines, and the text `a = "x`.
- **When** `decode_toml` runs on each.
- **Then** the first raises `TomlSyntaxError` at line 2, column 6, and the
  second at line 1, column 7, not at the start of the text.

### **AC-3** Only `wio.formats` may import `tomllib`

Ruff rejects any import of `tomllib` in `src/wio` outside `src/wio/formats/**`,
in every form, and accepts it there and in `tests` and `scripts`.

#### The forms

- **Given** probe files holding `import tomllib`, `from tomllib import loads`,
  `import tomllib.x`, `lazy import tomllib` and `lazy from tomllib import
  loads`.
- **When** each is linted with the repository's ruff configuration as
  `src/wio/config/probe.py`, as `src/wio/formats/probe.py` and as
  `tests/unit/probe.py`.
- **Then** every one is reported as `TID251` the first time, and none the other
  two times.

### **AC-4** Importing the decoder loads no TOML parser

Importing `wio.formats` does not import `tomllib`, and the first call of
`decode_toml` does.

#### A fresh interpreter

- **Given** a new Python process.
- **When** it imports `wio.formats`, checks `sys.modules`, calls `decode_toml`
  and checks again.
- **Then** `tomllib` is absent the first time and present the second.

## Additional context

- [Ruff settings](../../../../../pyproject.toml) hold the banned-api table this
  Work adds.
