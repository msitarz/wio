<!-- wio
id = "ces6tf"
template = "feature.leaf"
roots = ["wio"]
depends_on = ["xtgz9z", "h69nf8"]
-->

# The hierarchy and the dependency graph of the Works

## Purpose

Commands need the parents, children and dependents of a Work, the roots that a
parent collects from its descendants, and a dependency graph without cycles.
These are computed from the layout and the metadata, so that every command gets
the same answer and none drifts from the files.

## Goals

- The parent, children, ancestors and descendants of a Work are known under
  `nesting`, and none exist under `flat`.
- The roots of a Work are known with `@descendants` resolved.
- The dependencies and the dependents of a Work are known.
- A dependency on an id that is not in the tree, and a dependency cycle, are
  each reported once, and a cycle is readable.

## Glossary

- **Implicit dependency**: the wait of a parent for each of its children. No
  `depends_on` lists it, and it counts in the graph.
- **Dependents of a Work**: the Works that list its id in `depends_on`. A
  parent's implicit wait for its child does not make the parent a dependent.

## Non-Goals

- Warnings about roots, such as a leaf that lists `@descendants` or a parent
  whose roots omit a root of a descendant, which the check-works leaf gives from
  the data returned here, and judging a root's name against the config.
- Looking up a removed Work in the history, and which actions of a dependency
  must have run.
- Ordering the delivery of Works, and tracking items of a parent through the
  items of its children.
- Reading any file: the Works come from discovery.

## Assumptions

- **A-1**: The discovery leaf is delivered, so each Work has its path, id, roots
  and dependencies, a lookup by id refuses a shared id, and a Work left out is
  not among them.
- **A-2**: The hierarchy mode is `flat` or `nesting`, as the config guarantees.

## Mechanisms

- A hierarchy in `wio.contracts`, built from the Works that discovery found and
  the hierarchy mode, with the parent, children, ancestors, descendants,
  resolved roots, dependencies and dependents of a Work, and the diagnostics of
  the graph.
- `Work` and `Diagnostic` from `wio.models`, and the ordering of the shared
  leaf.
- A search for the strongly connected groups of the graph, and for one cycle
  through each, in plain Python.
- The names and the signatures above are provisional, for the architecture
  stage to decide.

## Constraints

- **The hierarchy is built on each run.** It comes from the paths and the
  metadata of the Works that are given.
- **The parent is the nearest Work above.** It is the Work of the nearest
  directory above the Work's own that holds one. A plain directory between
  holds no Work and is passed over, so does a directory whose Work was left
  out, and a file beside a Work is never its child. Under `flat` a Work has no
  relatives.
- **Roots are a set.** A Work's resolved roots are its own entries, with
  `@descendants` replaced by the union of what its children's roots resolve to,
  each name once and sorted. A child contributes what its own roots resolve to,
  so a middle parent decides what it passes up.
- **The graph is the listed edges and the implicit ones.** Under `flat` it is
  the listed edges only. An id that is shared by two Works counts as existing: a
  dependency on it is an edge to each of the two, and the duplicate is reported
  once, by discovery.
- **An unknown id is one error for each Work and id.** It is at the Work that
  lists it, and reads ``The dependency `zzzzzz` is not a Work``.
- **A group of Works that wait on each other is one error.** It is at the file
  of the group's Work with the smallest path, and shows the shortest cycle that
  starts at that Work, taking at each step, among equally short ones, the edge
  to the Work with the smallest path. When a pair has a listed and an implicit
  edge, the edge is called listed.
- **A cycle names its edges.** Each step names the id it reaches and says
  whether the edge was listed in `depends_on` or is a parent waiting for its
  child, and a Work that lists its own id is a cycle of one.
- **The output is deterministic.** Children, descendants and dependents are
  sorted by the string of their paths, ancestors run from the nearest,
  dependencies are in the order listed, and the diagnostics are ordered as the
  shared leaf orders them.
- **Nothing is read or written.** It works on the Works it is given.

## Acceptance criteria

In these scenarios a Work is named by its directory, such as `p` for
`p/README.md`.

### **AC-1** Under nesting each Work has a parent, children and descendants

The parent of a Work is the Work of the nearest directory above it that holds
one, its children are the Works whose parent it is, and the rest follows.

#### A tree with a plain directory

- **Given** `hierarchy = "nesting"` and Works `p/README.md`, `p/c1/README.md`,
  `p/c1/d/README.md` and `p/g/x/README.md`, where `p/g` holds no Work, and a
  Work `q/README.md`.
- **When** the hierarchy is built.
- **Then** the parent of `c1` and of `x` is `p`, of `d` is `c1`, and `p` and `q`
  have none, the children of `p` are `c1` and `x` in that order, the ancestors
  of `d` are `c1` and `p`, the descendants of `p` are `c1`, `d` and `x` in the
  order of their paths, and a leaf has no children.

#### A directory whose Work was left out

- **Given** `hierarchy = "nesting"`, a Work `p/README.md`, a file
  `p/m/README.md` whose block does not close, and a Work `p/m/k/README.md`.
- **When** the hierarchy is built.
- **Then** the parent of `k` is `p`.

### **AC-2** Under flat nobody is related

Under `flat`, no Work has a parent, a child, an ancestor or a descendant, and
the graph holds the listed edges only.

#### The same Works

- **Given** `hierarchy = "flat"`, the Works of the first scenario of AC-1 with
  `p` having `roots = ["@descendants", "wio"]`, and `d` listing `p` in
  `depends_on`.
- **When** the hierarchy is built.
- **Then** no Work has a parent, a child, an ancestor or a descendant, `p` has
  the roots `wio` only, and `d` has the one dependency `p` with no diagnostic.

