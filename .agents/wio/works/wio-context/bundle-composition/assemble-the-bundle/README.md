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

- The bundle is its header, the stage's guidance, the contract, the rules and
  the closing line, in that order.
- The closing line is one fixed sentence that tells the session to run the
  header's command again after its context is compacted.
- The header is given the id and the size of the body, which it does not
  contain.
- A part that is empty leaves no label behind.

## Non-Goals

- Building the parts, which their Works do.
- Printing the bundle, which the command and the delivery do.

## Assumptions

None.

## Mechanisms

The labels and the closing sentence are provisional, but the order is required.

- **The part labels** — the lines `--- stage ---`, `--- contract ---` and
  `--- rules ---`, each before its part and each followed by a blank line.
- **The closing line** — `If your context was compacted, run the command in the
  header again.`

## Acceptance criteria

### **AC-1** The parts come in order

A bundle holds the header, the guidance, the contract, the rules and the closing
line, in that order, with the closing line last.

#### All parts present

- **Given** a header, a goal, a contract section, a rules section and an id.
- **When** the bundle is assembled.
- **Then** the text is the header, `--- stage ---` and the goal,
  `--- contract ---` and the contract, `--- rules ---` and the rules, and the
  closing line `If your context was compacted, run the command in the header
  again.`, in that order.

### **AC-2** The header describes the body and not itself

The header is given the id and the size of the body, which is everything after
the header, and the same body gives the same header whatever it holds.

#### Counting the body

- **Given** the parts of a bundle.
- **When** the bundle is assembled.
- **Then** the size in the header is the bytes and lines of the text after the
  header, and the id in it is the id of that text.

### **AC-3** An empty part leaves no label

A contract section or a rules section that is empty is left out with its label.

#### No contract body and no rules

- **Given** a Work whose contract section is empty and a stage with no rule.
- **When** the bundle is assembled.
- **Then** it holds no `--- contract ---` and no `--- rules ---`, and the rest
  is unchanged.
