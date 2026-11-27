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
  each action's stage pipeline in order, marking a Work `done` once all
  non-on-demand actions pass.
- Treat a gate stage as passed only when its latest effective record has
  `Wio-Result: pass` (and `Wio-Judge: human` when `stage.judge == "human"`);
  any other result (`fail`, `unknown`) proposes redoing the previous stage (or
  retrying the gate if it is the first stage of the action).
- Invalidate an action when a newer effective record matches its
  `invalidated_by` entries (including `@descendants:<action>` and
  `@dependencies:<action>`).
- Mark a Work `blocked` when any `depends_on` Work is not yet `done` or, for a
  parent's `deliver` action, when any child Work is not yet delivered.

## Non-Goals

- Reading git history directly (owned by `cthw24`).
- CLI argument parsing or text/JSON rendering (owned by `rqms5z`).

## Assumptions

None.

## Mechanisms

- `src/wio/next/state.py` (provisional) defines `WorkStatus = Literal["ready",
  "blocked", "done"]`, frozen dataclass `NextStep(work_id: str, title: str |
  None, status: WorkStatus, action: str | None, stage: str | None, reason: str,
  blocked_by: tuple[str, ...])`, and `evaluate_next(works:
  Sequence[WorkSummary], records: Sequence[EffectiveRecord], config: Config) ->
  tuple[NextStep, ...]`.

## Constraints

None beyond those inherited from `45f1sa`.

## Acceptance criteria

### **AC-1** Action order, pipeline progression and completion

`evaluate_next` skips `on_demand` actions, orders remaining actions by `after`
(ties by name), proposes the first stage when no record exists, advances past a
non-gate stage once recorded, advances past a gate once passed, and returns
`status="done"` (`action=None`, `stage=None`) when all non-on-demand actions
have passed.

### **AC-2** Gate failures, first-stage gate retry and human-judged gates

A gate whose latest effective record has `fail` or `unknown` proposes redoing
the preceding stage (or retrying the gate itself when it is the first stage of
the action); a gate with `judge = "human"` is not cleared by `Wio-Judge: agent`
and waits for a `Wio-Judge: human` `pass`.

### **AC-3** Invalidation marks actions stale

A newer effective record matching an action's `invalidated_by` (direct action,
`@descendants:<action>`, or `@dependencies:<action>`) resets that action so
`evaluate_next` proposes starting it again.

### **AC-4** Parallel readiness, deterministic ordering and blocking boundaries

Independent ready Works are all returned with `status="ready"` sorted by
`work_id`; a Work waiting on an incomplete `depends_on` Work, or a parent
entering `deliver` with incomplete children, is returned with `status="blocked"`
and `blocked_by` listing the blocking Work ids sorted by id; a `depends_on` id
not present in `works` is treated as satisfied (retired), and dependency cycles
mark the involved Works `blocked`.
