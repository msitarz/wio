<!-- wio
id = "ztj4hj"
template = "feature.leaf"
roots = ["wio"]
depends_on = ["b53rss"]
-->

# Warn about a Work with no roots

## Purpose

A Work whose roots were never set gets no rule from its roots, and a bundle that
looks complete hides that, so the driver must be told.

## Goals

- A driver is warned when a stage that selects the Work's roots meets a Work
  whose roots are empty.
- A driver is not warned when the Work has roots.
- A driver is not warned when the stage names its roots without `@work`, because
  the Work's roots play no part there.

## Non-Goals

- Refusing the run, because a bundle with the rules of the stage's own roots is
  still useful and the driver decides.
- Selecting the rules, which `wio rules` does and which gives such a Work a
  selection with no included rule.

## Assumptions

### A-1

The roots of a Work, with `@descendants` expanded and each name once, can be had
through a port that `wio.contracts` satisfies, as the `WorkRoots` port of
`wio.rules` does.

### A-2

A stage selects the Work's roots when its `roots` are not set or list `@work`.

## Mechanisms

- **The roots port** — in `src/wio/context/ports.pyi`, provisional, satisfied by
  `wio.contracts`, which gives the expanded roots of a Work.
- **The stage's `roots`** — read through the shared `Settings` port.

## Acceptance criteria

### **AC-1** A Work with no roots is warned about at a stage that needs them

A Work with no roots at a stage that selects the Work's roots gives a warning
that names the Work and says why no rule from its roots applies, and the bundle
is still printed.

#### Three Works with no roots

- **Given** a Work whose `roots` are empty, a Work whose `roots` list
  `@descendants` and that has no children, and a stage with no `roots`.
- **When** `wio context` runs for each.
- **Then** each reports a warning that names the Work, prints its bundle and
  exits 0.

#### A stage that lists `@work`

- **Given** a Work with no roots and a stage whose `roots` are
  `["contract", "@work"]`.
- **When** `wio context` runs.
- **Then** a warning is reported and the bundle is printed.

### **AC-2** No warning when the Work's roots play no part

A Work with roots, and a stage that names its roots without `@work`, give no
warning.

#### Roots, and a stage with its own roots

- **Given** a Work whose `roots` list `api`, and a Work with no roots at a stage
  whose `roots` are `["contract"]`.
- **When** `wio context` runs for each at a stage with no `roots` for the first
  and at that stage for the second.
- **Then** neither run reports a warning.
