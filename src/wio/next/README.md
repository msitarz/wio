# `wio.next`

`wio.next` implements the Next step advisor (`wio next`), starting with
chronological `Wio-*` history reading and revert dropping
([history.py](history.py)).

## Guarantees

- **Chronological effective records.** `read_effective_records` walks
  first-parent commits via `wio.io.ports.History`, parses `Wio-*` trailers with
  `wio.formats.records.read` using the configured `trailers.reader` (`scan` or
  `git`), preserves in-commit record order, skips commits without records,
  malformed records, and `Wio-Work: none`, and returns immutable
  `EffectiveRecord` values oldest-to-newest (verified by
  [test_history.py](../../../tests/unit/next/test_history.py)).
- **Revert dropping and restoration.** Standard git revert lines
  (`This reverts commit <sha>.`, matching full or unique prefix SHAs) drop the
  reverted commit's records while keeping any `Wio-*` records on the revert
  commit itself; reverts naming a SHA absent from the walked history are
  ignored, and a revert of a revert restores the original commit's records.
- **Read-only and deterministic.** `wio.next` never writes to the working tree,
  git repository, or event log, and produces identical output for identical
  inputs with no timestamps.
- **Architecture boundary.** `wio.next` follows the
  [component dependency direction](../README.md#dependency-direction) enforced
  by `tach.toml` and imports no sibling components or `wio.cli`.
