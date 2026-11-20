<!-- wio
id = "8zn10d"
template = "feature.leaf"
roots = ["wio"]
depends_on = ["ht39xt"]
-->

# Ruleset manifest

## Purpose

The rulesets of a repository are directories of rule files and a manifest that
nothing reads, so no component can find a rule by its family or its code, or
know what a ruleset declares.

## Goals

- A ruleset's `ruleset.toml` is read into a manifest with its description, its
  families and its rule presets.
- The rulesets under `.agents/wio/rules/` are discovered as immutable
  `Ruleset`s, each with its manifest and its rules, in a fixed order and found
  by family and by code.
- A fault of a manifest, of a ruleset's name or of how its rules relate is
  reported with its place, and everything else is still read.

## Non-Goals

- Reading one rule file, which `ht39xt` does.
- Judging a reference in a rule preset, such as a family that does not exist or
  a qualified name, or a preset called `all`, which `wio rules check` does.
- The settings that the config gives a ruleset, its alias and its root
  independence.
- Writing a manifest.

## Assumptions

### A-1

A ruleset may have no families and no rules, and a manifest may be empty,
because a ruleset can be started before its first rule.

### A-2

The rule presets of a manifest have the shape of those of the config, a
`rules_include` and a `rules_exclude`, each a list of strings, so the type of
the config's rule preset serves for both.

## Mechanisms

The names of the types and the functions below are provisional.

- **`Manifest`** — in `wio.models.rule`, with the description or none, the
  families by their letters with their topics, and the rule presets by name,
  each a `RulePreset` of `wio.models.config`; immutable.
- **`read_manifest(path: PurePosixPath, text: str) -> ManifestReading`** — in
  `wio.rules`, reads the text of one `ruleset.toml` and does no input or output,
  through `decode_toml` and `closest_key` of `wio.formats`; a `ManifestReading`
  holds the manifest, or none when there is an error, and the diagnostics.
- **`Ruleset`** — in `wio.models.rule`: its name, its manifest and its rules,
  immutable, the rules in the order of family and the number of the code, with
  `rules_of(family)` and `get(code)` to find them.
- **The discovery** — `discover(root, files) -> Discovery` in `wio.rules`, whose
  frame is in [rule files](../README.md): it lists `.agents/wio/rules/` with the
  `FileSystem` port of `wio.io`, reads each ruleset's `ruleset.toml` with
  `read_manifest` and its rule files with `read_rule` of `ht39xt`, joins them in
  a `Ruleset`, and reports how the rules of one ruleset relate.

## Acceptance criteria

### **AC-1** A manifest is read

The text of a `ruleset.toml` is read into a `Manifest` with its description, its
families with their topics and its rule presets, and no diagnostic.

#### A full manifest

- **Given** a `ruleset.toml` with `description = "How to build adapters."`, the
  families `ARC = "Architecture"` and `PAY = "Payments"`, and a rule preset
  `recommended` with `rules_include = ["ARC", "PAY001"]` and
  `rules_exclude = ["ARC009"]`.
- **When** `read_manifest` reads it.
- **Then** the manifest has that description, the families `ARC` and `PAY` in
  that order with their topics, and the preset `recommended` with its two lists
  in the order written, and there is no diagnostic.

#### An empty manifest

- **Given** an empty `ruleset.toml`.
- **When** `read_manifest` reads it.
- **Then** the manifest has no description, no family and no rule preset, and
  there is no diagnostic.

### **AC-2** A fault of a manifest is an error, a doubtful key a warning

Each fault of a manifest is an error that names its place and leaves the ruleset
out, and a key it does not know is a warning that names the closest key.

#### Faults

- **Given** a `ruleset.toml` that does not parse, whose fault is on line 2, and
  one each with a `description` that is a number, `families` that is a list, a
  topic that is a number, a family written `Arc`, a rule preset written
  `Backend` and one whose `rules_include` holds a number.
- **When** `read_manifest` reads each.
- **Then** the first is one error whose place is the path followed by `:2`, each
  of the others is one error that names the path, and none returns a manifest.

#### A doubtful key

- **Given** a `ruleset.toml` with a valid `description` and a key `family`.
- **When** `read_manifest` reads it.
- **Then** it reports one warning that names `family` and suggests `families`,
  and returns the manifest.

### **AC-3** A ruleset is found by family and by code

A `Ruleset` holds its rules in the order of family and the number of the code,
and finds them by family and by code, and the rulesets are returned by name.

#### Finding rules

- **Given** a ruleset `demo` that declares `ARC` and `PAY` and holds `ARC2`,
  `ARC10`, `ARC1` and `PAY1`, and a ruleset `acme` that declares `ARC` and holds
  `ARC1`.
- **When** the discovery runs.
- **Then** it returns `acme` and `demo` in that order, the rules of `demo` as
  `ARC1`, `ARC2`, `ARC10`, `PAY1`, `rules_of("ARC")` gives the first three,
  `rules_of("ZZZ")` gives none, `get("ARC2")` gives that rule and `get("ARC3")`
  gives none.

#### A ruleset is a value

- **Given** two discoveries of the same files.
- **When** the rulesets are compared.
- **Then** they are equal with one hash, and a ruleset that differs in a rule is
  not equal.

### **AC-4** The rules of one ruleset must relate

A rule whose family the manifest does not declare, and rules that share a code
or a name, are errors that name their places and leave those rules out.

#### An undeclared family

- **Given** a ruleset `demo` whose manifest declares `ARC` and that holds
  `ARC001` and `ZZZ001`.
- **When** the discovery runs.
- **Then** it reports one error that names the file of `ZZZ001` and the family
  `ZZZ`, and `demo` holds `ARC001` only.

#### A shared code or name

- **Given** a ruleset `demo` that declares `ARC` and holds two files with the
  code `ARC001`, two other rules with the name `keep-it-small`, and `ARC009`.
- **When** the discovery runs.
- **Then** it reports one error for the code that names both files and one for
  the name that names both files, and `demo` holds `ARC009` only.

#### The same code in two rulesets

- **Given** two rulesets that each hold `ARC001`.
- **When** the discovery runs.
- **Then** it reports no error and both rules are returned, because a qualified
  code is unique.

### **AC-5** A ruleset's name and place come from its directory

A ruleset is named by its directory directly under `.agents/wio/rules/`, in the
form of a ruleset name, and hidden directories and symbolic links are not
rulesets.

#### The name of a ruleset

- **Given** the directories `demo`, `My_Rules`, `.cache` and a symbolic link
  `linked` to a ruleset, each with a valid `ruleset.toml`.
- **When** the discovery runs.
- **Then** it returns `demo` only and reports one error for `My_Rules`, which
  names the directory and says its name is not in the form of a ruleset name,
  and neither the hidden directory nor the link is read or reported.

## Additional context

- The faults of a directory, a stray rule file, a `ruleset.toml` below a
  ruleset's directory, a directory without a manifest and a rules directory that
  is a symbolic link or not a directory, are verified once, by AC-2 of
  [rule files](../README.md), because they belong to the discovery that this
  Work builds with the frame it states there.
