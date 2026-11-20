<!-- wio
id = "fjvj3x"
template = "feature.leaf"
roots = ["wio"]
depends_on = ["5yb4tz", "ndwemw", "9pfyfe"]
-->

# Listing by selection

## Purpose

The rules that a root, a stage, a Work or a file is given are decided by the
selection but shown by nothing, so a person cannot see them, and no program can
read them.

## Goals

- The selectors of `wio rules list` give the roots and the stage, and the
  listing holds the rules that apply for them, or every rule when there is no
  selector.
- A header says which layers were applied and which roots, and each rule is a
  block with its qualified code, name, description or summary and roots, in the
  indented form of `wio contracts list`, or one line of JSON for a program.
- The block layout is one renderer in `wio.formats` that `wio contracts list`
  and `wio rules list` both use.
- A selector that cannot be used is refused before anything is printed.

## Non-Goals

- Narrowing the listing by references and `--not-selected`, which `9r1zpd` does,
  and explaining where a rule came from, which `qxfpg9` does, both on the
  `Listing` that this Work builds.
- Showing one rule's body, which `wio rules show` does.
- Choosing which rules apply, which `select` of `5yb4tz` does.

## Assumptions

### A-1

A rule that is out for a view is shown only when `--explain` is given, so a
listing without it holds the included rules only, and a listing without layers
holds every rule.

### A-2

The text of the view for the roots that a stage selects names the Work and the
stage, and the names of the layers that applied are `roots`, `stage` and
`always fields`.

## Mechanisms

The names of the types and the functions below are provisional.

- **`Listing`** — frozen, with `header: Header` and `rows: tuple[Row, ...]`; a
  `Row` holds the `Rule` and its `Decision`, or none when no layers applied; a
  `Header` holds the view, the layers applied, the roots or none when they are
  not applied, the stage, and the references and `--not-selected` that narrowing
  fills in.
- **`list_view(request, config, rulesets, selector) -> Listing`** — in
  `wio.rules`, built from the selectors of the request: `roots_of_path` and
  `stage_roots` of `ndwemw`, `select` of `5yb4tz` and `RuleSelector.selection`
  of `9pfyfe` for a Work; it does no input or output.
- **The command's arguments** — `--root`, `--path`, `--work`, `--stage`,
  `--explain` and `--json`, and the references, read into a request.
- **`render_blocks`** — in `wio.formats`, which writes items as blocks: each
  `Block` has an indent depth, a key, a title, an optional suffix and detail
  lines; the first line is the key padded to the widest key of the output, two
  spaces and the title, and the details are indented to the title; moved out of
  `wio.contracts`, which then calls it.
- **The rendering of a listing** — the header lines, the blocks and the JSON,
  through `render_blocks` and `encode_json` of `wio.formats`.

## Acceptance criteria

### **AC-1** Without a selector every rule is listed with no layers

`wio rules list` with no selector holds every rule of every ruleset in the order
of A-8 of [wio rules](../../README.md), with no layers applied.

#### Everything

- **Given** a ruleset `demo` with `ARC001` named `keep-it-small` with the
  description `A rule is one instruction.` and `PAY001` named `pay-first`
  without one whose body starts `Pay the invoice first.`, and a ruleset `web`
  with `WEB001`.
- **When** `wio rules list` runs.
- **Then** the header says the view is every rule, that no layers applied and
  that roots are not applied, and the blocks are `demo.ARC001  keep-it-small`
  with the description under it, `demo.PAY001  pay-first` with the summary under
  it, and `web.WEB001`, in that order, with no `roots:` line.

### **AC-2** A root, a path or a Work gives the rules that apply to it

`--root`, `--path` and `--work` apply the roots' layer and the always fields,
and the listing holds the rules that are included for those roots.

#### The three selectors

- **Given** a ruleset `demo` that declares `ARC` and `PAY` with `ARC001`,
  `ARC002` and `PAY001`, a root `api` with the path `src/api` whose rule preset
  includes `ARC`, a ruleset `web` whose rule `WEB001` no root reaches, a
  root-independent ruleset `process` with `FIX001` in `rules_always_include`,
  and a Work whose `roots` list `api`.
- **When** `wio rules list --root api`, `wio rules list --path src/api/app.py`
  and `wio rules list --work <id>` run.
