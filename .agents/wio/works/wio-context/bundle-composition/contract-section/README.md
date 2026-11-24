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

- The bundle shows the Work's resolved contract as the view that
  `wio contracts show` prints.
- A Work with no parent that passes a section, whose contract holds nothing
  after its metadata block, gives an empty section and does not fail.

## Non-Goals

- Laying out the resolved view, which `wio.contracts` does.
- Judging the contract, which `wio contracts check` does.

## Assumptions

### A-1

The resolved view that `render_resolved` writes already starts after the
metadata block and has the readable directive lists taken off, so the section
needs no stripping of its own.

## Mechanisms

- **`render_resolved`** — in `wio.contracts`, the one function that writes the
  resolved view, which this section calls and does not copy.
- **The `Contracts` port** — gives the resolved contract of a Work.

## Acceptance criteria

### **AC-1** The section is the view that `wio contracts show` prints

The section equals the resolved view that `wio contracts show` prints for the
Work after the blank line that follows its `----` line, with no metadata block.

#### A child with an inherited section

- **Given** a parent whose template marks `Glossary` as inheritable and a child
  of it.
- **When** the section is built for the child.
- **Then** it equals the view that `wio contracts show` prints for the child
  after the blank line that follows its `----` line.

### **AC-2** A contract with no body gives an empty section

A Work that has no parent passing a section, and nothing after its metadata
block, gives an empty section.

#### An empty contract

- **Given** a Work with no parent whose file holds only its metadata block.
- **When** the section is built.
- **Then** it is empty and no error is raised.
