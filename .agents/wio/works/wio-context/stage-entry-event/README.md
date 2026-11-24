<!-- wio
id = "18m35a"
template = "feature.parent"
roots = ["@descendants"]
depends_on = []
-->

# Stage-entry event

## Purpose

What a session was given, and where a gate's review started, cannot be rebuilt
later, so cost and quality cannot be analyzed and a later form of
`wio trailers --result` has nothing to compare the reviewed commit with.

## Goals

- Each run that delivers its bundle, with the log on, records that a session
  entered a stage, with what it received.
- A gate's entry also records the commit its review starts from and whether the
  tree had uncommitted changes.

## Non-Goals

- Reading the log back, which `wio log show` does.
- Recording the result of a gate, which `wio trailers --result` does.
- Comparing the recorded start with the reviewed commit and warning about a
  dirty start, which `wio trailers --result` does in a later form.

## Assumptions

### A-1

The comparison and the dirty warning are a later form of
`wio trailers --result`, as `src/wio/trailers/README.md` says, so this group
records what that form will read and states nothing of its behaviour.

## Visuals

Before, `wio context` writes no event, so a gate's review start is unknown.
After, each run that delivers its bundle, with the log on, writes one `context`
event to the event log, and a gate's event also carries the start commit and
whether the tree was dirty, for the later form of `wio trailers --result` to
read.

## Acceptance criteria

### **AC-1** A gate's run writes one event

A gate stage's run writes one `context` event that carries both the fields of a
stage entry and the start commit and the dirty flag, not two events; the fields
are those that AC-7 of [wio context](../README.md) states.

#### A gate

- **Given** a repository with a commit and a stage with `gate = true`.
- **When** `wio context` runs for it.
- **Then** the log holds exactly one new `context` event, and that one event
  holds the stage entry's fields and the start and the dirty flag.
