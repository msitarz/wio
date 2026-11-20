<!-- wio
id = "km9cmc"
template = "feature.leaf"
roots = ["wio"]
depends_on = ["8zn10d", "1gs341", "xs3dsj"]
-->

# wio rules new

## Purpose

A rule's code must be the next number of its family and its file must be valid,
and writing one by hand risks a clashing code or a malformed block, so authors
need a command that creates the rule and says whether anything selects it.

## Goals

- `wio rules new` creates a rule file in a ruleset with the next code of its
  family, which never fills a gap, and a name and an optional description that
  the author gives.
- The file is valid at once: `wio rules check` reports no error for it, whatever
  characters the description holds.
- The result says whether anything selects the new rule and by what, in text and
  in JSON.
- A request that cannot be met is refused before anything is written, and no
  file is overwritten.

## Non-Goals

- Writing a body for the rule, because a placeholder would reach a bundle if it
  were never edited, so the body is empty and the author writes it.
- Writing a rule with `+++` front matter, or choosing the form, as the top Work
  says.
- Editing, renaming, moving or deleting a rule, and adding a family or a rule
  preset to a manifest, which no command does.

## Assumptions

### A-1

The author gives the ruleset, which may be its alias, the family and the name,
so `wio rules new <ruleset> <family> --name <name>` with `--description <text>`
as an option, and the code is not chosen by the author.

### A-2

The width of the number of a code is at least three digits and at least the
width of the highest code of the family, so `ARC999` is followed by `ARC1000`
and `ARC0007` by `ARC0008`.

### A-3

The file is named `<code>-<name>.md`, a convention that no command reads, as the
top Work says.

### A-4

The command resolves an alias to the canonical name of the ruleset from the
`rulesets` of the config before it plans the rule, so `plan_rule` knows
canonical names only.

### A-5

A rule is selected when some entry of the config delivers it, whatever the
roots, as A-2 of `1gs341` says, so the result can say selected for a rule that
no session receives because its ruleset is not reached.

## Mechanisms

The names of the functions below are provisional.

- **`plan_rule(ruleset: str, family: str, name: str, description: str | None,
  discovery: Discovery) -> NewRule`** — in `wio.rules`, which judges the request
  against the `Discovery` of `8zn10d` and refuses an unknown ruleset, a family
  that the manifest does not declare, a name or a description of the wrong form
  and a name that the ruleset has; it does no input or output. A `NewRule` is
  frozen, with `path: PurePosixPath`, `text: str` and `rule: Rule`.
- **The command** — `wio rules new`, with `--name`, `--description` and
  `--json`, an entry of `SUBCOMMANDS` of `xs3dsj`. It resolves the alias, plans
  the rule, checks that `FileSystem.exists` is false for the path, because
  `write_text` overwrites, writes the file, runs the discovery again to read it
  back, and asks `selected_anywhere` of `1gs341` whether anything selects the
  rule.
- **The block** — written by `encode_comment_toml` of `wio.formats`, which
  escapes a quote, a backslash and the `-->` that would close the comment early.
- **The refusal** — a `WioError` that names the cause, which `wio.cli` turns
  into exit 2.

## Acceptance criteria

### **AC-1** A new rule gets the next code and never fills a gap

The new rule's code is the family's letters and the number after the highest
number in the family, and a number that is free below it is not reused.

#### A gap is left alone

- **Given** a ruleset `demo` that declares `ARC` and `PAY` and holds `ARC001`
  and `ARC003`.
- **When** `wio rules new demo ARC --name keep-it-small` runs.
- **Then** it creates a rule with the code `ARC004`, a file named
  `ARC004-keep-it-small.md`, and says it created `demo.ARC004 keep-it-small`;
  `ARC002` is not used.

#### An empty family

- **Given** the same ruleset, which holds no `PAY` rule.
- **When** `wio rules new demo PAY --name pay-first` runs.
- **Then** the code is `PAY001`.

### **AC-2** The number is as wide as the family's

The number is padded to at least three digits and to the width of the highest
code of the family.

#### Widths

- **Given** three rulesets that each declare `ARC`, whose highest codes are
  `ARC999`, `ARC0007` and `ARC12`.
- **When** `wio rules new` runs for each.
- **Then** the new codes are `ARC1000`, `ARC0008` and `ARC013`.

### **AC-3** The file is written next to the family's last rule

The file goes in the directory of the rule with the highest code of the family,
and in the ruleset's directory when the family has none.

#### Where it goes

- **Given** a ruleset `demo` whose `ARC001` and `ARC002` are in a subdirectory
  `arc/` and whose family `PAY` has no rule.
- **When** `wio rules new demo ARC --name keep-it-small` and
  `wio rules new demo PAY --name pay-first` run.
- **Then** the first file is in `arc/` and the second is directly in the
  ruleset's directory.

### **AC-4** The file is valid and in the comment form

The file has a `<!-- wio -->` block with the code, the name and, when given, the
description, and an empty body, whatever form the other rules have, and the
discovery reads it back as the rule that was planned.

