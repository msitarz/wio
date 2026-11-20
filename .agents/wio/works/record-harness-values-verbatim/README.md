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

Set configured ID values are recorded exactly as supplied.

Given configured session, parent, and extra recorded environment variables,
when an event is recorded, every set ID variable's value is retained verbatim in
the event's recorded IDs, including an empty string, whitespace, newlines,
and characters or lengths rejected by the former shape guard. An unset
variable is omitted. Wio does not warn that a value is an invalid ID.

### **AC-2** Session identification uses presence rather than value shape

Session identification distinguishes set values from unset variables.

A set session variable other than the reserved preference override, including an
empty one, matches its harness; an unset variable does not. Existing harness
preference resolves multiple matches, and when a harness is selected its first
set session variable supplies the session ID and its first set parent variable
supplies the parent ID, including empty values. Unresolved matches have no
selected session. A parent equal to the session remains omitted.

### **AC-3** Shared variables retain one value

A shared variable has one recorded value available to each of its ID uses.

Given a variable other than the reserved preference override named by more than
one harness mapping or extra recorded variable list, when it is set, its one
verbatim value is available to each use
and appears once in the recorded IDs.

### **AC-4** The preference override can be recorded explicitly

The preference override retains its control role and can also be recorded.

Given `WIO_PREFER_HARNESS` is listed in `record_env_vars`, when it is set, its
verbatim value appears in the recorded IDs, including when empty. It continues
to control harness preference and neither matches a harness nor supplies a
session or parent ID when named in a harness mapping. It is recorded only when
explicitly listed in `record_env_vars`.

## Additional context

Configured variables may contain arbitrary text, including secrets; project
authors choose which environment variables wio records in their local log.
