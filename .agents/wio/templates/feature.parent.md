<!-- wio
name = "feature.parent"
type = "feature"
shape = "parent"
description = "A capability delivered by child Works, with constraints they share."

[actions]
define = "define-feature"
deliver = "integrate"
amend = "amend-contract"
ratify = ["ratify"]

[contract]
depends_on = []
-->

# <Work name>

<!--
Write each section for the rules this stage's bundle lists.
Delete a section or a heading that has nothing under it, unless it is
required.
-->

## Purpose <!-- wio: required -->

<!-- Why this change is needed. -->

## Goals <!-- wio: required, items>=1 -->

<!-- The capabilities this Work makes possible. -->

## Glossary <!-- wio: inherit -->

<!-- Terms whose meaning in this Work could be read more than one way. -->

## Non-Goals

<!-- What this Work deliberately does not do. -->

## Assumptions <!-- wio: required -->

<!-- What this Work takes as true without having confirmed it, with ids
     (A-1, A-2, ...), or "None." -->

## Mechanisms

<!-- The tools, packages, modules or data structures central to the
     solution, and their roles. -->

## Constraints <!-- wio: inherit -->

<!-- The constraints this Work adds and its children inherit. -->

## Visuals <!-- wio: required -->

<!-- Before and after diagrams of what the Work changes. -->

## Acceptance criteria <!-- wio: required, items>=1, pattern=AC-\d+ -->

<!-- The system-level guarantees that the integrated result establishes. -->

<!-- Example:

### **AC-1** Executed purchases update cash and positions correctly

Applying a valid purchase fill produces a successor portfolio reflecting the
purchased quantity, execution price, and fees.

#### Purchase with fees

- **Given** a portfolio with USD 1,000 cash and no positions.
- **When** a fill purchases two shares of XYZ at USD 100 each, with a total fee
  of USD 5.
- **Then** the successor portfolio contains USD 795 cash and two shares of XYZ.
-->

## Additional context

<!-- Context, risks and links the Work needs that fit nowhere above. -->
