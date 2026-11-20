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

- Preserve configured environment values in log events exactly as supplied,
  including the preference override when explicitly requested.
- Distinguish a set empty value from an unset variable when identifying a
  harness session.
- Present session values safely and readably in the text log report.

## Non-Goals

- Introduce configurable validation or filtering of harness values.

## Assumptions

None.

## Mechanisms

- `wio.log.identify.identify` returns a `SessionIdentity` whose ID values
  represent set variables, and uses `stdio` for preference diagnostics.

## Acceptance criteria

### **AC-1** Set configured values are recorded verbatim

Set configured ID values are recorded exactly as supplied.

Given configured session, parent, and extra recorded environment variables,
when an event is recorded, every set variable other than the preference
override is retained verbatim in the event's recorded IDs, including an empty
string, whitespace, newlines, characters outside `A-Za-z0-9._:-`, and values
longer than 128 characters. An unset variable is omitted. Wio does not warn
that a value is an invalid ID. AC-4 governs the preference override.

### **AC-2** Session identification uses presence rather than value shape

Session identification distinguishes set values from unset variables.

A set session variable other than the reserved preference override, including an
empty one, matches its harness; an unset variable does not. Preference order
picks among multiple matches as before; without a usable preference, they
remain unresolved and have no selected session.

### **AC-5** Selected fields use the first set values

The selected harness uses its configured variables in order.

When a harness is selected, its first set session variable other than
`WIO_PREFER_HARNESS` supplies the session ID and its first set parent variable
other than that override supplies the parent ID, including empty values. A
parent equal to the session remains omitted.

### **AC-3** Shared variables retain one value

A shared variable has one recorded value available to each of its ID uses.

Given a variable other than the reserved preference override named by more than
one harness mapping or extra recorded variable list, when it is set, its one
verbatim value is available to each use and appears once in the recorded IDs.

### **AC-4** The preference override can be recorded explicitly

The preference override retains its control role and can also be recorded.

Given `WIO_PREFER_HARNESS` is listed in `record_env_vars`, when it is set, its
verbatim value appears in the recorded IDs, including when empty. It continues
to control harness preference and neither matches a harness nor supplies a
session or parent ID when named in a harness mapping. It is recorded only when
explicitly listed in `record_env_vars`.

### **AC-6** Text reports safely present session values

Text reports make session and parent values readable without interpreting
their contents as terminal controls or report structure.

Given a recorded session or parent containing a newline, escape character, or
other control character, `wio log show` text output represents the value
without emitting those characters as controls or adding report lines. An empty
value is distinguishable from an absent value, and the displayed representation
allows a reader to recover the original value. JSON output preserves the
original values.

## Additional context

Configured variables may contain arbitrary text, including secrets; project
authors choose which environment variables wio records in their local log.
