<!-- wio
id = "ces6tf"
template = "feature.leaf"
roots = ["wio"]
depends_on = ["xtgz9z"]
-->

# The hierarchy and the dependency graph of the Works

## Purpose

Commands need the parents, children and dependents of a Work, the roots that a
parent collects from its descendants, and a dependency graph without cycles.
These are computed from the layout and the metadata, never stored, so that
every command gets the same answer and none drifts from the files.

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
  the data returned here.
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

- **Computed, never stored.** There is no `parent` or `children` key, and the
  hierarchy is built from the paths and the metadata on each run.
- **The parent is the nearest Work above.** It is the Work of the nearest
  directory above the Work's own that holds one. A plain directory between
  holds no Work and is passed over, and a file beside a Work is never its
  child. Under `flat` a Work has no relatives.
- **Roots are a set.** A Work's resolved roots are its own entries, with
  `@descendants` replaced by the union of what its children's roots resolve to,
  each name once and sorted. A child contributes what its own roots resolve to,
  so a middle parent decides what it passes up, and a name is not checked
  against the config here.
- **The graph is the listed edges and the implicit ones.** Under `flat` it is
  the listed edges only. An id that is shared by two Works counts as existing,
  so the duplicate is reported once, by discovery.
- **Every report is one error at one file.** An unknown id is one error at the
  Work that lists it. A group of Works that wait on each other is one error at
  the file of its Work with the smallest path, and shows one cycle that starts
  at that Work.
- **A cycle names its edges.** Each step names the id it reaches and says
  whether the edge was listed in `depends_on` or is a parent waiting for its
  child, and a Work that lists its own id is a cycle of one.
- **The output is deterministic.** Children, descendants and dependents are
  sorted by path, ancestors run from the nearest, and the diagnostics are
  ordered as the shared leaf orders them.
- **Nothing is read or written.** It works on the Works it is given.

## Acceptance criteria

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

### **AC-2** Under flat nobody is related

Under `flat`, no Work has a parent, a child, an ancestor or a descendant, and
the graph holds the listed edges only.

#### The same Works

- **Given** `hierarchy = "flat"`, the Works of the previous scenario, and `d`
  listing `p` in `depends_on`.
- **When** the hierarchy is built.
- **Then** no Work has a relative, `@descendants` resolves to nothing, and `d`
  has the one dependency `p` with no diagnostic.

### **AC-3** Roots resolve through the descendants

`@descendants` is the union of what the descendants' roots resolve to, and a
middle parent passes up what its own roots resolve to.

#### Resolving

- **Given** `hierarchy = "nesting"`, a Work `top` with
  `roots = ["e2e", "@descendants"]`, a child `mid` with `roots = ["api"]` that
  has a child `deep` with `roots = ["web"]`, a child `leaf` with
  `roots = ["db", "db"]`, a child `bad` whose `roots` was of the wrong type and
  so is empty, and a Work `solo` that lists `@descendants` and `wio`.
- **When** the roots are resolved.
- **Then** `top` has `api`, `db` and `e2e`, `mid` has `api`, `deep` has `web`,
  `leaf` has `db` once, `bad` has none, and `solo`, which has no children, has
  `wio` only.

#### A chain of parents

- **Given** `top` and `mid` both with `roots = ["@descendants"]` and `deep` with
  `roots = ["web"]`.
- **When** the roots are resolved.
- **Then** `mid` and `top` both have `web`.

### **AC-4** Dependencies and dependents are the listed ones

The dependencies of a Work are the ids it lists, its dependents are the Works
that list its id, and an id that is not in the tree is an error.

#### Dependents

- **Given** Works `a` listing `b` and `c`, `d` listing `b`, and `b` the child
  of a parent `p`.
- **When** the dependents of `b`, `a` and `p` are read.
- **Then** those of `b` are `a` and `d` in the order of their paths, `a` has the
  dependencies `b` and `c`, and `p`, which waits for `b` implicitly, is not a
  dependent of `b`, and `p` and `b` are not dependents of each other.

#### An unknown id and a shared id

- **Given** a Work that lists `zzzzzz`, which no Work has, and a Work that lists
  `k3m9xq`, which two Works share.
- **When** the hierarchy is built.
- **Then** there is one error at the first Work that names `zzzzzz`, and none
  for the second.

### **AC-5** A dependency cycle is one error with one readable cycle

Each group of Works that wait on each other is reported once at the file of its
first Work, with one cycle through the group and the kind of each edge.

#### A cycle through a parent

- **Given** `hierarchy = "nesting"`, a parent `p5n2hv` at `p/README.md` and its
  child `k3m9xq` at `p/k/README.md` that lists `p5n2hv` in `depends_on`.
- **When** the hierarchy is built.
- **Then** there is one error at `p/README.md` that reads
  `Dependency cycle: p5n2hv → k3m9xq (a parent waits for its child) → p5n2hv
  (listed in depends_on)`.

#### Overlapping cycles and a self-dependency

- **Given** Works `a` that lists `b` and `c`, `b` and `c` that each list `a`,
  and a Work `s` that lists its own id.
- **When** the hierarchy is built.
- **Then** there are two errors: one at `a`, with one cycle that starts at `a`
  and none of the other, and one at `s` that reads
  `Dependency cycle: <id> → <id> (listed in depends_on)`.

#### Two separate cycles

- **Given** two pairs of Works that list each other, in different directories.
- **When** the hierarchy is built.
- **Then** there are two errors, one at the first file of each pair, in the
  order of their paths.

## Additional context

- [Parent and leaf](../../../../../docs/concepts.md#parent-and-leaf),
  [Roots of a Work](../../../../../docs/concepts.md#roots-of-a-work) and
  [Dependencies](../../../../../docs/concepts.md#dependencies) in the concepts
  say how the relations, the roots and the graph are defined.
- A dependency on a Work that was deleted is an unknown id here. The note that
  reads the history belongs to the `wio trailers` Work.
- The resolve leaf uses the ancestors, and the list and show leaves use the
  parent, the dependencies and the dependents.