### **AC-3** Roots resolve through the children

`@descendants` is the union of what the children's roots resolve to, and a
middle parent passes up what its own roots resolve to.

#### Resolving

- **Given** `hierarchy = "nesting"` and Works `top/README.md` with
  `roots = ["e2e", "@descendants"]`, `top/mid/README.md` with `roots = ["api"]`,
  `top/mid/deep/README.md` with `roots = ["web"]`, `top/leaf/README.md` with
  `roots = ["db", "db"]`, `top/bad/README.md` whose `roots` was of the wrong
  type and so is empty, and `solo/README.md` that lists `@descendants` and
  `wio`.
- **When** the roots are resolved.
- **Then** `top` has `api`, `db` and `e2e`, `mid` has `api`, `deep` has `web`,
  `leaf` has `db` once, `bad` has none, and `solo`, which has no children, has
  `wio` only.

#### A chain of parents

- **Given** the tree of the previous scenario with `mid` having
  `roots = ["@descendants"]` and `deep` having `roots = ["web"]`.
- **When** the roots are resolved.
- **Then** `mid` has `web`, and `top` has `db`, `e2e` and `web`.

### **AC-4** Dependencies and dependents are the listed ones

The dependencies of a Work are the ids it lists, its dependents are the Works
that list its id, and an id that is not in the tree is an error.

#### Dependents

- **Given** `hierarchy = "nesting"` and Works `a/README.md` that lists `b` and
  `c` by their ids, `d/README.md` that lists `b`, `c/README.md`, and `b` at
  `p/b/README.md`, the child of a parent `p/README.md`.
- **When** the dependents of `b`, `a` and `p` are read.
- **Then** those of `b` are `a` and `d` in the order of their paths, `a` has the
  dependencies `b` and `c` in the order listed, and `p`, which waits for `b`
  implicitly, is not a dependent of `b`.

#### An unknown id and a shared id

- **Given** Works `u1/README.md` and `u2/README.md` that each list `zzzzzz`,
  which no Work has, `u3/README.md` that lists `zzzzzz` and `yyyyyy`, neither of
  which a Work has, a Work `r/README.md` that lists `k3m9xq`, and two Works
  `s1/README.md` and `s2/README.md` that share the id `k3m9xq`.
- **When** the hierarchy is built.
- **Then** there is one error for each of `u1` and `u2`, two for `u3`, each at
  its own file and reading ``The dependency `zzzzzz` is not a Work`` or the same
  with `yyyyyy`, none for `r`, and the dependents of both `s1` and `s2` include
  `r`.

### **AC-5** A dependency cycle is one error with one readable cycle

Each group of Works that wait on each other is reported once at the file of its
first Work, with one cycle through the group and the kind of each edge.

#### A parent that also lists its child

- **Given** `hierarchy = "nesting"`, a parent `p5n2hv` at `p/README.md` that
  lists its child `k3m9xq` at `p/k/README.md` in `depends_on`, and the child
  lists `p5n2hv`.
- **When** the hierarchy is built.
- **Then** the cycle reads
  `Dependency cycle: p5n2hv → k3m9xq (listed in depends_on) → p5n2hv (listed in
  depends_on)`, because a listed edge is called listed.

#### A cycle through a parent

- **Given** `hierarchy = "nesting"`, a parent `p5n2hv` at `p/README.md` and its
  child `k3m9xq` at `p/k/README.md` that lists `p5n2hv` in `depends_on`.
- **When** the hierarchy is built.
- **Then** there is one error at `p/README.md` that reads
  `Dependency cycle: p5n2hv → k3m9xq (a parent waits for its child) → p5n2hv
  (listed in depends_on)`.

#### Overlapping cycles and a self-dependency

- **Given** `hierarchy = "flat"`, a Work `a7b2c4` at `a/README.md` that lists
  `c9d4e6` and `b8c3d5`, Works `c9d4e6` at `b/README.md` and `b8c3d5` at
  `c/README.md` that each list `a7b2c4`, and a Work `s5t3wx` at `s/README.md`
  that lists its own id.
- **When** the hierarchy is built.
- **Then** there are two errors: one at `a/README.md` that reads
  `Dependency cycle: a7b2c4 → c9d4e6 (listed in depends_on) → a7b2c4 (listed in
  depends_on)`, because the Work at `b/README.md` has the smaller path, and with
  no mention of `b8c3d5`, and one at `s/README.md` that reads
  `Dependency cycle: s5t3wx → s5t3wx (listed in depends_on)`.

#### Two separate cycles

- **Given** `hierarchy = "flat"`, a Work `f4g5h6` at `e/README.md` and `e1f2g3`
  at `f/README.md` that list each other, and `w4x5y6` at `t/README.md` and
  `t1v2w3` at `w/README.md` that list each other.
- **When** the hierarchy is built.
- **Then** there are two errors, one at `e/README.md` that starts
  `Dependency cycle: f4g5h6 →` and one at `t/README.md` that starts
  `Dependency cycle: w4x5y6 →`, in that order.

## Additional context

- [Parent and leaf](../../../../../docs/concepts.md#parent-and-leaf),
  [Roots of a Work](../../../../../docs/concepts.md#roots-of-a-work) and
  [Dependencies](../../../../../docs/concepts.md#dependencies) in the concepts
  say how the relations, the roots and the graph are defined.
- A dependency on a Work that was deleted, or that was left out, is an unknown
  id here. The note that reads the history belongs to the `wio trailers` Work.
- The resolve leaf uses the ancestors, and the list and show leaves use the
  parent, the dependencies and the dependents.
