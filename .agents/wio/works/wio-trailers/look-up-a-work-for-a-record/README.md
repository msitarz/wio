<!-- wio
id = "jzvrtx"
template = "feature.leaf"
roots = ["wio"]
depends_on = []
-->

# Look up a Work for a record

## Purpose

A record refers to a Work by id, and the write command and the commit-time check
must find that Work's items and pipeline in the same places, so that a Work
that the commit deletes is still found.

## Goals

- The item ids and the pipelines of a Work are found by the Work's id.
- A Work is found in the working tree or in the index, and otherwise in `HEAD`.
- A Work that is nowhere is reported as absent, not as a Work with no items.

## Non-Goals

- Judging a record against what the lookup finds; the validator leaf does that.
- Reading a Work that is not named by a record, such as listing the Works.

## Assumptions

None.

## Mechanisms

- **The adapter of the `Contracts` port** — the adapter of the provisional port
  of `src/wio/trailers/ports.pyi`, whose `items` and `pipeline` it implements
  for the working tree or for the index, each falling back to `HEAD`.
- **`History` port** — gives the Works of `HEAD` through `list_files` and
  `show`.
- **Contracts component** — resolves a Work's template, its own sections' item
  ids and the stages of its actions, as `wio contracts show` does.

## Acceptance criteria

The examples use a Work `k3m9xq`, a leaf under a parent that has a constraint
`C-1`, with the items `AC-1` and `AC-3` in its own sections. Its `deliver` is
the `typed-boundary` stage preset, which lists `architecture`,
`architecture-review`, `wiring`, `wiring-review`, `implementation`,
`implementation-review`, `promote-docs` and `docs-review` in that order.

### **AC-1** The items of a Work are its own

#### A Work in the working tree

- **Given** `k3m9xq` in the working tree.
- **When** `items("k3m9xq")` runs on the working-tree adapter.
- **Then** it returns `AC-1` and `AC-3` and not `C-1`.

### **AC-2** The pipeline of an action is found in order

#### An action the Work has, and one it lacks

- **Given** `k3m9xq` in the working tree.
- **When** `pipeline("k3m9xq", "deliver")` and `pipeline("k3m9xq", "nosuch")`
  run.
- **Then** the first returns the eight stages of `typed-boundary` in order and
  the second returns `None`.

#### A Work whose contract overrides an action

- **Given** a Work `m5n6p7` whose `[actions]` sets
  `deliver = ["implementation", "implementation-review"]`.
- **When** `pipeline("m5n6p7", "deliver")` runs.
- **Then** it returns `implementation` and `implementation-review`.

### **AC-3** A Work is found in the working tree, the index or `HEAD`

#### A Work that only `HEAD` has

- **Given** a Work `d4e5f6` that is in `HEAD` and in neither the working tree
  nor the index, with the item `AC-1`.
- **When** `items("d4e5f6")` runs on the working-tree adapter and on the index
  adapter.
- **Then** each returns `AC-1`.

#### A Work that differs between the working tree and the index

- **Given** `k3m9xq` with the item `AC-3` in the working tree and without it in
  the index.
- **When** `items("k3m9xq")` runs on each adapter.
- **Then** the working-tree adapter returns `AC-1` and `AC-3` and the index
  adapter returns `AC-1`.

### **AC-4** A Work that is nowhere is absent

#### An unknown id

- **Given** an id `zz9zz9` that is in no place.
- **When** `items("zz9zz9")` and `pipeline("zz9zz9", "deliver")` run.
- **Then** both return `None`.
