<!-- wio
id = "fy51ae"
template = "feature.leaf"
roots = ["wio"]
depends_on = ["b53rss", "fadef4", "q6mf05"]
-->

# Record a stage entry

## Purpose

The bundle a session received cannot be rebuilt later, so cost and quality
cannot be analyzed unless each run records which Work, action, stage and bundle
it gave and which rules it contained.

## Goals

- Each run that delivers its bundle writes one `context` event with the Work,
  the action, the stage, the bundle id and the size of the body.
- The event holds the hash of the file of each included rule, in the order of
  the bundle.
- The event is written after the bundle has been delivered.

## Non-Goals

- The start commit and the dirty flag of a gate, which the sibling records.
- Reading the event log, or the identification of the harness session, which
  `wio.log` does.
- A failed delivery of a bundle to standard output, because printing it is the
  delivery and it is not refused.

## Assumptions

### A-1

`ContextEvent`, `EventSink` and the identification of the harness session in
`wio.log` carry everything that a stage entry records, as A-1 of
[wio context](../../README.md) says, and the `size` of `ContextEvent`, which its
docstring calls "the length of the bundle in bytes", is the size of the body, as
A-2 of that Work says, so the docstring is corrected with this Work.

### A-2

The compiler result carries the qualified code and the `rule_hash` of each
included rule in the order of the bundle, as the command Work says, so this Work
reads no rule file.

### A-3

A reader of the log takes the first `context` event of a session, as the
concepts say, so a run that is repeated writes another event without confusing
it.

## Mechanisms

- **`ContextEvent`** — in `wio.models.events`, with `work`, `action`, `stage`,
  `bundle`, `size`, `rules`, `start` and `dirty`; the encoded line omits `start`
  and `dirty` when they are `None`.
- **`EventSink`** — in `wio.ports`, which writes the event and reports a failure
  as a warning.
- **A gate** — a stage with `gate = true` in the config.

## Acceptance criteria

### **AC-1** A run records one event with what it gave

One run writes one event with the Work, the action, the stage, the bundle id of
the metadata, the size of the body and the hash of each rule's file, keyed by
qualified code in the order of the bundle.

#### A stage with two rules

- **Given** a stage whose bundle holds `mp.ARC001` and `mp.ERR002` in that
  order.
- **When** `wio context` runs.
- **Then** the log holds one event whose `bundle` is the id in the metadata,
  whose `size` is the size in the header, and whose `rules` map `mp.ARC001` and
  `mp.ERR002`, in that order, to the `rule_hash` of their files.

### **AC-2** Only the included rules are recorded

An excluded rule is not in `rules`, and a bundle with no included rule has an
empty `rules`.

#### An excluded rule, and none included

- **Given** a stage with one included rule and one excluded rule, and a stage
  with no included rule.
- **When** `wio context` runs for each.
- **Then** the first event's `rules` holds the included rule only, and the
  second event's `rules` is empty.

### **AC-3** A stage that is not a gate records no start and no dirty flag

The event of a stage that is not a gate holds no start commit and no dirty flag.

#### A plain stage

- **Given** a stage without `gate = true`.
- **When** `wio context` runs.
- **Then** the encoded event has no `start` and no `dirty`.

### **AC-4** A failure to write never blocks

When the event cannot be written, the command warns, prints the bundle and exits
0, which verifies C-2 of the top Work.

#### An unwritable log, and a log that cannot be located

- **Given** an event log whose append fails, and a relative `$WIO_HOME`, which
  `wio.log` cannot locate.
- **When** `wio context` runs for each.
- **Then** the first warns that the event log could not be written and names the
  path, the second warns that the log could not be located, and each prints the
  bundle and exits 0.

### **AC-5** A failed delivery records no event

When the bundle cannot be delivered, no event is written, because the session
was not given its bundle.

#### A file that cannot be written, and no temporary directory

- **Given** `--output` with a path that cannot be written, and `--output`
  without a path with `$TMPDIR` unset and a system directory that cannot be
  written.
- **When** `wio context` runs for each.
- **Then** each exits 2, and the log holds no new `context` event.

### **AC-6** Each run that delivers writes its own event

A repeated run writes another event, and a run that was only warned about writes
one.

#### A repeated run, and a warned run

- **Given** a stage run twice in one session, and a stage whose body is over the
  size threshold.
- **When** `wio context` runs for each.
- **Then** the first leaves two events, and the second writes one.

### **AC-7** A switched-off log writes no event

When the log is switched off, no event is written and no warning is given.

#### Logging off

- **Given** the log switched off as `wio.log` allows.
- **When** `wio context` runs.
- **Then** the bundle is printed, no event is written, and no warning about the
  log is reported.
