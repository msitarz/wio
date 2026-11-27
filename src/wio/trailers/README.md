# `wio.trailers`

The component behind `wio trailers` (write, `none`, `check`, `fold`). Concepts
and the `Wio-*` record format live in
[docs/concepts.md](../../../docs/concepts.md#records).

## Package invariants

- **Shared shape check.** Commit-time (`check --require`), post-hoc (`check`),
  and write paths all share the record parser and shape validation in
  [`wio.formats`](../formats/README.md#the-records-of-a-message).
- **Commit-time vs. post-hoc strictness.** `check --require` fails on missing
  records (except merge, revert, reapply, fixup, and squash commits; `amend!`
  is checked), unknown names, or hidden `Wio-` lines. Plain `check` only
  enforces shape and warns on names absent from the current config so old
  commits stay valid.
- **Gate reviews in one step.** Passing `--result` on a gate stage validates
  the result against `gates.results`, finds the reviewed commit by walking back
  past pure gate commits, emits `Wio-Judge` (`agent` by default), and appends a
  `review` event via the
  [log sink](../log/README.md#appending-an-event) using
  [`RuleSelector`](../rules/README.md#the-rule-selector) for rule hashes.

## Modules

- Write & gate review: [`write.py`](write.py), [`nowork.py`](nowork.py),
  [`gate.py`](gate.py), [`reviewed.py`](reviewed.py),
  [`validation.py`](validation.py).
- Check & fold: [`check.py`](check.py), [`later.py`](later.py),
  [`fold.py`](fold.py), [`report.py`](report.py), [`errors.py`](errors.py).
- Entry, ports & tests: [`command.py`](command.py), [`ports.pyi`](ports.pyi),
  [unit tests](../../../tests/unit/trailers/).
