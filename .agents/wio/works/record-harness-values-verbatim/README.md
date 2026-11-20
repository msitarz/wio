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
  including the preference override when configured.
- Distinguish a set empty value from an unset variable when identifying a
  harness session.
- Present session values safely and readably in the text log report.

## Non-Goals

- Introduce configurable validation or filtering of harness values.

## Assumptions

- **A-1** Project authors accept that configured variables may contain secrets,
  because they choose which environment variables wio records in their local
  log.
- **A-2** A recorded line of any length is appended as the existing append port
  appends it, and wio adds no size limit or atomicity guarantee for long lines.
- **A-3** The environment port returns undecodable bytes as surrogate-escaped
  strings, and the log line encoding escapes every non-ASCII character, so such
  values survive recording.

## Mechanisms

- `wio.log.identify.identify` returns a `SessionIdentity` whose `ids` hold every
  set variable's value, empty ones included, and which matches and selects by
  presence.
- `wio.log.render` formats the session and parent of a context event for
  `wio log show`, with `wio.formats.encode_json` supplying the escaping.

## Acceptance criteria

### **AC-1** Set configured values are recorded verbatim

Set configured ID values are recorded exactly as supplied.

Given configured session, parent, and extra recorded environment variables, when
an event is recorded, every set variable is retained verbatim in the event's
recorded IDs, including an empty string, whitespace, newlines, characters
outside `A-Za-z0-9._:-`, lone surrogates from undecodable bytes, and values
longer than 128 characters. An unset variable is omitted. Wio does not warn that
a value is an invalid ID. Reading the event back returns the same recorded IDs,
session and parent.

### **AC-2** Session identification uses presence rather than value shape

Session identification distinguishes set values from unset variables.

A set session variable, including an empty one, matches its harness; an unset
variable does not. When several harnesses match, the first matching harness in
the existing preference order is selected, and a single matching harness is
selected whatever the preference. When no matching harness is preferred, the
matches remain unresolved and no session is selected.

### **AC-3** Selected fields use the first set values

The selected harness uses its configured variables in order.

When a harness is selected, its first set session variable supplies the session
ID and its first set parent variable supplies the parent ID, including empty
values. A parent equal to the session remains omitted, including when both are
empty.

### **AC-4** Shared variables retain one value

A shared variable has one recorded value that supplies every use of it.

Given a variable named by more than one harness mapping or extra recorded
variable list, when it is set, its one verbatim value supplies each use
and appears once in the recorded IDs.

### **AC-5** The preference override can also supply IDs

The preference override retains its control role and can also be recorded.

Given `WIO_PREFER_HARNESS` is listed in a harness mapping or in
`record_env_vars`, when it is set, its verbatim value appears in the recorded
IDs, including when empty. It participates in harness matching and field
selection like any other configured variable, while continuing to control
harness preference. An empty value matches like any other set variable and
leaves the configured preference in force. Its warning about unknown harness
names is unchanged and is not a warning about an invalid ID.

### **AC-6** Text reports safely present session values

Text reports make session and parent values readable without interpreting
their contents as terminal controls or report structure.

Given a recorded session or parent, `wio log show` text output shows each
present value as a JSON string literal with every UTF-16 code unit outside
printable ASCII, DEL included, escaped as lowercase `\uXXXX` or JSON's short
escape, so `abc` appears as `"abc"`, an empty value as `""`, a value of `a`, a
newline, an escape character and `b` as `"a\n\u001bb"`, a quote as `\"`, a
backslash as `\\` and DEL as `\u007f`. An absent value keeps its existing label,
so a log recorded by an earlier version, whose selected harness has no session,
still shows `claude-code:unknown`. A present session appears as
`claude-code:"abc"`, and a parent as `(parent "def")`. A value with control
characters adds no report lines. JSON output preserves the original values.
