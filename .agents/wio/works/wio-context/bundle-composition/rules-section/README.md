<!-- wio
id = "4h73tb"
template = "feature.parent"
roots = ["@descendants"]
depends_on = []
-->

# Rules section

## Purpose

The rules that a stage selects reach the session only as a selection, so nothing
yet groups them by where they apply, puts them in a fixed order and prints them
as written.

## Goals

- The rules that apply to a stage are printed grouped by the roots they apply
  to.
- The rules of a group are in an order that depends only on their names.
- Each rule is printed with its qualified name and its body as written.

## Non-Goals

- Selecting the rules, which `wio rules` does.
- Saying why a rule was selected, which `wio rules list --explain` does.
- Labelling the section and joining it to the other parts of the bundle, which
  the assembly does.

## Assumptions

None.

## Mechanisms

The name below is provisional.

- **The rules section builder** — in `wio.context`, which turns a `Selection`
  into the text of the section by the three children below.

## Visuals

Before, a selection is a map of rules to decisions. After, the rules that apply
become one section: the grouping places each rule under the roots that reach it,
the ordering sorts each group, and the rendering prints each rule.

## Acceptance criteria

### **AC-1** A selection becomes one section

The section built from a selection is the groups, the family lines and the
rendered rules that the children specify, in one text, with a rule that two
roots reach printed in one group only.

#### Three rules of different reach

- **Given** a selection that includes `mattpocock.ERR002`, which no root is
  needed for, `mattpocock.ARC001`, which `api` reaches, and `python.API001`,
  which `api` and `web` reach, named `errors-carry-context`, `keep-it-small` and
  `adapters-return-typed-results` with the bodies shown below, with the roots
  `api` at `services/api` and `web`
  at `apps/web`, the topics `Error handling` for `ERR`, `Architecture` for `ARC`
  and `Python API` for `API`, and the default separator.
- **When** the section is built.
- **Then** it equals this text, in the provisional wording of the group lines:

  ```text
  Rules for every root:

  mattpocock: Error handling (ERR)

  mattpocock.ERR002 errors-carry-context
  Add context to every error.

  Rules for root api (services/api):

  mattpocock: Architecture (ARC)

  mattpocock.ARC001 keep-it-small
  Keep each module small.

  Rules for roots api, web (services/api, apps/web):

  python: Python API (API)

  python.API001 adapters-return-typed-results
  Adapters return typed results.
  ```
