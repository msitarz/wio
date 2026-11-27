# `wio.formats`

The single home for file-format parsing, validation, and deterministic
rendering across all `wio` commands.

## Package invariants

- **Library boundary.** `tomllib`, `tomlkit`, `markdown-it-py`, and `difflib`
  are imported only inside this package (enforced by `tach.toml` and tooling
  tests).
- **Deterministic output.** Every renderer sorts its keys and items and emits
  no timestamps (except event log lines).

## The TOML decoder

[`toml.py`](toml.py) wraps `tomllib` so every caller gets uniform line/column
diagnostics instead of raw `TOMLDecodeError` exceptions.

## Event log lines

[`event_lines.py`](event_lines.py) encodes and decodes versioned JSON-lines
events shared by `wio context`, `wio trailers --result`, and `wio log`.

## The directive grammar

[`directives.py`](directives.py) owns the directive table and parser used by
`wio templates directives`, `wio templates check`, and `wio contracts check`.

## The grammar of a reference and the wording of messages

[`grammar.py`](grammar.py) and [`wording.py`](wording.py) parse rule and preset
references (`ruleset`, `ruleset.FAM`, `ruleset.FAM001`, `ruleset.preset`) and
own their error wording.

## The items of a section

[`items.py`](items.py) extracts item ids from contract sections so
`wio contracts check` and `wio trailers` agree on what counts as an item id.

## Editing contract metadata

[`skeleton.py`](skeleton.py) and [`setkeys.py`](setkeys.py) prepare template
skeletons and edit metadata blocks with `tomlkit` without disturbing the body.

## The records of a message

[`records.py`](records.py) implements both the `scan` and `git` trailer readers
and the record renderer.

## The hash of a rule file

[`digest.py`](digest.py) computes the deterministic SHA-256 content hash of a
rule file for `context` and `review` events.

## The layout of blocks

[`blocks.py`](blocks.py) formats indented multi-line text blocks shared by
`wio contracts list` and `wio rules list`.

## Modules

See [`src/wio/formats/`](.) and
[unit tests](../../../tests/unit/formats/) for per-module docstrings and cases.
