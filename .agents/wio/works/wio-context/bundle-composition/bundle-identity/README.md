<!-- wio
id = "ghq8mz"
template = "feature.leaf"
roots = ["wio"]
depends_on = []
-->

# Bundle identity

## Purpose

Two sessions can be said to have seen the same context only if one value names
it, and that value must change when the request, the goal, the contract, the
rules or the skill change.

## Goals

- A bundle has an id that is the same for the same text.
- The id is 12 lower-case hexadecimal digits for every stage.
- The id changes when any part of the text changes, a skill's files included,
  which count through the files hash in the header's skill line.

## Non-Goals

- Printing the id in the metadata, which the assembly does.
- Finding the skill and hashing its files, which the lookup does.
- Defining the text that is hashed, which the assembly does.

## Assumptions

### A-1

The 12 digits and the hashing of the header and the whole body, labels and
closing line included, are the departures from the concepts that A-3 and A-4 of
[Bundle composition](../README.md) declare.

## Mechanisms

The signature is provisional. The hash and its input are required.

- **`bundle_id(text: str) -> str`** — the first twelve lower-case hexadecimal
  digits of the SHA-256 of the UTF-8 bytes of `text`.

## Acceptance criteria

### **AC-1** The id is the one that the algorithm gives

The id is 12 lower-case hexadecimal digits, the same for the same text, and the
vector below holds.

#### One vector

- **Given** the text `a` and a newline.
- **When** the id is computed, twice.
- **Then** it is `87428fc52280` both times.

### **AC-2** Any change to the text changes the id

A change to the text gives a different id, whatever part of the text changes.

#### One character

- **Given** a text and its id.
- **When** one character of the text changes.
- **Then** the id differs from the first.
