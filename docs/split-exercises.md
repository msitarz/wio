# Split exercises

These exercises split an outcome into Works on paper. They test whether the
pieces planned for v0.1 (the Work tree, `depends_on`, inherited sections,
actions and rules) fit real workflows, and they collect what they showed. The
Works, ids and paths are invented for illustration. Terms are in the
[glossary](../GLOSSARY.md) and the model is in [concepts](concepts.md).

The split procedure itself is a skill, a candidate for a later version, and not
a feature of the engine. wio only reads its result: the directory layout and the
metadata.

## The model the exercises use

- A Work is a directory with a contract. The tree is the hierarchy, and a Work
  with child directories is a parent.
- `depends_on` is an array of Work ids. Together with an implicit edge from each
  child to its parent, it forms a graph for delivery.
- Defining runs top-down. Delivering runs bottom-up, in batches that can run in
  parallel.
- A contract inherits its template's actions, and its own `[actions]` replace
  them in full.
- Parents pass their Glossary and Constraints to their children.

## Exercise 1: a nested split

The outcome: an agent gets the context for a stage with one command. The parent
has five child Works:

```text
.agents/wio/works/context/                (parent, id c4n7xt)
  bundle-model/      id b2m5qa   types only: the bundle's sections and header
  rule-files/        id r7f3kd   read and validate rule files
  rule-selection/    id s9t2wy   select by root, type, stage tags  depends_on r7f3kd
  bundle-render/     id d4r8hz   deterministic text output         depends_on b2m5qa
  context-command/   id x6c1ne   wires inputs to a printed bundle  depends_on s9t2wy, d4r8hz
```

After the parent is defined and split, each child starts as a stub: an id, a
template, a title, a seed sentence and an `[actions]` block with only `define`.
The parent has no root, and the leaves have one.

**Inherited by every leaf:** the parent's Constraints (the same inputs give
identical bytes; an unknown Work or stage fails loudly and never yields an empty
bundle) and its Glossary (bundle, stage, rule code).

### Behaviors, split between parent and leaves

- The parent's criteria are system-level: the command prints the right bundle
  for a Work and stage on real files; two runs give identical bytes; an unknown
  Work or stage exits non-zero with no bundle.
- The leaves' criteria are local: `rule-selection` filters by root, by type and
  by all-of tags; `bundle-render` fixes the order of sections and builds the
  bundle id from the text; `context-command` wires the pieces and exits non-zero
  for unknown input.
- Determinism is established by two leaves and verified only at the parent.

**Order.** Define: the parent, then its five stubs. Deliver, as batches:
`(bundle-model, rule-files)`, `(rule-selection, bundle-render)`,
`(context-command)`, and then the parent, whose pipeline is integration and a
system-level review. Its pull request reads `ID: c4n7xt`, `Action: deliver`,
`Stage: integration`, `Criteria: AC-1, AC-2, AC-3`.

### What exercise 1 showed

1. A boundary shared by several leaves needs an owner. Making it a leaf of its
   own (`bundle-model`), delivered first, keeps ordering at the level of Works.
2. A dependent's definition wants the dependency's contract as context.
   Defining could hold back on dependencies while independent stubs are defined
   in parallel.
3. The parent's Constraints are written before the children exist. A leaf that
   finds one wrong sends the work back to the parent's define action, where it
   is amended. Which siblings to redo is the driver's call.
4. Nothing links a parent's criterion to the child criteria that establish it.

### Architecture comes from a designated leaf

The split procedure designates one leaf to produce the architecture for the
whole outcome, and the other leaves depend on it. In the example that is
`bundle-model`.

- Its contract states **invariants, not signatures**: every public boundary is
  typed, dependencies point inward. The artifact is the stubs (`.pyi` or the
  equivalent in another language), in the proper directories.
- Later leaves change those files in their own pull requests, so they never
  amend the first leaf's contract. The architecture evolves with each leaf.
- The procedure can limit itself to constraints and boundaries and leave each
  leaf to architect its own part.
- It fits the overrides: the boundary leaf can use
  `[actions] deliver = ["architecture", "architecture-review"]`, ordinary leaves
  the full pipeline, and the parent `["integration", "system-review"]`.
- The driver's preferences become written constraints. If a leaf finds one
  unworkable (say asyncio does not suit the outcome), that is a signal to the
  driver that the choice was wrong, and the answer ranges from an amendment to
  resetting everything to stubs.
- A review rule can ask that a change to boundary files owned by another Work be
  justified against the parent's constraints.
