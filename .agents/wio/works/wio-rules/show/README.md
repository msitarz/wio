<!-- wio
id = "ca70ny"
template = "feature.leaf"
roots = ["wio"]
depends_on = ["8zn10d", "fjvj3x", "xs3dsj", "w3k7vd"]
-->

# wio rules show

## Purpose

A listing shows a rule in one line and a bundle shows it only to a session, so a
person who wants to read one rule's description, file and whole body has to find
and open its file.

## Goals

- `wio rules show` prints one rule by its qualified code: its name, description
  and file in the indented form of the other listings, and then its body as the
  reader returns it.
- The same rule is available as one line of JSON.
- A reference that is not one rule's code, and a fault in the rules, are refused
  before anything is printed.

## Non-Goals

- Showing where a rule came from, whether it is selected or which roots it
  applies to, which `wio rules list --explain` does.
- Showing the body of several rules, which a program does with `--json` and a
  loop.
- Editing the rule.

## Assumptions

### A-1

The reference is one rule's qualified code, `<ruleset>.<code>`, where the
ruleset may be its alias, because a rule is named by its ruleset and code and
never by a bare code, as C-4 of [wio rules](../README.md) says.

### A-2

The body is printed as the reader returns it, without its leading and trailing
blank lines, with the line endings it has, followed by one line feed.

### A-3

Standard output does not translate line ends, so a CRLF inside a body reaches
the reader of the output as it is stored.

### A-4

The command resolves the ruleset part of the reference, which may be an alias,
with `resolve_ruleset` of `w3k7vd`, over `Sources` from `ruleset_map` and
`build_sources`, and `show_rule` knows canonical names
only.

## Mechanisms

The names of the functions below are provisional.

- **`show_rule(reference: str, discovery: Discovery) -> Rule`** — in
  `wio.rules`, which judges the reference with `parse_reference` and `item_kind`
  of `wio.formats`, finds the rule in the `Discovery` of `8zn10d` by its
  canonical ruleset and code, or refuses; it does no input or output.
- **The command** — `wio rules show`, with `--json`, an entry of `SUBCOMMANDS`
  of `xs3dsj`, which resolves the alias and renders the header with
  `render_blocks` of `wio.formats`, built with `fjvj3x`, followed by the body,
  or the JSON with `encode_json`.
- **The refusal** — a `WioError` that names the cause, which `wio.cli` turns
  into exit 2.

## Acceptance criteria

### **AC-1** A rule is shown with its header and its body

`wio rules show` prints the rule's qualified code and name, its description when
it has one, its file, a blank line, and its body as the reader returns it.

#### A rule with a description

- **Given** a rule `demo.ARC001` named `keep-it-small` in
  `.agents/wio/rules/demo/ARC001-keep-it-small.md`, with the description
  `A rule is one instruction.` and the body
  `State one instruction in each rule.`, a blank line and
  `Why: a long rule hides several decisions.`.
- **When** `wio rules show demo.ARC001` runs.
- **Then** it prints `demo.ARC001  keep-it-small`, the line
  `A rule is one instruction.` and the line
  `file: .agents/wio/rules/demo/ARC001-keep-it-small.md`, each detail indented
  to the name, a blank line, the two paragraphs of the body with the blank line
  between them, and ends with one line feed.

### **AC-2** A rule without a description or a body

A rule without a description has no description line, and a rule without a body
prints only its header.

#### Nothing to say

- **Given** a rule `demo.ARC002` named `other-rule` with no description and an
  empty body.
- **When** `wio rules show demo.ARC002` runs.
- **Then** it prints `demo.ARC002  other-rule` and the file line, no description
  line and no blank line or body after them, and ends with one line feed.

### **AC-3** The body is printed as the reader returns it

The body keeps its leading spaces and its line endings, and nothing is added
before or after it but the blank line that follows the header and the final line
feed.

#### Indentation and CRLF

- **Given** a rule whose body starts with two spaces on its first line, and a
  rule whose file has CRLF line endings.
- **When** `wio rules show` runs for each.
- **Then** the first body starts with its two spaces, the second body keeps its
  CRLF line endings between its lines, and each is followed by one line feed.

### **AC-4** A ruleset's alias is accepted

An alias works as the ruleset part of the reference, and the output names the
rule by its canonical ruleset.

#### An alias

- **Given** a ruleset `demo` with the alias `d`.
- **When** `wio rules show d.ARC001` runs.
- **Then** it shows the rule as `demo.ARC001`, not `d.ARC001`.

### **AC-5** A reference that is not one rule's code is refused

A family, a rule preset, `all`, a bare code, a malformed reference, an unknown
ruleset and an unknown rule are each refused with exit 2 and a message that says
what is wrong, and nothing is printed on standard output.

#### Each reference

- **Given** a ruleset `demo` that declares `ARC` and holds `ARC001` and
  `ARC002`, and a rule preset `recommended`.
- **When** `wio rules show demo.ARC`, `wio rules show demo.recommended`,
  `wio rules show demo.all`, `wio rules show ARC001`, `wio rules show Docs`,
  `wio rules show nope.ARC001`, `wio rules show demo.ARC999` and
  `wio rules show demo.arc001` run.
- **Then** each exits 2 and says that `demo.ARC` is a family and `show` takes a
  rule's code, that `demo.recommended` and `demo.all` are rule presets, that
  `ARC001` has no ruleset, that `Docs` is not a reference, that no ruleset is
  `nope`, that `demo` holds `ARC001` and `ARC002` and not `ARC999`, and that
  `demo.arc001` is not a code, which wins over reading it as a rule preset.

### **AC-6** A warning refuses nothing

A warning of the discovery does not refuse the command, while an error anywhere
refuses it as AC-9 of [wio rules](../README.md) says.

#### A warning

- **Given** a valid rule `demo.ARC001` whose block has an unknown key.
- **When** `wio rules show demo.ARC001` runs.
- **Then** it shows the rule and exits 0.

### **AC-7** The JSON is one line with a fixed order

`--json` prints one object on one line with the rule's code, name, description,
summary, body and path.

#### Text and JSON

- **Given** the rules of AC-1 and AC-2.
- **When** `wio rules show demo.ARC001 --json` and
  `wio rules show demo.ARC002 --json` run.
- **Then** each document has `code`, `name`, `description` that is `null` when
  there is none, `summary`, `body` and `path` in that order, with the qualified
  code, the body as the reader returns it and no final line feed in the body,
  and says what the text says.

### **AC-8** The output is deterministic and nothing is written

The same repository and reference give the same bytes, and the repository is
left as it was.

#### Two runs

- **Given** one repository.
- **When** `wio rules show demo.ARC001` runs twice, as text and as JSON.
- **Then** the outputs are equal, and no file of the repository changed.

## Additional context

- A rule's file path in the output is relative to the repository root and
  written with `/`, as the places of the other commands are.
