<!-- wio
id = "5pes9b"
template = "feature.leaf"
roots = ["wio"]
depends_on = []
-->

# Encode and decode an event

## Purpose

A log is read long after it is written, by a reader that may be newer or older
than the writer, and the `context` event that `wio context` will write has no
fields yet; the engine needs event types that are final and a line format that
can grow without rewriting an old line.

## Goals

- `ContextEvent` carries every field of the `context` event of concepts.md, so
  `wio context` only builds it.
- An event and its envelope are written as one line of JSON that decodes back to
  the same event and envelope.
- A reader skips a line it cannot understand, counts it, and goes on with the
  rest.
- A later field can be added to a line without breaking a reader of version 1.

## Non-Goals

- Appending a line or reading a file; the sink and `show` do that.
- Computing a bundle id, a rule hash or a commit; `wio context` does that.
- The meaning of the stamps, which `xfy1mq` computes.

## Assumptions

### A-1

The size of a bundle is its length in bytes, because concepts.md gives no unit
and a harness truncates by length.

## Mechanisms

- **`ContextEvent`** — in `wio.models.events`, frozen: `work: str`,
  `action: str`, `stage: str`, `bundle: str` (the bundle id), `size: int`,
  `rules: Mapping[str, str]` (each qualified rule code with the hash of its
  file, in the order of the bundle), `start: str | None` and
  `dirty: bool | None`, which only a gate has, so they are `None` for any other
  stage. `ReviewEvent` keeps the fields it has.
- **`Envelope`** — in `wio.models.events`, frozen: `time: float` (seconds since
  the epoch, in UTC), `directory: str`, `harness: str | None`,
  `session: str | None`, `parent: str | None`, `matches: tuple[str, ...]` (the
  names of the harnesses whose variables were set, in config order) and
  `ids: Mapping[str, str]` (the mapped variables that were set, with their
  values).
- **`encode_line(envelope: Envelope, event: Event) -> str`** — in `wio.formats`,
  one JSON object and a newline, built with the shared JSON encoding of
  `wio.formats`: `"v": 1`, `"type"` (`context` or `review`), `"time"` as an RFC
  3339 string in UTC with millisecond precision, `"directory"`, the session
  fields left out when they are `None` or empty, and the fields of the event.
- **`decode_lines(text: str) -> Decoding`** — in `wio.formats`;
  `Decoding(entries: tuple[Entry, ...], skipped: int)` and `Entry(envelope:
  Envelope, event: Event)`, with the entries in line order. A line is skipped,
  and counted, when it is not a JSON object, has a version other than 1, has an
  unknown type, lacks a field of its version or has a field of the wrong type. A
  field that version 1 does not name is ignored, and a blank line is neither an
  entry nor skipped.

## Constraints

### C-1

A field that version 1 adds later is optional and ignored by a reader that does
not know it, and a change that removes or reinterprets a field raises the
version. A reviewer judges it from the next change to the format.

## Acceptance criteria

### **AC-1** A `review` event round-trips

#### Every field

- **Given** a `ReviewEvent` of the Work `k3m9xq`, the action `deliver`, the
  stage `implementation-review`, a commit, the judge `agent`, the result
  `fail`, the cited `{"ARC001": "fail", "AC-2": "pass"}` and the hashes
  `{"ARC001": "h1"}`, and an envelope with every field set.
- **When** it is encoded and the line is decoded.
- **Then** the decoding has one entry equal to the event and the envelope, with
  the cited items in the order given, and no line was skipped.

### **AC-2** A `context` event round-trips

#### A gate and a stage that is not a gate

- **Given** a `ContextEvent` with every field set, including `start` and
  `dirty`, and one for a stage that is not a gate, with both `None`.
- **When** each is encoded and decoded.
- **Then** each decodes to an event equal to the one given, and the second keeps
  its `None` fields.

### **AC-3** An event is one line

#### A value that holds a newline

- **Given** an envelope whose directory is `/w/a\nb/日本`.
- **When** it is encoded.
- **Then** the text ends in one newline and holds no other, and decoding it
  gives the same directory.

#### The session fields

- **Given** an envelope with no harness, session or parent and no matches.
- **When** it is encoded.
- **Then** the line holds none of `harness`, `session`, `parent` and `matches`,
  and decoding it gives `None`, `None`, `None` and an empty tuple.

### **AC-4** A line that cannot be understood is skipped and counted

#### A damaged log

- **Given** a text of lines: a complete `review` event, `{"v": 1, "type": "re`,
  a line with `"v": 2`, a line with `"type": "other"`, a `review` line without
  its `result`, a `review` line whose `cited` is a list, a blank line, and a
  complete `context` event.
- **When** `decode_lines` runs on it.
- **Then** it gives two entries, in line order, and the count 5.

#### A field that is not known

- **Given** a `review` line of version 1 with a field `"later": 1`.
- **When** `decode_lines` runs on it.
- **Then** it gives one entry and skips nothing.

### **AC-5** The time is exact and in UTC

#### A time with milliseconds

- **Given** an envelope with the time `1795000000.123456`.
- **When** it is encoded.
- **Then** the line holds `"time": "2026-11-18T11:06:40.123Z"`, and decoding
  gives the time `1795000000.123`.
