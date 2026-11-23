<!-- wio
id = "fjvj3x"
template = "feature.leaf"
roots = ["wio"]
depends_on = ["5yb4tz", "ndwemw", "xs3dsj", "w3k7vd"]
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
- A selector that cannot be used is refused before anything is printed, with
  exit 2.
- The arguments of the command, and what it reads the project through, are
  declared here for the other leaves of `list` to use.

## Non-Goals

- Narrowing the listing by references and `--not-selected`, which `9r1zpd` does,
  and explaining where a rule came from, which `qxfpg9` does, both on the
  `Listing` that this Work builds.
- Showing one rule's body, which `wio rules show` does.
- Choosing which rules apply, which `select` of `5yb4tz` does.

## Assumptions

### A-1

`Listing.rows` holds every rule considered, and a row is shown by the renderer
when its rule is included or has no decision, or when the row has an
`Explanation`, or when the header is marked `not selected`, which `9r1zpd` sets
for the rules that nothing selects, so a listing without those holds the
included rules only, and a listing without layers holds every rule.

### A-2

The header layer names, which are not the four layers of `cm25z9`, are `roots`,
`stage` and `always fields`, the last for both always fields.

### A-3

The command runs the discovery once and gives `list_view` the rulesets it found,
made by `ruleset_map` of `w3k7vd`, so `list` does not call
`RuleSelector.selection`, which would discover again.

## Mechanisms

The names of the types and the functions below are provisional, except that the
field sets of `Header`, `Row` and `Listing` are required, because `9r1zpd` and
`qxfpg9` read and fill them.

- **`Listing` and `Header`** — frozen, in a new `wio.models.listing`, a
  `Listing` with `header: Header` and `rows: tuple[Row, ...]`, and a `Header`
  with `view: str`, `work: str | None`, `layers: tuple[str, ...]`,
  `roots: tuple[str, ...] | None`, `stage: str | None`,
  `references: tuple[str, ...]` and `not_selected: bool`, the last two filled by
  `9r1zpd`.
- **`Row`** — frozen, in `wio.models.listing`, with `rule: Rule`,
  `decision: Decision | None`, `via: Routes` and
  `explanation: Explanation | None`.
- **`Explanation`** — a `Protocol` in `wio.models.listing` with
  `lines() -> tuple[str, ...]` and `fields() -> Mapping[str, object]`, which
  `qxfpg9` implements.
- **`ListRequest`** — frozen, with `root: str | None`,
  `path: PurePosixPath | None`, `work: str | None`, `stage: str | None`,
  `references: tuple[str, ...]`, `not_selected: bool`, `explain: bool` and
  `as_json: bool`, read from the arguments below.
- **`list_view(request, config, rulesets, work_roots) -> Listing`** — in
  `wio.rules`, where `config` is the `Config`, `rulesets` is a
  `Mapping[str, LoadedRuleset]` and `work_roots` is a `WorkRoots`; it calls
  `roots_of_path` and `stage_roots` of `ndwemw` and `select` of `5yb4tz`, and
  does no input or output of its own.
- **The arguments** — `--root`, `--path`, `--work`, `--stage`, `--not-selected`,
  `--explain` and `--json`, and the references as the positional arguments,
  declared here as one entry of `SUBCOMMANDS` of `xs3dsj`, with `--json`
  declared by the helper of that Work.
- **The selector group** — `--root`, `--path` and `--work` are a mutually
  exclusive group, so a conflict is a usage error.
- **The flags of the other leaves** — the behaviour of `--not-selected` is
  `9r1zpd`'s and that of `--explain` is `qxfpg9`'s.
- **`Services`** — `xs3dsj` declares it, and this Work adds
  `work_roots: WorkRoots` to it and wires the `WorkLookup` of `wio.contracts` to
  it in `wio.cli`, the only place that does it for the command; AC-13 verifies
  it.
- **The refusal** — the handler turns the `KeyError` for an unknown stage, root
  or Work and the `ValueError` for a Work with no roots into a `WioError` that
  names the cause, so that they exit 2 and not 70.
- **`render_blocks`** — in `wio.formats`, with `Block` frozen as
  `depth: int`, `key: str`, `title: str`, `suffix: str | None` and
  `details: tuple[str, ...]`: `render_blocks(blocks: Sequence[Block]) -> str`
  writes each first line as two spaces for each depth, the key padded to the
  widest key of all the blocks, two spaces and the title, then two more spaces
  and the suffix when there is one, and each detail on its own line indented to
  the title; moved out of `wio.contracts`, which then calls it.
- **The rendering of a listing** — the header lines, the blocks and the JSON,
  through `render_blocks` and `encode_json` of `wio.formats`.

## Acceptance criteria

### **AC-1** Without a selector every rule is listed with no layers

`wio rules list` with no selector holds every rule of every ruleset in the order
of C-2 of [wio rules](../../README.md), with no layers applied.

#### Everything

- **Given** a ruleset `demo` with `ARC001` named `keep-it-small` with the
  description `A rule is one instruction.` and `PAY001` named `pay-first`
  without one whose body starts `Pay the invoice first.`, and a ruleset `web`
  with `WEB001` named `web-rule` and an empty body.
