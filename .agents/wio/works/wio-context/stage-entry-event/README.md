<!-- wio
id = "18m35a"
template = "feature.parent"
roots = ["@descendants"]
depends_on = []
-->

# Stage-entry event

## Purpose

What a session was given, and where a gate's review started, cannot be rebuilt
later, so cost and quality cannot be analyzed and `wio trailers --result` has
nothing to compare the reviewed commit with.

## Goals

- Each run records that a session entered a stage, with what it received.
- A gate's entry also records the commit its review starts from and whether the
  tree had uncommitted changes.

## Non-Goals

- Reading the log back, which `wio log show` does.
- Recording the result of a gate, which `wio trailers --result` does.

## Assumptions

None.

## Visuals

Before, `wio context` writes no event, so a gate's review start is unknown.
After, each run writes a `context` event to the event log, and a gate's event
carries the start commit that `wio trailers --result` compares with the commit
it reviewed.

## Acceptance criteria

### **AC-1** The recorded start is the one `wio trailers --result` compares

For a gate, the start commit in the `context` event is the one that
`wio trailers --result` compares with the reviewed commit, and a difference is
warned about there.

#### Unchanged and moved

- **Given** a gate whose session entered the stage and a review recorded on the
  same commit, and another review recorded after a new commit.
- **When** `wio trailers --result` runs for each.
- **Then** the first gives no warning about the start, and the second warns that
  the reviewed commit differs from the one the session started from.
