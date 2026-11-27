<!-- wio
id = "et1n2v"
template = "feature.leaf"
roots = ["wio"]
depends_on = ["cthw24"]
-->

# Work state, gate-pass and staleness evaluator

## Purpose

Compute the next action, stage, readiness and blocking reasons for every active
Work from its contract, resolved pipelines, config rules and effective history
records.

## Goals

- Order each Work's non-on-demand actions by `after` (ties by name) and walk
  each action's stage pipeline in order.
- Treat a gate stage as passed only when its latest effective record has
  `Wio-Result: pass` (and `Wio-Judge: human` when `stage.judge == "human"`);
  any other result (`fail`, `unknown`) proposes redoing the previous stage (or
  retrying the gate if first).
- Invalidate an action when a newer effective record matches its
  `invalidated_by` entries (including `@descendants:<action>` and
  `@dependencies:<action>`).
- Mark a Work blocked when any `depends_on` Work is not yet done or, for a
  parent's `deliver` action, when any child Work is not yet delivered.

## Non-Goals

- Reading git history directly (owned by `cthw24`).
- CLI argument parsing or text/JSON rendering (owned by `rqms5z`).

## Assumptions

None.

## Mechanisms

- `src/wio/next/state.py` (provisional) defines `NextStep`, `WorkStatus`
  (`ready`, `blocked`, `done`) and `evaluate_next(works, records, config) ->
  tuple[NextStep, ...]`.

## Constraints

None beyond those inherited from `45f1sa`.

## Acceptance criteria

### **AC-1** Action order and pipeline progression

For a Work with no records, `evaluate_next` proposes the first stage of its
first non-on-demand action; once a non-gate stage has a record, it proposes the
next stage; once a gate passes, it advances to the next stage or next action.

### **AC-2** Gate failures and human-judged gates

A gate with `fail` or `unknown` proposes redoing the preceding stage; a gate
with `judge = "human"` is not cleared by `Wio-Judge: agent` and waits for a
`Wio-Judge: human` `pass`.

### **AC-3** Invalidation marks actions stale

A newer record matching an action's `invalidated_by` (direct action,
`@descendants:<action>`, or `@dependencies:<action>`) resets that action so
`evaluate_next` proposes starting it again.

### **AC-4** Parallel readiness and blocking reasons

Independent ready Works are all returned as `ready` in deterministic order; a
Work waiting on `depends_on` or incomplete children is returned as `blocked`
naming the blocking Work ids.