- The boundary leaf should see its siblings' contracts. For now the stage goal
  or the skill tells the agent to read them, because `wio context` injects only
  the parent's inheritable sections.
- Leaves in one parallel batch can touch the same files, and wio cannot see it.
  The procedure should give leaves separate modules where it can, and git
  reports the conflicts that remain.

## Exercise 2: a flat split

The outcome: rules have stable codes and families. The slices are siblings with
no parent:

```text
.agents/wio/works/
  rule-families/       id f3a9kx   a ruleset declares families and prefixes
  rule-codes/          id c8d2mq   rule files carry code and name, validated     depends_on f3a9kx
  rule-new/            id n5w7ze   assigns the next free code in a family         depends_on c8d2mq
  code-in-bundle/      id g2h6vb   bundles and verdicts show code and name        depends_on c8d2mq
  stable-rule-codes/   id s1x4pr   the original outcome, kept as the last Work     depends_on n5w7ze, g2h6vb
```

The batches are `(rule-families)`, `(rule-codes)`, `(rule-new, code-in-bundle)`
and `(stable-rule-codes)`. Everything is a `depends_on`, so no implicit edge is
needed.

### What exercise 2 showed

- The original Work can become the last one, carrying the end-to-end criteria
  with `deliver = ["integration", "system-review"]`, or it can be abandoned.
  Nothing in wio requires either.
- Inheritance is lost. The slices are not under the original, so its
  Constraints and Glossary do not reach them. They would be copied into each
  slice, where they drift, or linked by hand.
- A flat split is lighter than a nested one, and it is a choice of the split
  procedure. A way to pass inheritable sections along `depends_on` could close
  the gap later.

## Exercise 3: a split found during delivery

`rule-selection` (id `s9t2wy`) is a leaf whose `architecture` pull request is
merged and whose review is under way. The agent finds two independent pieces:
filtering by root and type, and matching tags. `context-command` depends on it.

**Procedure A, promote in place.** The Work keeps its id and becomes a parent:

```text
before:  context/rule-selection/                  (leaf s9t2wy)
after:   context/rule-selection/                  (parent, still s9t2wy)
           scope-filtering/   id v6k2jd           (stub)
           tag-matching/      id m3p8cu           (stub)
```

- The leaf's criteria were already the outcome, so they become the parent's
  system-level criteria. The skill adds Constraints and Visuals, removes `root`
  and switches `template` to the parent template. Each child starts as a stub.
- Dependents need no change: `context-command` depends on `s9t2wy`, which still
  means the whole outcome.
- The merged `architecture` lines for `s9t2wy` stay in the history. The
  parent's pipeline is `["integration", "system-review"]`, which does not
  contain `architecture`, so `wio next` ignores them.
- The parent now waits for its children. A child whose artifact already exists
  can override its pipeline to skip `architecture`.

**Procedure B, wrap.** A new parent goes above, the old leaf is narrowed to one
piece, and the other piece becomes a stub. The dependents have to be re-pointed,
because the old id now means something narrower, and the new parent's contract
is written from scratch.

Use A when one outcome turns out to be several. Use B when the scope grew upward
and a new overarching outcome appears. wio does not care which.

### What exercise 3 showed

1. Define and deliver are enough. The restructuring pull request is
   `Action: define`, with the split stage.
2. Invariants do the work afterwards: the new template's sections are present,
   dependency ids exist, and there are no cycles. A child that depends on its
   own parent is a cycle, because the parent waits for its children.
3. A merged stage counts only if it belongs to the Work's current pipeline for
   that action. That is enough when the parent's and the leaf's pipelines use
   different stage names, so `integration` for parents and `implementation` for
   leaves is a convention worth following. The reset needed otherwise belongs to
   the custom actions that come after v0.1.
4. A way to list the dependents of an id would help any restructuring. It can
   be computed from the existing metadata.
5. A review session in progress is recorded in the local event log, which is
   personal and not authoritative.

## Summary

### For v0.1

- Delivery is a graph of Works: the tree plus `depends_on`. Stages of different
  Works do not interleave.
- A shared boundary is a leaf of its own, delivered first. The other leaves
  depend on it.
- Define and deliver cover splitting and restructuring.
- Promote in place when one outcome turns out to be several.
- Use different stage names for parent and leaf pipelines.

### Gaps to close later

- Parent constraints and criteria do not trace to the child criteria that
  establish them (v0.2 or v0.3).
- Sibling contracts are not injected into context.
- A flat split has no channel for shared constraints.
- A helper that lists the dependents of an id.
- Leaves in a batch can touch the same files.
