# Split exercises

These exercises split an outcome into Works on paper. They test whether the
pieces planned for v0.1 (the Work tree, `depends_on`, inherited sections,
actions, roots and rules) fit real workflows, and they collect what they showed.
The Works, ids and paths are invented for illustration. Terms are in the
[glossary](../GLOSSARY.md) and the model is in [concepts](concepts.md).

The split procedure itself is a skill, a candidate for a later version, and not
a feature of the engine. wio only reads its result: the directory layout and the
metadata.

## The model the exercises use

- A Work is a directory with a contract. The tree is the hierarchy, and a Work
  with child Works is a parent.
- `depends_on` is an array of Work ids. Together with an implicit dependency of
  each parent on its children, it forms a graph for delivery.
- Defining runs top-down. Delivering runs bottom-up, in batches that can run in
  parallel.
- The project declares the actions `define` and `deliver`. A contract inherits
  its template's actions, and each action its own `[actions]` names replaces
  the template's.
- A new Work starts from its type's entry template. Define stages select the
  `contract` root, so they get the rules for writing contracts.
- A leaf names its roots. A parent without declared roots uses the union of its
  leaves' roots.
- Parents pass their Glossary and Constraints to their children.
- Every commit of a stage carries a record of `Wio-*` trailers.

## Exercise 1: a nested split

The outcome: an agent gets the context for a stage with one command. The parent
has five child Works:

```text
.agents/wio/works/context/                (parent, id c4n7xt)
  bundle-model/      id b2m5qa   types only: the bundle's sections and header
  rule-files/        id r7f3kd   read and validate rule files
  rule-selection/    id s9t2wy   select by roots, type, stage tags  depends_on r7f3kd
  bundle-render/     id d4r8hz   deterministic text output          depends_on b2m5qa
  context-command/   id x6c1ne   wires inputs to a printed bundle   depends_on s9t2wy, d4r8hz
```

After the parent is defined, which includes its split, each child is created
from the entry template: an id, a template, a title and a seed sentence, and the
roots when the split already knows them. The entry template requires little, so
the children pass `wio contract check` before they are defined. The parent
lists `roots = ["@descendants"]`, from its template, so its roots are the union
of its descendants' roots.

**Inherited by every leaf:** the parent's Constraints (the same inputs give
identical bytes; an unknown Work or stage fails loudly and never yields an empty
bundle) and its Glossary (bundle, stage, rule code).

### Behaviors, split between parent and leaves

- The parent's criteria are system-level: the command prints the right bundle
  for a Work and stage on real files; two runs give identical bytes; an unknown
  Work or stage exits non-zero with no bundle.
- The leaves' criteria are local: `rule-selection` filters by roots, by type and
  by all-of tags; `bundle-render` fixes the order of sections and builds the
  bundle id from the text; `context-command` wires the pieces and exits non-zero
  for unknown input.
- Determinism is established by two leaves and verified only at the parent.

**Order.** Define: the parent, then its five children. Deliver, as batches:
`(bundle-model, rule-files)`, `(rule-selection, bundle-render)`,
`(context-command)`, and then the parent, whose pipeline is integration and a
system-level review. Its integration commit carries the record:

```text
Wio-Work: c4n7xt
Wio-Action: deliver
Wio-Stage: integration
Wio-Criteria: AC-1, AC-2, AC-3
```

### What exercise 1 showed

1. A boundary shared by several leaves needs an owner. Making it a leaf of its
   own (`bundle-model`), delivered first, keeps ordering at the level of Works.
2. A dependent's definition wants the dependency's contract as context.
   Defining could hold back on dependencies while independent children are
   defined in parallel.
3. The parent's Constraints are written before the children exist. A leaf that
   finds one wrong asks for the parent to be amended, through the parent's
   amend action. Which siblings to redo is the driver's call.
4. Nothing links a parent's criterion to the child criteria that establish it.

### Architecture comes from a designated leaf

The split procedure designates one leaf to produce the architecture for the
whole outcome, and the other leaves depend on it. In the example that is
`bundle-model`.

- Its contract states **invariants, not signatures**: every public boundary is
  typed, dependencies point inward. The artifact is the stubs (`.pyi` or the
  equivalent in another language), in the proper directories.
- Later leaves change those files in their own commits, so they never amend the
  first leaf's contract. The architecture evolves with each leaf.
- The procedure can limit itself to constraints and boundaries and leave each
  leaf to architect its own part.
- It fits the overrides: the boundary leaf can use
  `[actions] deliver = ["architecture", "architecture-review"]`, ordinary leaves
  the full pipeline, and the parent `["integration", "system-review"]`.
- The driver's preferences become written constraints. If a leaf finds one
  unworkable (say asyncio does not suit the outcome), that is a signal to the
  driver that the choice was wrong, and the answer ranges from an amendment to
  resetting everything to fresh Works.
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
  code-in-bundle/      id g2h6vb   bundles and reviews show code and name         depends_on c8d2mq
  stable-rule-codes/   id s1x4pr   the original outcome, kept as the last Work     depends_on n5w7ze, g2h6vb
