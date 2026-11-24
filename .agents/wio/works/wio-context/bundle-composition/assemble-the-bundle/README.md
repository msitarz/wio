<!-- wio
id = "fadef4"
template = "feature.leaf"
roots = ["wio"]
depends_on = ["30gfec", "ay92nt", "4h73tb", "ghq8mz", "bg0g78"]
-->

# Assemble the bundle

## Purpose

The parts of a bundle are built by separate Works, so nothing yet puts them in
order, closes the bundle with the line that tells a session what to do after its
context is compacted, and gives the header the id and the size of what it
introduces.

## Goals

- The bundle is its header, a blank line and the body.
- The body is the stage's part, the contract part and the rules part, each under
  its label, and then the closing line.
- The parts are joined by one blank line, a part's trailing newlines are
  removed, and the bundle ends with exactly one newline.
- The closing line is one fixed sentence that tells the session to run the
  header's command again after its context is compacted.
- The header is given the id and the size of the body, which it does not
  contain.
- A part that is empty leaves no label.

## Non-Goals

- Building the parts, which their Works do.
- Printing the bundle, which the command and the delivery do.
- Joining the items of the rules section, which Rule rendering does with
  `[bundle] separator`.

## Assumptions

None.

## Mechanisms

The labels and the closing sentence are provisional, but the order and the
joining are required.

- **The part labels** — the lines `--- stage ---`, `--- contract ---` and
  `--- rules ---`, each before its part and each followed by a blank line.
- **The closing line** — `If your context was compacted, run the command in the
  header again.`
- **The body** — the text after the first blank line of the bundle, which the
  header does not contain, up to the end; its size is its UTF-8 bytes and the
  number of `"\n"` in it.
- **The order of the build** — the body first, then its id and its size, then
  the header, so that the header describes the body and is not part of it.

## Acceptance criteria

### **AC-1** The parts come in order and are joined as written

The bundle is the header, a blank line, and the labelled parts and the closing
line, each separated from the next by one blank line, in this order.

#### All parts present

- **Given** a header of two lines, a goal `GOAL`, a contract section `CONTRACT`
  and a rules section `RULES`.
- **When** the bundle is assembled.
- **Then** the text is the following, in the provisional wording of the labels
  and the closing line:

  ```text
  <header line 1>
  <header line 2>

  --- stage ---

  GOAL

  --- contract ---

  CONTRACT

  --- rules ---

  RULES

  If your context was compacted, run the command in the header again.
  ```

### **AC-2** The header describes the body and not itself

The header is given the id and the size of the body, which is the text after the
first blank line, and the header holds no blank line.

#### Counting the body

- **Given** the parts of a bundle.
- **When** the bundle is assembled.
- **Then** the size in the header is the UTF-8 bytes of the text after the first
  blank line and the number of `"\n"` in it, and the id in the header is the id
  of that text.

### **AC-3** Newlines are removed and the bundle ends once

A part's trailing newlines are removed before it is joined, and the bundle ends
with exactly one newline.

#### A part that ends in a newline and one that does not

- **Given** a contract section `CONTRACT` followed by a newline and a rules
  section `RULES` with none.
- **When** the bundle is assembled.
- **Then** one blank line separates each pair of parts, and the bundle ends with
  the closing line and exactly one newline.

### **AC-4** An empty part leaves no label

A contract section or a rules section that is empty is left out with its label.

#### No contract body and no rules

- **Given** a Work whose contract section is empty and a stage with no rule.
- **When** the bundle is assembled.
- **Then** it holds no `--- contract ---` and no `--- rules ---`, and it equals
  the bundle of AC-1 with those two parts and their labels removed.
