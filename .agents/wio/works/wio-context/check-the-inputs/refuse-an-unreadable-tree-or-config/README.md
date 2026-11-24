<!-- wio
id = "k8z4gf"
template = "feature.leaf"
roots = ["wio"]
depends_on = ["b53rss"]
-->

# Refuse an unreadable config, tree, Work or rules

## Purpose

A session needs its guidance even while the tree has faults of its own, but a
config with an error, a tree that may not hold every Work, a Work that
does not exist and a rule that a fault leaves out must not produce a bundle that
looks complete.

## Goals

- A config with an error is refused, as every command refuses it.
- A Work tree that may not hold every Work is refused.
- An unknown Work is refused, and a shared id refuses only the lookup of that
  id.
- A fault in a rule file or a ruleset is refused, as `wio rules list` refuses
  it.
- A fault that leaves the tree complete, in the metadata, the graph or the
  template, does not stop the command.

## Non-Goals

- Refusing an unknown action, stage or root, which the sibling does.
- Reporting the faults of the tree or of the rules, which `wio contracts check`
  and `wio rules check` do.
- The order in which the refusals are judged, which the parent states.

## Assumptions

### A-1

The Work is named by its id and never by a path, so an argument that looks like
a path is an id that no Work has, because `wio contracts show` is where a path
is accepted.

### A-2

The judgement that `wio contracts show` makes of the tree, which refuses an
incomplete tree and a shared id and goes on past other faults, can be reached
through the `Contracts` port, whose provider raises `ContractsError`; the
`KeyError` that the stub of the port documents is provisional.

### A-3

The rule selection refuses with the diagnostics when a rule file or a manifest
has a fault, as `wio rules list` does, and `wio context` lets that refusal stand
as exit 2; the stub of the port documents only `KeyError`, which is provisional
on this point.

## Mechanisms

The ports below are provisional.

- **The `Contracts` port** — in `src/wio/context/ports.pyi`, whose `resolved`
  raises for a Work that cannot be found; its refusals follow `refusal.py` of
  `wio.contracts`.
- **The `RuleSelection` port** — in `src/wio/context/ports.pyi`, satisfied by
  `wio.rules`, whose `DiagnosticsError` for a fault in the rules this Work lets
  stand.
- **The loader of the config** — `Settings.load` of the shared `Settings` port,
  which refuses a config with an error for every command, as this command does.

## Acceptance criteria

### **AC-1** A config with an error is refused

A config with an error makes `wio context` exit 2 with the diagnostics that
every command prints for it.

#### A mistyped key

- **Given** a config with a key that the schema does not know.
- **When** `wio context` runs.
- **Then** it exits 2, prints the diagnostic of that key on standard error and
  nothing on standard output.

### **AC-2** A tree that may not hold every Work is refused

A tree that may not hold every Work exits 2 and names the files that cause it.

#### Two marked files in one directory

- **Given** under `nesting` a directory that holds two marked files.
- **When** `wio context` runs for a Work of the tree.
- **Then** it exits 2 and names both files.

#### A Work with no id

- **Given** a marked file whose metadata block has no `id`.
- **When** `wio context` runs for a Work of the tree.
- **Then** it exits 2 and names the file.

### **AC-3** An unknown Work is refused

An id that no Work has exits 2 and says that no Work has it, also when it looks
like a path.

#### An id and a path

- **Given** a complete tree and an id `nope11` that no Work has.
- **When** `wio context` runs for `nope11`, and for `works/a/README.md`.
- **Then** each exits 2 and says that no Work has that id.

### **AC-4** A shared id refuses only its own lookup

Two Works that share an id refuse a run for that id and no other.

#### One shared id

- **Given** two Works with the id `s1s1s1` and a third Work with its own id.
- **When** `wio context` runs for `s1s1s1` and then for the third.
- **Then** the first exits 2 and names both paths, and the second prints its
  bundle and exits 0.

### **AC-5** A fault that leaves the tree complete does not stop a run

A metadata, graph or template fault of another Work, or of the Work itself, that
leaves every Work in the tree does not stop the bundle, though other warnings
may appear.

#### Faults that `check` reports

- **Given** a Work with a `depends_on` id that no Work has, a key that wio does
  not know, and a `template` that names no template, and another Work with a
  repeated heading.
- **When** `wio context` runs for the first Work.
- **Then** the bundle is printed and the exit code is 0.

### **AC-6** A fault in the rules is refused

A rule file or a manifest with a fault exits 2 with the diagnostics of
`wio rules`, and no bundle.

#### A rule with an undeclared family

- **Given** a rule whose family its ruleset's manifest does not declare.
- **When** `wio context` runs for a Work and a stage.
- **Then** it exits 2, names the rule's file, and standard output is empty.
