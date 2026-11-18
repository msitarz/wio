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
  the same event and the same envelope, with its time to the millisecond.
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

### A-2

A time kept to the millisecond is enough to order the events of one person, so
the line does not carry more digits.

### A-3

The keys of a line are the names of the fields, a bundle id and a rule hash are
opaque strings, and a time is finite and not negative.

## Mechanisms

- **`ContextEvent`** — in `wio.models.events`, frozen: `work: str`,
  `action: str`, `stage: str`, `bundle: str` (the bundle id), `size: int`,
  `rules: Mapping[str, str]` (each qualified rule code with the hash of its
  file, in the order of the bundle), `start: str | None` and
  `dirty: bool | None`, which only a gate has, so they are `None` for any other
  stage, while `ReviewEvent` keeps the fields it has.
- **`Envelope`** — in `wio.models.events`, frozen: `time: float` (seconds since
  the epoch, in UTC), `directory: str`, `harness: str | None`,
  `session: str | None`, `parent: str | None`, `matches: tuple[str, ...]` (the
  names of the harnesses that matched, in config order) and
  `ids: Mapping[str, str]` (the mapped variables that were set, with their
  values).
- **`encode_line(envelope: Envelope, event: Event) -> str`** — in `wio.formats`,
  one JSON object and a newline, built with the shared JSON encoding of
  `wio.formats`: `"v": 1`, `"type"` (`context` or `review`), `"time"` as an RFC
  3339 string in UTC truncated to the millisecond after the time is rounded to
  the microsecond, `"directory"` and the fields
  of the event.
- **The optional fields** — `harness`, `session`, `parent`, `start` and `dirty`
  are left out when they are `None`, `matches` and `ids` when they are empty,
  and a line without them decodes to `None` or to an empty value, while every
  other field is written, an empty `rules`, `cited` or `hashes` as `{}` and an
  empty string as it is.
- **`decode_lines(text: str) -> Decoding`** — in `wio.formats`;
  `Decoding(entries: tuple[Entry, ...], skipped: int)` and `Entry(envelope:
  Envelope, event: Event)`, with the entries in line order.
- **A line that is skipped** — and counted, when it is not a JSON object, has a
  version other than 1, has an unknown type, lacks a field that is not optional,
  has a `time` that is not an RFC 3339 string in UTC, or has a field of the
  wrong type, where a `size` that is a boolean is of the wrong type and the
  value of a mapping must be a string.
- **A line that is not skipped** — a field that version 1 does not name is
  ignored, and a blank line is neither an entry nor skipped.

## Constraints

### C-1

A field that version 1 adds later is optional and ignored by a reader that does
not know it, and a change that removes or reinterprets a field raises the
version. AC-4 checks that a reader ignores a field it does not know, and a
reviewer checks the raising of the version in the next change to the format.

## Acceptance criteria

### **AC-1** A `review` event leaves the log and comes back the same

A `review` event with its envelope is written as a line and read back with
every field equal, so a reader sees what the writer recorded.

#### Every field

- **Given** a `ReviewEvent` of the Work `k3m9xq`, the action `deliver`, the
  stage `implementation-review`, a commit, the judge `agent`, the result
  `fail`, the cited `{"ARC001": "fail", "AC-2": "pass"}` and the hashes
  `{"ARC001": "h1"}`, and an envelope with every field set and the time
  `1795000000.123`.
- **When** it is encoded and the line is decoded.
- **Then** the decoding has one entry equal to the event and the envelope, with
  the time equal after rounding to three decimals and the cited items in the
  order given, and no line was skipped.

### **AC-2** A `context` event leaves the log and comes back the same

A `context` event with every field filled in is written and read back with
every field equal, so `wio context` only has to build it.

#### A gate and a stage that is not a gate

- **Given** a `ContextEvent` with every field set, including `start` and
  `dirty`, and one for a stage that is not a gate, with both `None`.
- **When** each is encoded and decoded.
- **Then** each decodes to an event equal to the one given, and the second keeps
  its `None` fields.

#### The order of the rules

- **Given** a `ContextEvent` whose `rules` are, in this order,
  `{"contracts.CON002": "h2", "contracts.ACC001": "h1"}`.
- **When** it is encoded and decoded.
- **Then** the keys of the decoded `rules` are `contracts.CON002` and then
  `contracts.ACC001`.

### **AC-3** An event is one line, and what is empty is left out

Each event takes one line whatever its values hold, so a reader can find an
event by its line, and a field with nothing to say takes no room.

#### A value that holds a newline

- **Given** an envelope whose directory is `/w/a\nb/日本`.
- **When** it is encoded.
- **Then** the text ends in one newline and holds no other, and decoding it
  gives the same directory.

#### Empty mappings and an empty string

- **Given** a `ReviewEvent` with empty `cited` and `hashes`, and an envelope
  whose harness is the empty string.
- **When** it is encoded and the line is decoded.
- **Then** the line holds `"cited": {}` and `"hashes": {}`, and the decoding
  gives empty mappings and the harness `""`.

#### The optional fields

- **Given** an envelope with no harness, session or parent, no matches and no
  ids, and a `context` event of a stage that is not a gate.
- **When** it is encoded and the line is decoded.
- **Then** the line holds none of `harness`, `session`, `parent`, `matches`,
  `ids`, `start` and `dirty`, the decoding gives `None`, `None`, `None`, an
  empty tuple, an empty mapping, `None` and `None`, and no line was skipped.

### **AC-4** A line that cannot be understood is skipped and counted

A reader goes on past a line it cannot understand and says how many it
skipped, so one bad line never hides the events around it.

#### A damaged log

- **Given** a text of lines: a complete `review` event, `{"v": 1, "type": "re`,
  a line with `"v": 2`, a line with `"type": "other"`, a `review` line without
  its `result`, a `review` line whose `cited` is a list, a `review` line whose
  `time` is `"yesterday"`, a `review` line whose `time` is
  `"2026-11-18T13:06:40.123+02:00"`, a `review` line whose `hashes` holds a
  number, a `context` line whose `size` is `true`, the line `[1]`, a blank line,
  and a complete `context` event.
- **When** `decode_lines` runs on it.
- **Then** it gives two entries, in line order, and the count 10.

#### A field that is not known

- **Given** a `review` line of version 1 with a field `"later": 1`.
- **When** `decode_lines` runs on it.
- **Then** it gives one entry and skips nothing.

### **AC-5** The time is written to the millisecond, truncated, in UTC

The time of an event is written as a UTC string that any tool reads, to the
millisecond and never rounded up.

#### A time with more than milliseconds

- **Given** an envelope with the time `1795000000.123956`.
- **When** it is encoded and the line is decoded.
- **Then** the line holds `"time": "2026-11-18T11:06:40.123Z"`, and decoding
  gives a time that rounds to `1795000000.123`.

#### A time that is already in milliseconds

- **Given** an envelope with the time `1795000000.123`.
- **When** it is encoded.
- **Then** the line holds `"time": "2026-11-18T11:06:40.123Z"`.
