<!-- wio
id = "fadef4"
template = "feature.leaf"
roots = ["wio"]
depends_on = ["ghq8mz"]
-->

# Assemble the bundle

## Purpose

The parts of a bundle are built by separate Works, so nothing yet puts them in
order, closes the bundle with the line that tells a session what to do after its
context is compacted, and gives the metadata the id of what follows it.

## Goals

- The bundle is its metadata, a blank line, its header, a blank line and the
  body.
- The body is the stage's part, the contract part and the rules part, each under
  its label, and then the closing line.
- The parts are joined by one blank line, a part's trailing newlines are
  removed, and the bundle ends with exactly one newline.
- The closing line is one fixed sentence that tells the session to run the
  header's command again after its context is compacted.
- The header is built from the size of the body, and the metadata from the text
  after it, so that neither describes itself.
- A part that is empty, the stage's included, leaves no label.

## Non-Goals

- Building the parts and the header, which their Works do.
- Printing the bundle, which the command and the delivery do.
- Joining the items of the rules section, which Rule rendering does with
  `[bundle] separator`.

## Assumptions

### A-1

The labels, the closing sentence, the fixed blank line and the metadata first
are the ones that A-2 to A-4 of [Bundle composition](../README.md) declare as
departures.

## Mechanisms

The labels, the closing sentence and the signature are provisional, but the
order, the joining and the three sections are required.

- **The metadata** — the first line, `bundle: <id>`, in the provisional wording
  of the label, which holds the id of the text after it.
- **The part labels** — the lines `--- stage ---`, `--- contract ---` and
  `--- rules ---`, each before its part and each followed by a blank line.
- **The closing line** — `If your context was compacted, run the command in the
  header again.`
- **The interface** — `assemble(stage: str, contract: str, rules: str,
  header_for: Callable[[int, int], str]) -> str`, which
  builds the body, asks `header_for` for the header with the body's UTF-8 bytes
  and its number of `"\n"`, computes the id with `bundle_id` from the header, a
  blank line and the body, and returns the metadata, a blank line, the header, a
  blank line and the body.
- **The body** — the text after the second blank line of the bundle, as the
  Glossary of [wio context](../../README.md) defines it; its size is its UTF-8
  bytes and the number of `"\n"` in it.
- **The text of the id** — the text after the first blank line, that is the
  header, a blank line and the body.
- **An empty part** — one that is empty after its trailing newlines are removed;
  leading newlines and whitespace are kept as written.

## Acceptance criteria

The criteria use a `header_for` that returns the two lines `HEADER 1` and
`HEADER 2` whatever it is given, unless they say otherwise.

### **AC-1** The sections and the parts come in order and are joined as written

The bundle is the metadata, a blank line, the header, a blank line, and the
labelled parts and the closing line, each separated from the next by one blank
line, in this order.

#### All parts present

- **Given** a stage part `GOAL`, a contract part `CONTRACT` and a rules part
  `RULES`.
- **When** the bundle is assembled.
- **Then** the text is the following, in the provisional wording of the labels
  and the closing line, which is regenerated when that wording changes:

  ```text
  bundle: 7a2383bc4098

  HEADER 1
  HEADER 2

  --- stage ---

  GOAL

  --- contract ---

  CONTRACT

  --- rules ---

  RULES

  If your context was compacted, run the command in the header again.
  ```

### **AC-2** The header and the metadata are built from what they describe

`header_for` is given the size of the body, which is the text after the second
blank line, and the id in the metadata is the id of the text after the first
blank line, so neither is part of what it describes.

#### A spy

- **Given** a `header_for` that records its arguments and returns a header, and
  the parts of AC-1.
- **When** the bundle is assembled with headers of one line and of three lines.
- **Then** the arguments are the same for both headers, 139 bytes and 13 `"\n"`
  for the body of AC-1, and the id in each metadata is the id that `bundle_id`
  gives for the text after the first blank line.

### **AC-3** Newlines are removed and the bundle ends once

A part's trailing newlines are removed before it is joined, and the bundle ends
with exactly one newline.

#### A part that ends in a newline and one that does not

- **Given** a stage part `GOAL`, a contract part `CONTRACT` followed by two
  newlines and a rules part `RULES` with none.
- **When** the bundle is assembled.
- **Then** one blank line separates each pair of parts, and the bundle ends with
  the closing line and exactly one newline.

### **AC-4** An empty part leaves no label

A stage part, a contract part or a rules part that is empty is left out with its
label.

#### Empty parts

- **Given** the parts of AC-1 with the contract part and the rules part empty,
  and then with the stage part empty.
- **When** each bundle is assembled.
- **Then** the first holds no `--- contract ---` and no `--- rules ---`, the
  second holds no `--- stage ---`, and each is what AC-1 gives for the parts
  that remain, with the id of its own text.

#### Every part empty

- **Given** the parts of AC-1 with all three empty.
- **When** the bundle is assembled.
- **Then** the body is the closing line and a newline alone, and the bundle is
  the metadata, the header and that body, each after a blank line.
