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

A missing `roots` key and `roots = []` both give a Work no roots, as the
concepts say.

## Mechanisms

- **The roots port** — the one that the parent names, which gives the expanded
  roots of a Work.
- **The stage's `roots`** — read through the shared `Settings` port.

## Acceptance criteria

### **AC-1** A Work with no roots is warned about at a stage that needs them

A Work with no roots at a stage that selects the Work's roots gives a warning
that names the Work's id and says that it has no roots, and the bundle is still
printed.

#### Three Works with no roots

- **Given** a composition of the bundle that is faked to return a fixed bundle,
  a config that declares the roots `api` and `contract`, a Work whose `roots`
  are empty, a Work with no `roots` key, a Work whose `roots` list
  `@descendants` and that has no children, and a stage with no `roots`.
- **When** `wio context` runs for each.
- **Then** each reports a warning that names the Work's id and says that it has
  no roots, prints its bundle and exits 0.

#### A stage that lists `@work`

- **Given** the same config, a Work with no roots and a stage whose `roots` are
  `["contract", "@work"]`.
- **When** `wio context` runs.
- **Then** a warning is reported and the bundle is printed.

### **AC-2** No warning when the Work's roots play no part

A Work with roots, and a stage that names its roots without `@work` or names
none, give no warning about the roots.

#### Roots, and stages with their own roots

- **Given** the same config, a stage with no `roots`, a stage whose `roots` are
  `["contract"]`, a stage whose `roots` are `[]`, a Work whose `roots` list
  `api` and a Work with no roots.
- **When** `wio context` runs for the Work with roots at the stage with no
  `roots`, and for the Work with no roots at each of the other two stages.
- **Then** no run reports a warning about the roots.
