<!-- wio
id = "ay92nt"
template = "feature.leaf"
roots = ["wio"]
depends_on = []
-->

# Contract section

## Purpose

A session must read the Work's contract and the sections its ancestors pass on,
and the text must be the one that `wio contracts show` prints, so that the two
commands cannot show different contracts.

## Goals

- The bundle shows the Work's resolved contract as `wio contracts show` prints
  it.
- A Work whose contract holds nothing after its metadata block gives an empty
  section and does not fail.

## Non-Goals

- Laying out the resolved view, which `wio.contracts` does.
- Judging the contract, which `wio contracts check` does.

## Assumptions

### A-1

The resolved view already starts after the metadata block, so the section needs
no stripping of its own.

## Mechanisms

- **`render_resolved`** — in `wio.contracts`, the one function that writes the
  resolved view, which this section calls and does not copy.
- **The `Contracts` port** — gives the resolved contract of a Work.

## Constraints

### C-1

The section is the text of `render_resolved` for the Work's resolved contract,
byte for byte.

## Acceptance criteria

### **AC-1** The section is what `wio contracts show` prints

The section holds the Work's own contract and, for each ancestor that passes a
section, that ancestor's sections under a `## Inherited from:` heading, with no
metadata block.

#### A child with an inherited section

- **Given** a parent whose template marks `Glossary` as inheritable and a child
  of it.
- **When** the section is built for the child.
- **Then** it equals the text that `wio contracts show` prints for the child
  after its metadata block, and the parent's glossary stands under
  `## Inherited from: <title> (<id>)`.

### **AC-2** A contract with no body gives an empty section

A Work with nothing after its metadata block gives an empty section.

#### An empty contract

- **Given** a Work whose file holds only its metadata block.
- **When** the section is built.
- **Then** it is empty and no error is raised.