- **When** `wio rules list` runs.
- **Then** the output is the header lines, a blank line and the three blocks, in
  that order, with the codes padded to the widest, `demo.ARC001`, which is 11
  characters, and each detail indented to the name, and no `roots:` line:

  ```text
  view: every rule
  layers: none
  roots: not applied

  demo.ARC001  keep-it-small
               A rule is one instruction.
  demo.PAY001  pay-first
               Pay the invoice first.
  web.WEB001   web-rule
  ```

### **AC-2** A root, a path or a Work gives the rules that apply to it

`--root`, `--path` and `--work` apply the roots' layer and the always fields,
and the listing holds the rules that are included for those roots.

#### The three selectors

- **Given** a ruleset `demo` that declares `ARC` and `PAY` with `ARC001`,
  `ARC002` and `PAY001`, a rule preset `arc` that includes `ARC`, a root `api`
  with the path `src/api` and `rule_presets = ["demo.arc"]`, a ruleset `web`
  whose rule `WEB001` no root reaches, a root-independent ruleset `process` with
  `FIX001` in `rules_always_include`, and a Work `W` whose `roots` list `api`.
- **When** `wio rules list --root api`, `wio rules list --path src/api/app.py`
  and `wio rules list --work W` run.
- **Then** each shows `demo.ARC001` and `demo.ARC002` with `roots: api` and
  `process.FIX001` with `roots: every root`, and not `demo.PAY001` or
  `web.WEB001`, and the header is `layers: roots, always fields` and
  `roots: api` with `view: root api`, `view: file src/api/app.py` and
  `view: Work W`.

### **AC-3** A stage adds its layer and without roots nothing is cut

`--stage` alone applies the stage's layer and the always fields with the roots
not applied, and lists each rule that is not root-independent with the roots
that reach its ruleset.

#### A stage alone and with a root

- **Given** the repository of AC-2 and a stage `s` whose `rules_include` has
  `demo.PAY001` and `web.WEB001`.
- **When** `wio rules list --stage s` and `wio rules list --root api --stage s`
  run.
- **Then** the first, whose header is `view: stage s`,
  `layers: stage, always fields` and `roots: not applied`, shows `demo.PAY001`
  with `roots: api`, `process.FIX001` with `roots: every root` and `web.WEB001`
  with `roots: none`, in the order of C-2; the second, whose header also has the
  line `stage: s`, shows `demo.ARC001`, `demo.ARC002`, `demo.PAY001` and
  `process.FIX001`, in that order, and not `web.WEB001`.

### **AC-4** `--work` alone gives the Work's roots and `--stage` decides which count

`--work` without `--stage` lists the rules of the Work's own roots with no stage
layer, and with `--stage` the stage's `roots` decide which roots count.

#### With and without a stage

- **Given** the repository of AC-2, a ruleset `web` with a rule preset `core`
  that includes `WEB001`, a root `ui` with `rule_presets = ["web.core"]`, a
  stage `s` with no rules of its own and no `roots`, and a stage `t` with
  `roots = ["ui"]`.
- **When** `wio rules list --work W`, `wio rules list --work W --stage s` and
  `wio rules list --work W --stage t` run.
- **Then** the first and the second show `demo.ARC001`, `demo.ARC002` and
  `process.FIX001`, and the third shows `web.WEB001` and `process.FIX001` and no
  rule of `demo`, its header being `roots: ui`.

### **AC-5** A rule that is out is shown only when it is asked for

A row whose rule is out is shown only when it has an `Explanation` or the header
is marked `not selected`, and it carries its decision in the JSON.

#### Included and out

- **Given** the repository of AC-2 with a stage `x` whose `rules_exclude` has
  `demo.ARC002`, and `Listing`s built by hand with the same rows, one with a
  fake `Explanation` on the row of `demo.ARC002` and one with the header marked
  `not selected`.
- **When** `wio rules list --root api --stage x` runs on the repository, and the
  renderer runs on the hand-built listings as text and as JSON.
- **Then** the command lacks `demo.ARC002`, the renderer shows the out row of
  each hand-built listing with no `roots:` line in the text and with `included`
  false and `roots` an empty array in the JSON, and hides it in a listing with
  neither.

### **AC-6** A selector that cannot be used is refused

Two selectors of `--root`, `--path` and `--work`, an unknown stage, root or
Work, a Work with no roots and a path outside the repository are each refused
with exit 2 and a message on standard error, and nothing is printed on standard
output.

#### Refusals of the views

- **Given** the repository of AC-2 and a Work `N` that lists no roots.
- **When** `wio rules list --root api --path src/x.py`,
  `wio rules list --stage none`, `wio rules list --root none`,
  `wio rules list --work none`, `wio rules list --work N` and
  `wio rules list --path ../x.py` run.
- **Then** each exits 2 and says which flags conflict, which name does not
  exist, that the Work `N` has no roots, or that the path is outside the
  repository, and prints nothing on standard output.

### **AC-7** The text is a header and indented blocks

