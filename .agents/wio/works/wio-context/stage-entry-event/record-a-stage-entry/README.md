<!-- wio
id = "fy51ae"
template = "feature.leaf"
roots = ["wio"]
depends_on = ["b53rss", "4h73tb", "ghq8mz", "bg0g78"]
-->

# Record a stage entry

## Purpose

The bundle a session received cannot be rebuilt later, so cost and quality
cannot be analyzed unless each run records which Work, action, stage and bundle
it gave and which rules it contained.

## Goals

- Each run writes one `context` event with the Work, the action, the stage, the
  bundle id and the size of the body.
- The event holds the hash of the file of each rule that the bundle contains.
- A failure to write the event is a warning and never blocks the run.

## Non-Goals

- The start commit and the dirty flag of a gate, which the sibling records.
- Reading the event log, or the identification of the harness session, which
  `wio.log` does.

## Assumptions

### A-1

`ContextEvent`, `EventSink` and the identification of the harness session in
`wio.log` carry everything that a stage entry records, so `wio.log` needs no
change.

### A-2

The `size` of the event is the size of the body, the number that the header
states.

### A-3

The hash of a rule's file is the `rule_hash` of `wio.formats`, the one that
`wio trailers` cites.

## Mechanisms

- **`ContextEvent`** — in `wio.models.events`, with `work`, `action`, `stage`,
  `bundle`, `size`, `rules`, `start` and `dirty`.
- **`EventSink`** — in `wio.ports`, which writes the event and reports a failure
  as a warning.
- **`rule_hash`** — in `wio.formats`, which hashes the bytes of a rule's file.

## Acceptance criteria

### **AC-1** A run records one event with what it gave

One run writes one event with the Work, the action, the stage, the bundle id of
the header, the size of the body and the hash of each rule's file, keyed by
qualified code in the order of the bundle.

#### A stage with two rules

- **Given** a stage whose bundle holds `mp.ARC001` and `mp.ERR002`.
- **When** `wio context` runs.
- **Then** the log holds one event whose `bundle` and `size` are those of the
  header and whose `rules` map `mp.ARC001` and `mp.ERR002`, in that order, to
  the `rule_hash` of their files.

### **AC-2** A stage that is not a gate records no start and no dirty flag

The event of a stage that is not a gate holds no start commit and no dirty flag.

#### A plain stage

- **Given** a stage that is not a gate.
- **When** `wio context` runs.
- **Then** the event's `start` and `dirty` are absent.

### **AC-3** A failure to write never blocks

When the event cannot be written, the command warns, prints the bundle and exits
0.

#### An unwritable log

- **Given** an event log that cannot be written.
- **When** `wio context` runs.
- **Then** a warning names the path, the bundle is printed, and the exit code is
  0.