```

The batches are `(rule-families)`, `(rule-codes)`, `(rule-new, code-in-bundle)`
and `(stable-rule-codes)`. Everything is a `depends_on`, so no implicit edge is
needed.

### What exercise 2 showed

- The original Work can become the last one, carrying the end-to-end criteria
  with a pipeline of its own for end-to-end checks and a review. It is not a
  parent, so the parents' `integration` stage, which joins children, does not
  fit it. Or it can be abandoned by deleting it, after its dependents are
  updated. Nothing in wio requires either.
- Inheritance is lost. The slices are not under the original, so its
  Constraints and Glossary do not reach them. They would be copied into each
  slice, where they drift, or linked by hand.
- A flat split is lighter than a nested one, and it is a choice of the split
  procedure. A way to pass inheritable sections along `depends_on` could close
  the gap later.

## Exercise 3: a split found during delivery

`rule-selection` (id `s9t2wy`) is a leaf whose `architecture` stage has a
record and whose review is under way. The agent finds two independent pieces:
filtering by roots and type, and matching tags. `context-command` depends on it.

**Procedure A, promote in place.** The Work keeps its id and becomes a parent:

```text
before:  context/rule-selection/                  (leaf s9t2wy)
after:   context/rule-selection/                  (parent, still s9t2wy)
           scope-filtering/   id v6k2jd           (new, from the leaf template)
           tag-matching/      id m3p8cq           (new, from the leaf template)
```

- The leaf's criteria move to the children that can establish them: filtering to
  `scope-filtering`, matching to `tag-matching`. A parent states only
  system-level guarantees (rule ACC006), so the parent gets new criteria for
  what only the joined result establishes, such as "a stage gets exactly the
  rules that pass both filters". The skill adds Constraints and Visuals, sets
  the parent's roots to `["@descendants"]` in place of the leaf's own, and
  switches `template` to the parent template. Each child that takes over
  criteria is created from the leaf template
  (`wio contract new feature --template feature.leaf --parent s9t2wy`), because
  the draft has no place for them.
- Dependents need no change: `context-command` depends on `s9t2wy`, which still
  means the whole outcome.
- The `architecture` record for `s9t2wy` stays in the history. The parent's
  pipeline is `["integration", "system-review"]`, which does not contain
  `architecture`, so `wio next` ignores it.
- The parent now waits for its children. A child whose artifact already exists
  can override its pipeline to skip `architecture`.

**Procedure B, wrap.** A new parent goes above, the old leaf is narrowed to one
piece, and the other piece becomes a new Work. The dependents have to be
re-pointed, because the old id now means something narrower, and the new
parent's contract is written from scratch.

Use A when one outcome turns out to be several. Use B when the scope grew upward
and a new overarching outcome appears. wio does not care which.

### What exercise 3 showed

1. Define and deliver are enough. The restructuring commit records
   `Wio-Action: define` with `Wio-Stage: define`: a restructure is the Work
   being defined again. Its record makes `review-contract` stale, and, through
   `invalidated_by`, the Work's delivery too.
2. Invariants do the work afterwards: the new template's sections are present,
   dependency ids exist, and there are no cycles. A child that depends on its
   own parent is a cycle, because the parent waits for its children.
3. A record counts only if its stage belongs to the Work's current pipeline for
   that action. That is enough when the parent's and the leaf's pipelines use
   different stage names, so `integration` for parents and `implementation` for
   leaves is a convention worth following. When the names coincide, the old
   records count, and the driver decides whether to redo the stages. Because
   the latest record wins, redoing an earlier stage makes the later ones stop
   being current.
4. Restructuring needs the dependents of an id. `wio contract show` lists them,
   computed from the metadata.
5. A review session in progress is recorded in the local event log, which is
   personal and not authoritative.

## Exercise 4: rules across a Work's life

The outcome: users can log in. It touches a FastAPI backend and a Next.js
frontend. The config has three roots, `api`, `web` and `contract`, and every
define stage has `roots = ["contract"]`. The workflow asks for one root per
leaf, so the outcome becomes a parent with two leaves.

| # | Session | Roots the stage selects | Rules |
| --- | --- | --- | --- |
| 1 | Define the new Work, which has no roots yet | `contract` | writing contracts |
| 2 | Split it into parent P with leaves L1 and L2 | `contract` | writing contracts |
| 3 | Define L1; the stage sets `roots = ["api"]` | `contract` | writing contracts |
| 4 | Deliver L1's `architecture` | the Work's roots: `api` | Python and FastAPI |
| 5 | Deliver P's `integration` | the Work's roots: the union of `api` and `web` | both, grouped by root |
| 6 | Amend L1 with its amend action | `contract` | writing contracts |
| 7 | Deliver a leaf that was never defined | the Work's roots, which are empty | none: a loud error |

### What exercise 4 showed

- The root a stage edits decides its rules, not the Work alone. Storing
  `roots = ["contract"]` on the contract while it is defined would give session
  6 the code rules, and session 7 the contract rules without an error.
- A Work's `roots` stays pure intent: where its code lives. It can be empty
  until definition decides it, and no check fails until a stage needs it.
- A parent's bundle mixes toolchains. Grouping the rules under a line that names
  each root and its paths tells the agent which files each rule is for.
- One root per leaf is the workflow's choice. A parent that lists
  `roots = ["e2e", "@descendants"]` for its integration stage is equally valid:
  it gets its children's `api` and `web` and adds `e2e`.

## Summary

### For v0.1

- Delivery is a graph of Works: the tree plus `depends_on`. Stages of different
  Works do not interleave.
- A shared boundary is a leaf of its own, delivered first. The other leaves
  depend on it.
- Define and deliver cover splitting and restructuring.
- Promote in place when one outcome turns out to be several.
- Use different stage names for parent and leaf pipelines.
- Define stages select the `contract` root. Other stages select the Work's
  roots.

### Gaps to close later

- Parent criteria do not trace to the child criteria that establish them (v0.2
  or v0.3). The proposal is in
  [concepts](concepts.md#tracking-criteria-planned). Parent constraints are not
  covered.
- Sibling contracts are not injected into context.
- A flat split has no channel for shared constraints.
- Leaves in a batch can touch the same files. The scope check planned for v0.2
  shows when a leaf touches files outside its roots.
