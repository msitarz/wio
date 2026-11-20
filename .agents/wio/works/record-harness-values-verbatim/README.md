<!-- wio
id = "8dk96v"
template = "feature.leaf"
roots = ["wio"]
depends_on = []
-->

# Record harness values verbatim

## Purpose

Harnesses can supply session identifiers in forms that wio's shape guard
rejects, losing information needed to associate log events with transcripts.
Wio should record what the configured environment provides without deciding
which values are valid identifiers.

## Goals

- Preserve configured environment values in log events exactly as supplied.
- Distinguish a set empty value from an unset variable when identifying a
  harness session.

## Non-Goals

- Introduce configurable validation or filtering of harness values.

## Assumptions

None.

## Acceptance criteria

### **AC-1** Set configured values are recorded verbatim

Given configured session, parent, and extra recorded environment variables,
when an event is recorded, every set variable's value is retained verbatim in
the event's recorded IDs, including an empty string, whitespace, newlines,
and characters or lengths rejected by the former shape guard. An unset
variable is omitted. Wio does not warn that a value is an invalid ID.

### **AC-2** Session identification uses presence rather than value shape

Given a harness with a configured session variable, when that variable is set,
including to an empty string, it matches the harness and is available as its
session ID. An unset variable does not match. Existing configured ordering and
harness preference continue to resolve matches and select session and parent
values, including empty values; a parent equal to the session remains omitted.

### **AC-3** Shared variables retain one value

Given a variable named by more than one harness mapping or extra recorded
variable list, when it is set, its one verbatim value is available to each use
and appears once in the recorded IDs.

## Additional context

Configured variables may contain arbitrary text, including secrets; project
authors choose which environment variables wio records in their local log.
