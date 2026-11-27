# `wio.describe`

`wio.describe` provides the offline, deterministic self-description command
`wio describe [<command>] [--json]`: immutable descriptor models
([models.py](models.py)), a code-derived registry ([registry.py](registry.py)),
text and JSON renderers ([render.py](render.py)), and the CLI command handler
([command.py](command.py)).

## Guarantees

- **Offline and config-free.** Building and rendering engine or command
  descriptions performs no filesystem or network I/O and requires neither a git
  repository nor `.agents/wio/config.toml`.
- **Deterministic output.** Descriptions are frozen dataclasses with sorted
  command lists and no timestamps; text and single-line JSON (via
  `wio.formats.encode_json`) end in a single newline and are byte-for-byte
  identical for identical installed versions.
- **Lazy CLI wiring.** `wio.cli.table` loads `DescribeCommand` lazily so other
  subcommands pay no startup cost.
- **No sibling or CLI imports.** To keep the [component dependency
  direction](../README.md#dependency-direction) acyclic, `wio.describe` derives
  live reference data from shared packages (`wio.models.config` for config
  schema keys and `wio.formats.directives` for template directives) rather than
  importing `wio.config` or `wio.cli`.
- **Anti-drift sync.**
  [test_describe_sync.py](../../../tests/tooling/test_describe_sync.py) enforces
  that the descriptor registry stays one-to-one with `wio.cli.table.Component`
  and covers every entry in `wio.cli.table.COMMANDS`.
