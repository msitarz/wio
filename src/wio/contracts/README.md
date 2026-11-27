# `wio.contracts`

The component behind `wio contracts` (`new`, `list`, `show`, `check`,
`skeleton`). Concepts live in
[docs/concepts.md](../../../docs/concepts.md#what-it-is); local terms are in
[GLOSSARY.md](GLOSSARY.md).

## Package invariants

- **Read-only on existing contracts.** `wio contracts new` creates a Work, and
  no subcommand rewrites an existing contract file.
- **Single-parser boundary.** TOML and Markdown parsing stay in
  [`wio.formats`](../formats/README.md); this package consumes parsed blocks,
  headings, and directives through it.
- **Shared template validation.** Template problems are reported by
  `wio templates check`; `wio contracts check` points there instead of
  repeating template diagnostics.

## The group

[`command.py`](command.py) wires the five subcommands under `wio contracts`,
loading settings once and delegating to the subcommand modules.

## Listing the Works

[`listing.py`](listing.py) prints each Work's id, title, template, path, and
only its own roots, dependencies, and `[actions]` overrides (never inherited
values or status). Under `nesting`, children are indented under their parent;
under `flat`, it prints a plain sorted list. An unreadable tree or duplicate id
exits 2.

## Showing a Work

[`showing.py`](showing.py) accepts an id or a path (anything with `/` or ending
in `.md`) and prints the Work's facts, actions with pipeline sources, resolved
roots, dependents, and resolved contract. Non-Work paths fail with the exact
reason from
[Which files are Works](../../../docs/concepts.md#which-files-are-works).

## The resolved view of a Work

[`resolve.py`](resolve.py) merges inheritable ancestor sections into a contract
in ancestor-to-descendant order without mutating the source files.

## Looking up a Work for a record

[`lookup.py`](lookup.py) resolves a Work by id for `wio trailers` and
`wio context`, exposing its roots, action pipelines, and own item ids.

## Modules

- Tree & discovery: [`discovery.py`](discovery.py),
  [`hierarchy.py`](hierarchy.py), [`lookup.py`](lookup.py),
  [`resolve.py`](resolve.py).
- Subcommands: [`command.py`](command.py), [`creation.py`](creation.py),
  [`listing.py`](listing.py), [`showing.py`](showing.py),
  [`skeleton.py`](skeleton.py), [`checking.py`](checking.py),
  [`body.py`](body.py).
- Ports & tests: [`ports.pyi`](ports.pyi),
  [unit tests](../../../tests/unit/contracts/).
