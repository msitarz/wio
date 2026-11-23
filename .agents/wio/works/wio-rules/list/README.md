<!-- wio
id = "ak7n2y"
template = "feature.parent"
roots = ["@descendants"]
depends_on = ["xs3dsj"]
-->

# wio rules list

## Purpose

What a root, a stage, a Work or a file is given, and which rules nothing
selects, can be learned only by reading the config and the rule files by hand,
so nobody can ask which rules apply or where a rule came from.

## Goals

- `wio rules list` lists the rules of a root, a stage, a Work at a stage or a
  file, or of the rules that references name, each by its qualified code, name
  and description or summary, with a header that names the layers it applied.
- References narrow every view, and `--not-selected` limits it to the rules that
  nothing selects anywhere.
- `--explain` shows where each rule came from or why it is out.
- Selectors that conflict, a reference that names nothing and a fault in the
  rules are refused, and every listing is also available as JSON.

## Non-Goals

- Deciding which rules apply, which the selection does, and which rules nothing
  selects, which `1gs341` does.
- Showing one rule's body, which `wio rules show` does.
- Checking the rules, which `wio rules check` does.

## Assumptions

### A-1

The views are the table of views in
[the concepts](../../../../../docs/concepts.md#listing-rules) with the flag
`--preset` replaced by references: no selector lists the rules that the
references name with no layers, `--root`, `--stage`, `--work` and `--path` give
the roots and the stage, and a reference is one of the forms `<ruleset>.<item>`,
such as `demo.ARC001` or `demo.all`, or the bare name of a rule preset of the
config.

### A-2

At most one of `--root`, `--path` and `--work` is given and each takes one
value; `--work` alone selects the Work's own roots and `--stage` with it makes
the stage decide which roots count, so `--work` does not need `--stage`.

### A-3

With a view that applies roots, `--not-selected` takes as its candidates the
rules whose ruleset is root-independent or reached by the roots of the view, and
keeps those that no entry includes anywhere in the config; without roots every
rule is a candidate.

## Mechanisms

The names of the functions below are provisional.

- **`wio rules list`** — the command, built by `fjvj3x` as a handler that runs
  the discovery once and prints the listing it builds, and completed by the
  integration of this Work, which adds the refusal on an error of the discovery
  with `refuse_on_errors` of `8zn10d` and passes the listing through the
  pipeline of C-2 to the output of `fjvj3x`, which writes through
  `render_blocks` and `encode_json` of `wio.formats`.
- **The views and the output** — the selectors, their refusals, the header and
  the text and JSON of a listing, built by `fjvj3x` over `select` of `5yb4tz`
  and the roots of `ndwemw`.
- **Narrowing** — the references that filter a view and `--not-selected`, built
  by `9r1zpd` over `expand` of `cyeth5` and the rules selected anywhere of
  `1gs341`.
- **`--explain`** — the origin of each rule and the reason a rule is out, built
  by `qxfpg9` from the effects and the routes of the selection.

## Constraints

### C-1

A refusal of this command prints nothing on standard output, as
[the command line](../../../../../src/wio/cli/README.md) requires, and a
refusal that a reference or a conflict raises happens before any output. AC-3
verifies it.

### C-2

`selected_anywhere` of `1gs341` is called once by the command, and its result is
given to `narrow` and to `explain`. The pipeline is in this order: `list_view`
of `fjvj3x` builds the `Listing`, `narrow` of `9r1zpd` narrows it, `explain` of
`qxfpg9` explains it, and the renderer of
`fjvj3x` prints it, `explain` only when `--explain` is given. The criteria of
the leaves run these functions one at a time, and AC-1 and AC-2 here run them
through the command.

### C-3

`Listing.rows` holds every rule that the view considers, and the renderer shows
a row only when its rule is included or has no decision, or when it has an
`Explanation`, or when the header is marked `not selected`, which the text
writes as `filter: not selected` and the JSON as `not_selected`. AC-5 of
`fjvj3x` verifies it.

### C-4

The header holds `view`, `work`, `layers`, `roots`, `stage`, `references` and
`not_selected`, in that order in the JSON, and every flag is declared by
`fjvj3x`: the header, the flags and `Services` are verified by AC-8 and AC-13
of that Work.

## Visuals

The diagrams are drawn from commit `1ddc8e1` of the branch
`docs/define-rules-tree`, and show only what the Work changes.

### Before

No command lists rules, so what a root, a stage, a Work or a file is given is
read from the config and the rule files by hand.

```mermaid
flowchart LR
    reader["a person"]
    cfg["config and rule files"]
    reader -. "reads by hand" .-> cfg
```

### After

`wio rules list` turns its flags into the roots and the stage, asks the
selection or the expansion for the rules, narrows them, explains them if asked,
and prints them. New parts are marked.

```mermaid
flowchart LR
    subgraph lst["wio rules list (new)"]
        views["views and selectors"]
        narrow["narrowing"]
        explain["explain"]
        render["header, text and JSON"]
    end
    sel["select, expand, rules selected anywhere"]
    roots["roots of a Work, a stage or a file"]
    shell["SUBCOMMANDS and Services (xs3dsj), with work_roots added by fjvj3x"]
    shell --> views
    views --> roots
    views --> sel
    sel --> narrow
    narrow --> explain
    explain --> render
```

## Acceptance criteria

### **AC-1** One command serves every view with references and explanations

`wio rules list` combines a view, references and `--explain` in one listing: the
rules of the view that the references name, each by its qualified code, name and
description or summary, with its origin or the reason it is out.

#### A Work at a stage, narrowed and explained

- **Given** a ruleset `demo` that declares `ARC` and `PAY` and holds `ARC001`,
  `ARC002`, `PAY001` with a description and `PAY002`, a rule preset
  `recommended` that includes `ARC` and excludes `ARC002`, a root `api` with
  `rule_presets = ["demo.recommended"]`, a stage `s` that includes
  `demo.PAY001`, and a Work whose `roots` list `api`.
- **When** `wio rules list demo.all --work <id> --stage s --explain` and
  `wio rules list demo.ARC --work <id> --stage s` run.
- **Then** the first shows `demo.ARC001` with the root `api` and the route
  `demo.recommended`, `demo.PAY001` with its description and the layer `stage`,
  and `demo.ARC002` and `demo.PAY002` out with their reasons, and a header that
  names the layers applied; the second shows `demo.ARC001` only, with no
  `from:`, `out:` or `by:` line. This is the system-level check that the
  pipeline composes; AC-2 of [wio rules](../README.md) checks the same selection
  from `context`.

### **AC-2** `--not-selected` limits any view to the rules that nothing selects

`--not-selected` keeps the rules that no root, stage or always field includes,
among the candidates of the view as A-3 says.

#### The same modifier on several views

- **Given** the repository of AC-1 with a second ruleset `web` whose rule
  `WEB001` no root reaches.
- **When** `wio rules list --not-selected`, `wio rules list --root api
  --not-selected`, `wio rules list demo.PAY --not-selected` and
  `wio rules list --stage s --not-selected` run.
- **Then** the first shows `demo.ARC002`, `demo.PAY002` and `web.WEB001`, the
  second shows `demo.ARC002` and `demo.PAY002` because `api` does not reach
  `web`, the third shows `demo.PAY002`, and the fourth shows `demo.ARC002`,
  `demo.PAY002` and `web.WEB001`.

### **AC-3** A refusal prints nothing, whichever leaf raises it

A conflict of selectors, a reference that names nothing and a fault in the rules
exit 2 with the message on standard error and nothing on standard output, so
each is refused before any output.

#### One of each source

- **Given** the repository of AC-1, and the same repository with a second
  ruleset `bad` that holds two rules of one code.
- **When** `wio rules list --root api --path src/x.py`, `wio rules list Docs`
  and `wio rules list --preset demo.recommended` run on the repository without
  `bad`, and `wio rules list demo.all` runs on the one with it.
- **Then** each exits 2, the messages say which flags conflict, that `Docs` is
  not a reference, the duplicate code, and that `--preset` is not an option, and
  none prints anything on standard output.

### **AC-4** The JSON holds the same listing as the text

`--json` prints one document with the same rules, header information, origins
and reasons as the text.

#### Text and JSON

- **Given** the repository of AC-1.
- **When** `wio rules list demo.all --work <id> --stage s --explain` runs as
  text and with `--json`.
- **Then** the document holds the header keys of C-4, the references `demo.all`,
  and every rule with the fields that AC-8 of `fjvj3x` and AC-6 of `qxfpg9` fix,
  and nothing that the text lacks.

## Additional context

- The roots rule that a stage with no `roots` needs a Work with roots, the order
  of the layers and what each exclude reaches belong to the selection, so this
  contract states only what the command shows of them.
- `--preset` of the concepts and the scope document is dropped in favour of
  references; the top Work's A-8 records the divergence.
