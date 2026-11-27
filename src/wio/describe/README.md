# `wio.describe`

`wio.describe` provides the offline, deterministic self-description layer for
`wio`: immutable descriptor models ([models.py](models.py)) and a code-derived
registry ([registry.py](registry.py)).

## Guarantees

- **Offline and config-free.** Building engine or command descriptions performs
  no filesystem or network I/O and requires neither a git repository nor
  `.agents/wio/config.toml`.
- **Deterministic.** Descriptions are frozen dataclasses with sorted command
  lists and no timestamps, so identical installed versions produce identical
  data.
- **No sibling or CLI imports.** To keep the [component dependency
  direction](../README.md#dependency-direction) acyclic, `wio.describe` derives
  live reference data from shared packages (`wio.models.config` for config
  schema keys and `wio.formats.directives` for template directives) rather than
  importing `wio.config` or `wio.cli`.
- **Anti-drift sync.**
  [test_describe_sync.py](../../../tests/tooling/test_describe_sync.py) enforces
  that the descriptor registry stays one-to-one with `wio.cli.table.Component`
  and covers every entry in `wio.cli.table.COMMANDS`.
