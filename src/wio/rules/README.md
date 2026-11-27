# `wio.rules`

The component behind `wio rules` (`new`, `list`, `show`, `check`) and the
rule-selection engine used by `wio context` and `wio trailers`. Concepts live
in [docs/concepts.md](../../../docs/concepts.md#rulesets-on-disk); local terms
are in [GLOSSARY.md](GLOSSARY.md).

## Package invariants

- **Read everything, raise nothing for file faults.** Rule and manifest readers
  ([`reading.py`](reading.py), [`manifest.py`](manifest.py)) and
  [`discovery.py`](discovery.py) collect every diagnostic in one pass so
  `wio rules check` reports all faults at once.
- **Deterministic output.** Rulesets sort by name, rules by family, numeric
  code, and code text, and diagnostics by `sort_diagnostics`.
- **No symlink traversal.** Discovery walks `.agents/wio/rules` via
  `walk_markdown` and reports symlinks as errors rather than silently skipping
  them.
- **Four-layer selection.** [`layers.py`](layers.py), [`chooser.py`](chooser.py)
  and [`applicability.py`](applicability.py) apply root presets, stage
  includes/excludes, `rules_always_include`, and `rules_always_exclude` in
  order, then filter by root reachability.

## The rule selector

[`select_rules`](chooser.py) (exposed through [`ports.pyi`](ports.pyi)) gives
`wio context` and `wio trailers` the selected rules and their
[`rule_hash`](../formats/README.md#the-hash-of-a-rule-file) digests for a
stage. [`topics.py`](topics.py) provides the family topics for bundle
rendering.

## Modules

- Discovery & parsing: [`reading.py`](reading.py), [`manifest.py`](manifest.py),
  [`discovery.py`](discovery.py), [`expansion.py`](expansion.py).
- Selection & planning: [`inputs.py`](inputs.py), [`roots.py`](roots.py),
  [`layers.py`](layers.py), [`chooser.py`](chooser.py),
  [`applicability.py`](applicability.py), [`anywhere.py`](anywhere.py),
  [`planning.py`](planning.py), [`topics.py`](topics.py).
- Subcommands & checks: [`command.py`](command.py),
  [`creating.py`](creating.py), [`listing.py`](listing.py),
  [`narrowing.py`](narrowing.py), [`explaining.py`](explaining.py),
  [`showing.py`](showing.py), [`checking.py`](checking.py),
  [`errors.py`](errors.py), [`warns.py`](warns.py).
- Ports & tests: [`ports.pyi`](ports.pyi),
  [unit tests](../../../tests/unit/rules/).