- **Then** each shows `demo.ARC001` and `demo.ARC002` with `roots: api` and
  `process.FIX001` with `roots: every root`, and not `demo.PAY001` or
  `web.WEB001`, and the header names the layers `roots` and `always fields` and
  the roots `api`.

### **AC-3** A stage adds its layer and without roots nothing is cut

`--stage` alone applies the stage's layer and the always fields with the roots
not applied, and lists each rule that is not root-independent with the roots
that reach its ruleset.

#### A stage alone

- **Given** the repository of AC-2 and a stage `s` whose `rules_include` has
  `demo.PAY001` and `web.WEB001`.
- **When** `wio rules list --stage s` and `wio rules list --root api --stage s`
  run.
- **Then** the first shows `demo.PAY001` with `roots: api`, `web.WEB001` with
  `roots: none` and `process.FIX001` with `roots: every root`, and its header
  says that roots are not applied; the second shows `demo.PAY001`,
  `demo.ARC001`, `demo.ARC002` and `process.FIX001` and not `web.WEB001`.

### **AC-4** Rules that are out are shown only with `--explain`

A rule that a layer excluded or the roots cut is left out of the listing and
shown only with `--explain`, with the fact that it is out.

#### Included and out

- **Given** the repository of AC-2 and a stage whose `rules_exclude` has
  `demo.ARC002`.
- **When** `wio rules list --root api --stage s` and the same with `--explain`
  run.
- **Then** the first lacks `demo.ARC002`, and the second shows it marked as out.

### **AC-5** A selector that cannot be used is refused

An unknown stage or root, and a path outside the repository, are each refused
with exit 2 and a message on standard error, and nothing is printed on standard
output.

#### Refusals of the views

- **Given** the repository of AC-2.
- **When** `wio rules list --stage none`, `wio rules list --root none` and
  `wio rules list --path ../x.py` run.
- **Then** each exits 2 and says which name does not exist or that the path is
  outside the repository, and prints nothing on standard output.

### **AC-6** The text is indented blocks with a header

The text holds a header of `key: value` lines, a blank line, and one block for
each rule, whose first line is the qualified code padded to the widest code, two
spaces and the name, with detail lines written only when they have something to
say.

#### The layout

- **Given** the repository of AC-2 with a rule whose code is the longest and a
  rule without a description or a summary.
- **When** `wio rules list --root api` runs.
- **Then** the header lines come first, a blank line follows, every first line
  pads its code to the same width, each detail line is indented to the name, the
  rule without a description or a summary has no description line, nothing is
  cut or wrapped, and the output ends in a newline.

### **AC-7** The JSON is one line with a fixed order

`--json` prints one object on one line with the header and the rules, with the
same information as the text.

#### Text and JSON

- **Given** the repository of AC-2.
- **When** `wio rules list --root api --explain` runs as text and with `--json`.
- **Then** the document holds `view`, `layers`, `roots`, `stage` and `rules` in
  that order, each rule has `code`, `name`, `description` that is `null` when
  there is none, `summary`, `roots`, `root_independent` and `included`, and the
  rules are the ones the text shows.

### **AC-8** One renderer serves both commands and changes nothing

`wio contracts list` prints through `render_blocks` and its output, in text and
in JSON, is what it was before.

#### The same bytes

- **Given** the scenarios of the acceptance tests of `wio contracts list`, and
  blocks with indent depths, a key and a title, a suffix and detail lines.
- **When** the scenarios run after the move, and `render_blocks` runs on the
  blocks.
- **Then** every output of `wio contracts list` is byte for byte what it was,
  and `render_blocks` pads the keys to the widest, indents each block by two
  spaces for each depth, and indents the details to the title.

### **AC-9** The listing is deterministic and `list_view` needs no file

The same config, rulesets and arguments give the same listing in the order of
A-8, whatever the order of the tables and entries.

#### Two orders

- **Given** the repository of AC-2 declared in two orders, with no file system.
- **When** `list_view` runs for each selector on each.
- **Then** the listings are equal.

## Additional context

- The refusals of two selectors together, an unknown Work, a Work with no roots,
  a reference that names nothing and a fault in the rules are verified by AC-3
  of [wio rules list](../README.md), because the command raises them from more
  than one of the leaves.
- `render_blocks` takes the layout of `render_list` in
  `src/wio/contracts/listing.py` and its first-line, padding and indent rules,
  with the hierarchy left to the caller, which gives each block its depth.
