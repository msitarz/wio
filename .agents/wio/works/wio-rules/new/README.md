<!-- wio
id = "km9cmc"
template = "feature.leaf"
roots = ["wio"]
depends_on = ["8zn10d", "1gs341"]
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
- The file is valid at once: `wio rules check` reports no error for it.
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

## Mechanisms

The names of the functions below are provisional.

- **`plan_rule(ruleset, family, name, description, discovery) -> NewRule`** — in
  `wio.rules`, which judges the request against the `Discovery` of `8zn10d` and
  returns the path, the text and the `Rule` to write, or refuses; it does no
  input or output.
- **The command** — `wio rules new`, with `--name`, `--description` and
  `--json`, which writes the file through the `FileSystem` port, runs the
  discovery again to read the file back, and asks `selected_anywhere` of
  `1gs341` whether anything selects the rule.
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
  `ARC004-keep-it-small.md`, and says it created `demo.ARC004`; `ARC002` is not
  used.

#### An empty family

- **Given** the same ruleset, which holds no `PAY` rule.
- **When** `wio rules new demo PAY --name pay-first` runs.
- **Then** the code is `PAY001`.

### **AC-2** The number is as wide as the family's

The number is padded to at least three digits and to the width of the highest
code of the family.

#### Widths

- **Given** families whose highest codes are `ARC999`, `ARC0007` and `ARC12`.
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
  `keep-it-small`, and an unrelated file at the path `ARC002-other.md`.
- **When** `wio rules new nope ARC --name x`, `wio rules new demo ZZZ --name x`,
  `wio rules new demo ARC --name Bad_Name`, `wio rules new demo ARC --name x
  --description ""`, `wio rules new demo ARC --name keep-it-small` and
  `wio rules new demo ARC --name other` run.
- **Then** each exits 2 with a message on standard error, which lists the
  rulesets that exist, lists the families that `demo` declares, gives the form
  of a name, says the description must be one line that is not blank, names the
  rule that has the name, and says the file exists, and no file is written or
  changed.

### **AC-7** A fault in the rules refuses the command

An error of the discovery anywhere in the repository, including in another
ruleset, refuses the command, and no file is written.

#### A fault elsewhere

- **Given** a valid ruleset `demo` and another ruleset `bad` with two rules of
  one code.
- **When** `wio rules new demo ARC --name keep-it-small` runs.
- **Then** it exits 2 with the error of the duplicate code on standard error and
  writes no file.

### **AC-8** The result says whether anything selects the new rule

The result tells whether some entry delivers the new rule, and by which source.

#### Selected and not yet

- **Given** a ruleset `demo` with a rule preset `recommended` that includes
  `ARC`, a root `api` whose rule preset is `demo.recommended`, and a family
  `PAY` that no entry includes.
- **When** `wio rules new demo ARC --name keep-it-small` and
  `wio rules new demo PAY --name pay-later` run.
- **Then** the first says it is selected, by root `api` through
  `demo.recommended`, and the second says that nothing selects it yet.

### **AC-9** The JSON is one line with a fixed order

`--json` prints one object on one line with the code, the name, the path,
whether it is selected and the sources.

#### Text and JSON

- **Given** the repository of AC-8.
- **When** the two requests of AC-8 run with `--json`.
- **Then** each document has `code`, `name`, `path`, `selected` and `sources` in
  that order, with `selected` true and one source for the first and false and no
  source for the second, and says what the text says.

### **AC-10** The same repository gives the same file

The same repository and the same request give a file of the same name and bytes,
and the command creates exactly one file.

#### Two runs

- **Given** two copies of one repository.
- **When** the same `wio rules new` request runs on each.
- **Then** the two new files have the same path and the same bytes, and nothing
  else in either copy changed.

## Additional context

- The empty body is deliberate: `wio rules check` has no rule about a missing
  instruction because whether a rule is good is for a reviewer, and `wio rules
  list` shows an empty summary until the author writes one.
- The top Work states that `new` writes only the comment form, and that a
  refusal for a fault is verified there by its AC-9; the causes of a refusal
  that belong to the request itself are verified here.