The text holds the header lines `view:`, `layers:` and `roots:`, then `stage:`
when a stage is given and the view is not the stage, `references:` when there
are references and `filter: not selected` when marked, a blank line, and one
block for each shown rule, whose first line is the qualified code padded to the
widest code, two spaces and the name, with detail lines written only when they
have something to say.

#### The layout

- **Given** the repository of AC-2 with a rule whose code is the longest and a
  rule without a description or a summary.
- **When** `wio rules list --root api` runs.
- **Then** the header lines come first, a blank line follows, every first line
  pads its code to the same width, each detail line is indented to the name, the
  rule without a description or a summary has no description line, nothing is
  cut or wrapped, and the output ends in a newline.

### **AC-8** The JSON is one line with the header and the rules

`--json` prints one object on one line with the header keys and the rules, with
the same information as the text.

#### Text and JSON

- **Given** the repository of AC-2 with the stage `s` of AC-3.
- **When** `wio rules list --work W --stage s` runs as text and with `--json`.
- **Then** the document holds `view`, `work`, `layers`, `roots`, `stage`,
  `references`, `not_selected` and `rules` in that order, with `work` `"W"`,
  `roots` `["api"]`, `stage` `"s"`, `references` `[]` and `not_selected` false;
  each rule has `code`, `name`, `description` that is `null` when there is none,
  `summary`, `roots`, `root_independent` and `included`, and the rules are the
  ones the text shows; the fields of an explanation follow them when there is
  one, as AC-9 shows.

### **AC-9** The renderer prints an explanation without knowing it

A row with an `Explanation` has its `lines()` printed under its block and its
`fields()` added to its JSON object.

#### A fake explanation

- **Given** a `Listing` whose row has an `Explanation` whose `lines()` is
  `("note: one",)` and whose `fields()` is `{"note": "one"}`.
- **When** the listing is rendered as text and as JSON.
- **Then** the block has the line `note: one` under its other details, and the
  object has `"note": "one"` after the fields of the rule.

### **AC-10** One renderer serves both commands and changes nothing

`wio contracts list` prints through `render_blocks` and its output, in text and
in JSON, is what it was before.

#### The same bytes

- **Given** the scenarios of the acceptance tests of `wio contracts list`, and
  blocks with indent depths, a key and a title, a suffix and detail lines.
- **When** the scenarios run after the move, and `render_blocks` runs on the
  blocks.
- **Then** every output of `wio contracts list` is byte for byte what it was,
  and `render_blocks` pads the keys to the widest, indents each block by two
  spaces for each depth, writes the suffix after two more spaces, and indents
  the details to the title.

### **AC-11** The listing is deterministic and `list_view` needs no file

The same config, rulesets and arguments give the same listing in the order of
C-2, whatever the order of the tables and entries.

#### Two orders

- **Given** the repository of AC-2 declared in two orders, with no file system
  and a fake `WorkRoots`.
- **When** `list_view` runs for each selector on each.
- **Then** the listings are equal.

### **AC-12** The boundaries of a listing

An empty listing, a path in no root and a listing without layers have defined
forms.

#### Three boundaries

- **Given** a repository with no rules, the repository of AC-2 with a file
  `docs/readme.md`, and the repository of AC-1.
- **When** `wio rules list` and `wio rules list --json` run on the first,
  `wio rules list --path docs/readme.md` on the second, and
  `wio rules list --json` on the third.
- **Then** the first prints, as text, the header, a blank line and nothing else,
  and `"rules": []` in the JSON; the second has `roots: none`, applies no root
  and shows only `process.FIX001` with `roots: every root`; and the third has
  for each rule `roots` and `root_independent` null and `included` true, because
  no decision was made.

### **AC-13** The command is declared and wired

`wio rules list` is one entry of `SUBCOMMANDS` with the arguments of the
Mechanisms, and its `Services` hold a `WorkRoots` that answers for the Works of
the repository.

#### The entry and the lookup

- **Given** the table of `wio.cli` and a repository with a Work `W` whose roots
  list `api`.
- **When** `wio rules list --help` and `wio rules list --work W` run.
- **Then** the help names every flag and the references, and the second shows
  the rules of `api`, so `Services.work_roots` finds `W`.

### **AC-14** A path and a stage together

`--path` with `--stage` applies the roots that contain the file and the stage's
layer, as `--root` with `--stage` does.

#### A file and a stage

- **Given** the repository of AC-2 and the stage `s` of AC-3.
- **When** `wio rules list --path src/api/app.py --stage s` runs.
- **Then** the header is `view: file src/api/app.py`,
  `layers: roots, stage, always fields`, `roots: api` and `stage: s`, and it
  shows `demo.ARC001`, `demo.ARC002`, `demo.PAY001` and `process.FIX001`, in
  that order, and not `web.WEB001`.

## Additional context

- The refusals that more than one leaf can raise, a reference that names nothing
  and a fault in the rules, are verified by AC-3 of
  [wio rules list](../README.md); the others are verified here.
- `render_blocks` takes the layout of `render_list` in
  [`src/wio/contracts/listing.py`](../../../../../../src/wio/contracts/listing.py)
  and its first-line, padding and indent rules, with the hierarchy left to the
  caller, which gives each block its depth.
