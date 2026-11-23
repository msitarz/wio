<!-- wio
id = "8zn10d"
template = "feature.leaf"
roots = ["wio"]
depends_on = ["ht39xt", "zq07av"]
-->

# Ruleset manifest

## Purpose

The rulesets of a repository are directories of rule files and a manifest that
nothing reads, so no component can find a rule by its family or its code, or
know what a ruleset declares.

## Goals

- A ruleset's `ruleset.toml` is read into a `Manifest` with its description, its
  families and its rule presets.
- The rulesets under `.agents/wio/rules/` are discovered as immutable
  `LoadedRuleset`s, each with its manifest and its rules, in a fixed order and
  found by family and by code.
- A fault of a manifest, of a rules directory, of a ruleset's directory or
  files, of a stray file, or of how the rules of one ruleset relate, is reported
  with its place, and everything else is still read.
- A discovery with an error is refused by one function that every command that
  must not work from it calls.

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

### A-3

The rules of one ruleset have distinct names as well as distinct codes, as
`docs/v0.1-scope.md` says, although the concepts do not list it.

### A-4

A `ruleset.toml` in a hidden subdirectory of a ruleset is not looked for, and a
hidden directory directly under `.agents/wio/rules` is not a ruleset, because
the shared walk does not enter hidden directories.

## Mechanisms

The names of the types and the functions below are provisional.

- **`Manifest`** — a frozen dataclass in `wio.models.rule` with
  `description: str | None`, `families: Mapping[str, str]` by the letters of the
  family with its topic, and `rule_presets: Mapping[str, RulePreset]` by name,
  each a `RulePreset` of `wio.models.config`; the mappings are frozen so that it
  hashes.
- **`read_manifest(path: PurePosixPath, text: str) -> ManifestReading`** — in
  `wio.rules`, reads the text of one `ruleset.toml` and does no input or output,
  through `decode_toml` and `closest_key` of `wio.formats`; a `ManifestReading`
  holds `manifest: Manifest | None` and `diagnostics: tuple[Diagnostic, ...]`.
- **The name forms** — the forms of a ruleset name, a family and a rule preset
  name of `wio.formats`, which `zq07av` moves there with the grammar and which
  this Work reuses.
- **The key paths** — `join_path` and `item_path` of `wio.formats`, which
  `zq07av` moves there and `read_manifest` uses for the places of AC-2.
- **`refuse_on_errors(discovery: Discovery) -> None`** — in `wio.rules`, raising
  the `DiagnosticsError` of `wio.errors` that carries the error diagnostics of
  the discovery, and not its warnings, and doing nothing when there is none.
- **`LoadedRuleset`** — a frozen dataclass in `wio.models.rule` with
  `name: str`, `path: PurePosixPath`, `manifest: Manifest` and
  `rules: tuple[Rule, ...]` in the order of C-2 of [wio rules](../../README.md),
  and the methods `rules_of(family: str) -> tuple[Rule, ...]` and
  `get(code: str) -> Rule | None`; it is not the `Ruleset` of
  `wio.models.config`, which holds the settings that the config gives a ruleset.
- **The discovery** — `discover(root: Path, files: FileSystem) -> Discovery` in
  `wio.rules`, where `Discovery` holds `rulesets: tuple[LoadedRuleset, ...]` and
  `diagnostics: tuple[Diagnostic, ...]` as that of `wio.templates` does; it
  lists `.agents/wio/rules/` and the subdirectories of each ruleset with the
  `FileSystem` port of `wio.io`, which it needs to see a directory that holds no
  Markdown file and a `ruleset.toml` below a ruleset's directory, reads each
  ruleset's files with `walk_markdown`, `read_manifest` and `read_rule` of
  `ht39xt`, and joins them; it judges `.agents/wio/rules` with
  `refuse_directory` of `wio.io` before it walks it, and a file directly in it
  is a stray rule file when `read_metadata_block` finds a block in it, a block
  that cannot be read being reported as that fault.

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

Each fault of a manifest is an error that names its place and returns no
manifest, and a key it does not know is a warning that names the closest key.

#### Faults

- **Given** a `ruleset.toml` that does not parse, whose fault is on line 2, and
  one each with a `description` that is a number, `families` that is a list, a
  topic that is a number, a family written `Arc`, a rule preset written
  `Backend`, a rule preset that is a string, a `rules_include` that is a string,
  and a `rules_include` that holds a number.
- **When** `read_manifest` reads each.
- **Then** the first is one error whose place is the path followed by `:2`, each
  of the others is one error whose place is the manifest's path followed by `#`
  and the key path of the fault, such as `#description` and
  `#rule_presets.x.rules_include`, and none returns a manifest.

#### A doubtful key

- **Given** a `ruleset.toml` with a valid `description` and a key `family`, and
  another with a rule preset that has a key `rules_includes`.
- **When** `read_manifest` reads each.
- **Then** each reports one warning that names the key and the closest known
  key, `families` and `rules_include`, and returns the manifest.

### **AC-3** A ruleset is found by family and by code

A `LoadedRuleset` holds its rules in the order of C-2 of
[wio rules](../../README.md) and finds them by family and by code, and the
rulesets are returned by name.

#### Finding rules

- **Given** a ruleset `demo` that declares `ARC` and `PAY` and holds `ARC2`,
  `ARC10`, `ARC1`, `ARC01`, `ARC001` and `PAY1`, each with its own name, and a
  ruleset `acme` that declares `ARC` and holds `ARC1`.
