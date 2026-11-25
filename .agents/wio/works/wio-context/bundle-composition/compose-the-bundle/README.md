<!-- wio
id = "m4c8wp"
template = "feature.leaf"
roots = ["wio"]
depends_on = ["b53rss", "bgc8q9", "30gfec", "ay92nt", "bg0g78", "ghq8mz", "fadef4", "4h73tb"]
-->

# Compose the bundle

## Purpose

The parts of a bundle are built by separate Works, so nothing yet calls them in
order, gives the header the facts it states, asks for the rule selection once,
and returns the finished bundle with the id, the size of the body and the hash
of each rule's file that the delivery and the event read.

## Goals

- One call with the Work's id, the action and the stage's name returns the text
  of the bundle, its id, the size of its body in UTF-8 bytes, and the qualified
  code and `rule_hash` of each rule it prints, in the order it prints them.
- The rule selection is asked once, and the same `Selection` gives the rules
  section and the hashes.
- The header states the number of rules that the bundle prints and the settings
  of the stage.
- A fault in the rules, or a rule file that cannot be read, raises and returns
  no bundle.

## Non-Goals

- Building a part, the header, the id or the assembly, which their Works do.
- Checking the inputs and warning about them, which Check the inputs does before
  this call.
- Delivering the bundle and recording the entry, which the command and their
  Works do.

## Assumptions

### A-1

The title and id of the Work are those of `ResolvedContract.work`, which the
`Contracts` port gives, and the settings of the stage are read through the
shared `Settings` port, as the header Work needs them.

### A-2

The hash of a printed rule is `rule_hash` of the bytes of the file at
`Rule.path`, read through `FileSystem` under the root that `Repository` gives,
which are the bytes that `selected` of `RuleSelector` hashes; the file is read
again for the hash after the discovery read it for the rule, and a change
between the two reads is accepted, as it is for `selected`.

### A-3

The id is that of the text after the metadata, which `assemble` of the assembly
Work wrote, so it is computed again with `bundle_id` from that text, and the
size is the number of bytes that the assembly gives `header_for`, which this
Work's closure keeps.

## Mechanisms

The names below are provisional, except what the Goals require.

- **The composition** — in `wio.context`, which takes its ports as arguments so
  that a test and `wio.cli` build it the same way: it asks `Contracts` for the
  resolved contract and then for the text of the view of that contract,
  `RuleSelection` once for the selection, the skill lookup once for the stage's
  skill, which it gives to both the stage's guidance and the header, builds each
  part with the Work that owns
  it, and gives `assemble` a `header_for` closure that builds the header with
  the Work's title, the stage's settings, the number of printed rules, the sizes
  and the skill.
- **`CompiledBundle`** — the value that
  [The wio context command](../../the-wio-context-command/README.md) declares
  and this composition builds.
- **The composition port** — the one that
  [The wio context command](../../the-wio-context-command/README.md) declares
  and this composition satisfies.
- **The stubs** — this Work corrects the `Raises` of `RuleSelection.select` and
  the statement that the selection needs the contract for the roots in
  `src/wio/context/ports.pyi`; the selection reads only the Work's id.

## Acceptance criteria

The criteria use fakes of `Contracts`, `RuleSelection`, the topics port, the
skill lookup, `Settings`, `Repository` and `FileSystem`.

### **AC-1** The bundle is composed from the parts

The text is the assembly of the stage's part, the Work's resolved view and the
rules section, and the id and the size are those of that text.

#### A stage with a goal

- **Given** a Work with a resolved view, a stage with a goal, and a selection
  that includes two rules whose files are read.
- **When** the bundle is composed.
- **Then** the text is the assembly of the goal, the view and the rules section,
  the id equals `bundle_id` of the text after its first blank line, the size
  equals the UTF-8 bytes of the text after its second blank line, and the header
  states `rules: 2` and that size.

### **AC-2** The rules and their hashes are in the order printed

The mapping holds exactly the printed rules, in the order the rules section
prints them, each with `rule_hash` of the bytes of its file.

#### A selection in another order

- **Given** a selection that gives `python.API001`, a rule of a root, and then
  `process.FIX001`, a rule of a root-independent ruleset, and files with known
  bytes.
- **When** the bundle is composed.
- **Then** the codes are `process.FIX001` and `python.API001` in that order,
  each mapped to the `rule_hash` of its file's bytes.

### **AC-3** The selection is asked once

The rule selection is asked once for one composition.

#### One call

- **Given** a `RuleSelection` that counts its calls.
- **When** the bundle is composed.
- **Then** it was called once.

### **AC-4** A rule that is not included is not printed or recorded

An excluded or unselected rule is in neither the text nor the mapping, and a
selection with no included rule gives an empty mapping and a header with
`rules: 0`.

#### An excluded rule, and none included

- **Given** a selection with one included rule and one excluded rule, and a
  selection with no included rule.
- **When** the bundle is composed for each.
- **Then** the first mapping holds the included rule only, and the second is
  empty with `rules: 0` in its header.

### **AC-5** The header gets the skill exactly when the stage has one

A stage with a skill gives the header the skill's name, directory and files
hash, and a stage with a goal gives it none.

#### A skill and a goal

- **Given** a stage with a skill that a lookup finds, which counts its calls,
  and a stage with a goal.
- **When** the bundle is composed for each.
- **Then** the lookup was called once, the first header has the skill line with
  its directory and hash, the pointer in the first bundle has the same
  directory, and the second header has no skill line.

### **AC-6** A fault returns no bundle

A fault in the rules and a rule file that cannot be read raise, and nothing is
returned.

#### A fault, and an unreadable file

- **Given** a `RuleSelection` that raises `DiagnosticsError`, and one whose
  included rule has a file that cannot be read.
- **When** the bundle is composed for each.
- **Then** the first raises the `DiagnosticsError` and no file was read, and the
  second raises a `WioError` that names the rule's path.
