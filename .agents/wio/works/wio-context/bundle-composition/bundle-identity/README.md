<!-- wio
id = "ghq8mz"
template = "feature.leaf"
roots = ["wio"]
depends_on = ["bgc8q9"]
-->

# Bundle identity

## Purpose

Two sessions can be said to have seen the same context only if one value names
it, and that value must change when the goal, the contract, the rules or the
skill change.

## Goals

- A bundle has an id that is the same for the same body and skill files.
- The id is 12 lower-case hexadecimal digits for every stage.
- The id changes when any part of the body, or any file of the skill, changes.

## Non-Goals

- Printing the id in the header, which the header does.
- Finding the skill and hashing its files, which the lookup does.
- Defining the body, which the assembly does.

## Assumptions

None.

## Mechanisms

The signature and the way the skill's hash joins the input are provisional.

- **`bundle_id(body: str, skill_hash: str | None) -> str`** — the first twelve
  lower-case hexadecimal digits of the SHA-256 of the UTF-8 bytes of `body`,
  followed, for a stage with a skill, by a NUL byte and the ASCII of
  `skill_hash` in the input of the hash and not in the id.

## Acceptance criteria

### **AC-1** The id is short and repeatable

The id is 12 lower-case hexadecimal digits, and the same inputs always give it.

#### Two computations, with and without a skill

- **Given** one body, and one body with a skill hash.
- **When** each id is computed twice.
- **Then** each pair is equal, and each id is 12 lower-case hexadecimal digits.

### **AC-2** Any change to the body or the skill changes the id

A change to the body, a different skill hash, and a skill hash against none,
each give a different id.

#### Three changes

- **Given** a body and a skill hash and their id.
- **When** one character of the body changes, then the skill hash changes, and
  then the skill hash is `None`.
- **Then** each gives an id that differs from the first.
