<!-- wio
id = "ghq8mz"
template = "feature.leaf"
roots = ["wio"]
depends_on = ["bgc8q9", "30gfec", "ay92nt", "4h73tb"]
-->

# Bundle identity

## Purpose

Two sessions can be said to have seen the same context only if one value names
it, and that value must change when the goal, the contract, the rules or the
skill change and must not change with how the command was run.

## Goals

- A bundle has an id that is the same for the same body and skill files.
- The id changes when any part of the body, or any file of the skill, changes.
- The id does not depend on the header, on how wio was invoked or on `--output`.

## Non-Goals

- Printing the id in the header, which the header does.
- Finding the skill and hashing its files, which the lookup does.

## Assumptions

None.

## Mechanisms

The length of the id and the way the skill's hash joins the body are
provisional.

- **The bundle id** — the first twelve lower-case hexadecimal digits of the
  SHA-256 of the bytes of the body, followed, for a stage with a skill, by the
  hash of the skill's files.
- **The body** — the goal or the pointer, the resolved contract, the rules and
  the closing line, as the assembly joins them.

## Acceptance criteria

### **AC-1** The same body gives the same id

The same body and skill files always give the same id.

#### Two computations

- **Given** one body and one skill hash.
- **When** the id is computed twice.
- **Then** both ids are equal.

### **AC-2** Any change to the body or the skill changes the id

A change to the goal, the contract, the rules, or a file of the skill gives a
different id.

#### Four changes

- **Given** a body and a skill hash and their id.
- **When** the goal, the contract text, the rules text and the skill hash are
  changed one at a time.
- **Then** each gives an id that differs from the first.

### **AC-3** The id does not depend on the header or the invocation

The id is the same whatever the header says and however the command was run.

#### A changed header

- **Given** a body and its id.
- **When** the id is computed with another header, and with the command run
  through `--output`.
- **Then** every id is the first.