- **When** the discovery runs.
- **Then** it returns `acme` and `demo` in that order, the rules of `demo` as
  `ARC001`, `ARC01`, `ARC1`, `ARC2`, `ARC10`, `PAY1`, `rules_of("ARC")` gives
  the first five, `rules_of("ZZZ")` gives none, `get("ARC2")` gives that rule
  and `get("ARC3")` gives none.

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
  code `ARC001`, two other rules with distinct codes and the name
  `keep-it-small`, and `ARC009`.
- **When** the discovery runs.
- **Then** it reports one error for the code that names both files, joined by
  `, `, and one for the name that names both files, and `demo` holds `ARC009`
  only.

#### The same code in two rulesets

- **Given** two rulesets that each declare `ARC` and hold `ARC001`.
- **When** the discovery runs.
- **Then** it reports no error and both rules are returned, because a qualified
  code is unique.

### **AC-5** A ruleset's name comes from its directory

A ruleset is named by its directory directly under `.agents/wio/rules/`, in the
form of a ruleset name, a lower-case letter followed by lower-case letters,
digits, `-` and `_`; hidden directories are ignored and a symbolic link is an
error.

#### The name of a ruleset

- **Given** the directories `demo`, `My_Rules` and `.cache`, and a symbolic link
  `linked` to a ruleset, each with a valid `ruleset.toml`.
- **When** the discovery runs.
- **Then** it returns `demo` only, reports one error for `My_Rules` that names
  the directory and says its name is not in the form of a ruleset name, reports
  one error for `linked` that says it must not be a symbolic link, and reads and
  reports nothing for `.cache`.

### **AC-6** The faults of directories and files are reported

A missing or broken manifest, a `ruleset.toml` below a ruleset's directory, a
stray rule file and a file that cannot be read are each one error that names its
place, and everything else is still returned.

#### Faults of rulesets

- **Given** a directory `bare` without a `ruleset.toml`, a ruleset `broken`
  whose `ruleset.toml` does not parse, a valid ruleset `outer` that has a
  subdirectory with its own `ruleset.toml`, a stray rule file, which is a marked
  rule file directly in `.agents/wio/rules/`, an unmarked `README.md` there, and
  a valid ruleset `good`.
- **When** the discovery runs.
- **Then** it reports one error for each fault, naming the directory or the
  file, and returns `outer` and `good` whole and neither `bare` nor `broken`;
  the unmarked file is ignored.

#### Faults of files

- **Given** a ruleset `demo` whose manifest declares `ARC`, with a rule file
  that is not valid UTF-8, a rule file whose read raises `OSError`, and a valid
  rule, and a ruleset `other` whose `ruleset.toml` is a symbolic link.
- **When** the discovery runs.
- **Then** it reports one error for each of the three faults, naming the file,
  raises nothing, and returns `demo` with the valid rule only.

### **AC-7** The rules directory is checked before it is walked

A `.agents/wio/rules` that is missing is no fault, and one that is a symbolic
link or not a directory is one error and is not walked.

#### The rules directory

- **Given** a repository with no `.agents/wio/rules`, one where it is a symbolic
  link, and one where it is a file.
- **When** the discovery runs on each.
- **Then** the first returns no ruleset and no diagnostic, and each of the
  others returns no ruleset and one error that names `.agents/wio/rules`.

#### A directory that cannot be listed

- **Given** a port whose `list_dir` raises `OSError` for `.agents/wio/rules`,
  and another whose `list_dir` raises it for one ruleset's directory beside a
  valid ruleset.
- **When** the discovery runs on each.
- **Then** the first returns no ruleset and one error that names
  `.agents/wio/rules`, and the second returns the valid ruleset and one error
  that names the directory, and nothing is raised.

### **AC-8** The diagnostics do not depend on the order of the listing

The diagnostics that the discovery returns are in the order of C-2 of
[wio rules](../../README.md), whatever the order in which the port lists the
files and directories.

#### Two listings

- **Given** a repository with a rule file whose block does not close, a rule of
  an undeclared family, a manifest that does not parse and a stray rule file,
  and a port that lists its entries in one order and then in the reverse.
- **When** the discovery runs with each.
- **Then** the rulesets and the diagnostics returned are equal, and the
  diagnostics are in the order of `sort_diagnostics`.

### **AC-9** A discovery with an error is refused, with a warning it is not

`refuse_on_errors` raises for a discovery that holds an error and returns for
one that holds a warning only, so that every command refuses alike.

#### An error and a warning

- **Given** a discovery with a rule whose block does not close and an unknown
  key in a manifest, and another with the unknown key only.
- **When** `refuse_on_errors` runs on each.
- **Then** the first raises a `DiagnosticsError` that carries the error and not
  the warning, and the second returns.

## Additional context

- A directory under `.agents/wio/rules/` without a `ruleset.toml`, and a ruleset
  whose name is not in the form of a ruleset name, are errors of
  `wio config check` already, which stops every command before the discovery
  runs, so those criteria reach the discovery by a call and not through the
  command line; the discovery reports them again for `wio rules check` to show,
  which is intended. `wio config check` accepts a symbolic link to a ruleset,
  because it follows links, so the discovery's error for one is the only report
  of it.
