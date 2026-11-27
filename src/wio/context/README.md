# `wio.context`

The component behind `wio context <work> <action> <stage>`. It compiles a
deterministic context bundle for an agent session and records a `context`
event.

## Refusing what cannot be trusted

Input validation runs in a fixed order ([`inputs.py`](inputs.py),
[`known_work.py`](known_work.py)):

1. Settings must pass config validation.
2. The requested Work must exist and be readable (same refusal reasons as
   [`wio contracts show`](../contracts/README.md#showing-a-work)).
3. The requested action and stage must be declared in config.

Non-fatal issues emit warnings without blocking delivery: a stage outside the
Work's pipeline ([`pipeline.py`](pipeline.py)), empty Work roots
([`no_roots.py`](no_roots.py)), a bundle body exceeding the configured byte
threshold ([`size_warning.py`](size_warning.py)), or `--output <path>` inside
the worktree ([`delivery.py`](delivery.py)).

## Bundle composition

[`compiler.py`](compiler.py), [`composition.py`](composition.py), and
[`assembly.py`](assembly.py) build the bundle from five parts in order:
metadata/header (with SHA-256 [`bundle_id`](identity.py) over header and body),
stage guidance (goal or skill `SKILL.md` pointer via
[`wio.config`](../config/README.md#finding-a-skill)), resolved contract without
metadata or directive comments, grouped and sorted rules, and the fixed
compaction-reminder closing line. After delivery, [`entry.py`](entry.py)
records a `context` event (with gate start commit and dirty flag from
[`gate_start.py`](gate_start.py) when the stage is a gate).

## Modules

- Command & delivery: [`command.py`](command.py), [`delivery.py`](delivery.py),
  [`size_warning.py`](size_warning.py), [`entry.py`](entry.py),
  [`gate_start.py`](gate_start.py).
- Validation & composition: [`inputs.py`](inputs.py),
  [`known_work.py`](known_work.py), [`pipeline.py`](pipeline.py),
  [`no_roots.py`](no_roots.py), [`compiler.py`](compiler.py),
  [`composition.py`](composition.py), [`assembly.py`](assembly.py),
  [`identity.py`](identity.py), [`heading.py`](heading.py),
  [`guidance.py`](guidance.py), [`section.py`](section.py),
  [`roots.py`](roots.py), [`grouping.py`](grouping.py),
  [`ordering.py`](ordering.py), [`rendering.py`](rendering.py).
- Ports & tests: [`ports.pyi`](ports.pyi),
  [unit tests](../../../tests/unit/context/).