#### A new file

- **Given** a ruleset whose existing rules use `+++` front matter, and a request
  with `--description "A rule is one instruction."`.
- **When** `wio rules new` runs.
- **Then** the new file starts with `<!-- wio`, holds the code, the name and the
  description, has an empty body, the existing files are unchanged, and the
  discovery returns the new rule with that code, name and description.

#### A description with special characters

- **Given** the description `Use "quotes", a \ and --> carefully.`.
- **When** `wio rules new` runs with it.
- **Then** the file has one `<!-- wio -->` block that the discovery reads, and
  the rule it returns has exactly that description.

### **AC-5** A ruleset's alias is accepted and the canonical name is shown

An alias works wherever the ruleset's name does, and the result names the
ruleset by its canonical name.

#### An alias

- **Given** a ruleset `demo` with the alias `d`.
- **When** `wio rules new d ARC --name keep-it-small` runs.
- **Then** the file is in the directory of `demo` and the result says
  `demo.ARC…`, not `d.ARC…`.

### **AC-6** A request that cannot be met is refused and writes nothing

An unknown ruleset, a family that the manifest does not declare, a name that is
not in the form of a name, a description that is not one line, a name that
another rule of the ruleset has, and a file that already exists are each refused
with exit 2.

#### Each cause

- **Given** a ruleset `demo` that declares `ARC` and holds `ARC001` named
  `keep-it-small`, and an unmarked file `ARC002-other.md` in its directory.
- **When** `wio rules new nope ARC --name x`, `wio rules new demo ZZZ --name x`,
  `wio rules new demo ARC --name Bad_Name`, `wio rules new demo ARC --name x
  --description ""`, `wio rules new demo ARC --name keep-it-small` and
  `wio rules new demo ARC --name other` run.
- **Then** each exits 2 with a message on standard error, which lists the
  rulesets that exist, lists the families that `demo` declares, gives the form
  of a name, says the description must be one line that is not blank, names the
  rule that has the name, and says the file `ARC002-other.md` exists, and no
  file is written or changed.

### **AC-7** A fault in another ruleset refuses the command

An error of the discovery anywhere in the repository, including in a ruleset
that is not the one asked for, refuses the command, and no file is written; the
case of two rules with one code is verified by AC-9 of
[wio rules](../README.md).

#### A fault elsewhere

- **Given** a valid ruleset `demo` and another ruleset `bad` with a rule whose
  block does not close.
- **When** `wio rules new demo ARC --name keep-it-small` runs.
- **Then** it exits 2 with the error of the block on standard error and writes
  no file.

### **AC-8** A warning refuses nothing

A warning of the discovery does not refuse the command.

#### A warning

- **Given** a valid ruleset `demo` that declares `ARC`, with a rule whose block
  has an unknown key.
- **When** `wio rules new demo ARC --name keep-it-small` runs.
- **Then** it creates the rule and exits 0.

### **AC-9** The result says whether anything selects the new rule

The result tells whether some entry delivers the new rule, and by which source,
in the chain form of `wio rules list --explain`.

#### Selected and not yet

- **Given** a ruleset `demo` holding `ARC001` to `ARC003`, with a rule preset
  `recommended` that includes `ARC`, a root `api` whose rule preset is
  `demo.recommended`, a stage `s` whose
  `rules_include` has `demo.ARC` and a family `PAY` that no entry includes.
- **When** `wio rules new demo ARC --name keep-it-small` and
  `wio rules new demo PAY --name pay-later` run.
- **Then** the first prints `created demo.ARC004 keep-it-small`, the line
  `file: <path>` and two lines
  `selected: demo.ARC004 ← root api ← demo.recommended ← demo.ARC` and
  `selected: demo.ARC004 ← stage s ← demo.ARC`, and the second prints its first
  two lines and `selected: no, nothing selects it yet`.

### **AC-10** The JSON is one line with a fixed order

`--json` prints one object on one line with the qualified code, the name, the
path, whether it is selected and the sources.

#### Text and JSON

- **Given** the repository of AC-9.
- **When** the two requests of AC-9 run with `--json`.
- **Then** each document has `code`, `name`, `path`, `selected` and `sources` in
  that order, with `code` the qualified code, `selected` true and `sources` the
  two arrays of labels such as `["root api", "demo.recommended", "demo.ARC"]`
  for the first, and false and an empty array for the second, and says what the
  text says.

### **AC-11** The same repository gives the same file

The same repository and the same request give a file of the same name and bytes,
and the command creates exactly one file.

#### Two runs

- **Given** two copies of one repository.
- **When** the same `wio rules new` request runs on each.
- **Then** the two new files have the same path and the same bytes, and nothing
  else in either copy changed.

## Additional context

- The empty body is deliberate: `wio rules check` has no rule about a missing
  instruction because whether a rule is good is for a reviewer.
- The top Work states that `new` writes only the comment form, and that two
  rules with one code refuse `new`, `list` and `show` alike by its AC-9; the
  causes of a refusal that belong to the request itself are verified here.
