# `wio.rules`

The component behind `wio rules`. So far it holds the reader of one rule file,
the reader of a ruleset's manifest, the discovery of the rulesets, the
expansion of rule presets and the inputs that the selection shares, which
`wio rules check`, `list` and `show` build on.
[A rule file](../../../docs/concepts.md#a-rule-file) says what the file holds,
[Codes and families](../../../docs/concepts.md#codes-and-families) what its
code and name mean and
[Rulesets on disk](../../../docs/concepts.md#rulesets-on-disk) what a ruleset
is. Its terms are in the [glossary](../../../GLOSSARY.md).

## Reading a rule file

[`read_rule`](reading.py) turns the text of one rule file into a
[`Rule`](../models/rule.py), and its docstring says what it takes and returns.
Its [tests](../../../tests/unit/rules/test_reading.py) say how each case reads.

- **It reads text and does no input or output.** The caller finds the file,
  reads it and names its ruleset, so the walk of a directory and the judging of
  a rule against its ruleset, such as a family the manifest does not declare or
  a code that two rules share, are not here. A reader of one text is easy to run
  on every case, and its places are the same wherever the file came from.
- **A file reports every fault at once.** Each missing key and each key of the
  wrong form or type is its own error, so an author fixes the file in one turn,
  and an error leaves the rule out because a rule with a bad code could not be
  selected or shown safely. It never raises for a fault of the text.
- **A doubtful key is a warning and keeps the rule.** An unknown key is most
  likely a typo, so the warning suggests the known key it is close to, but a key
  that nothing reads cannot make the rule wrong.
- **A file that is not marked is not a rule and costs nothing.** A Markdown file
  next to the rules, such as a README, is left alone, while a block that claims
  to be wio's and cannot be read is an error, as for a template or a contract.
  Either metadata block form is accepted and reads to the same rule.
- **The place of a fault is the file's path.** It is followed by `:<line>` only
  when the fault has a line, which is the fault of a block that cannot be read.
  A missing key, a key of the wrong form and an unknown key have no line, so a
  person looks in the block, which is the first lines of the file.
- **The body is what the file says, trimmed.** Leading and trailing blank lines
  go, a line of whitespace counts as blank, and the final line ending goes,
  while the indentation and the line endings inside stay as written, because a
  bundle shows the body as it is. `body_line` says where the body starts, so a
  later check of the body can name its line.
- **The summary is the first paragraph on one line.** Its lines are stripped and
  joined with single spaces, so a listing shows a rule on one line whatever the
  line endings of the file are.
- **The name has a form of its own.** Hyphenated lower-case words starting with
  a letter keep a rule's file name, `<code>-<name>.md`, one readable token. The
  form is held once, here, and the code form is that of
  [`wio.formats`](../formats/README.md#the-grammar-of-a-reference-and-the-wording-of-messages).
- **A rule is a value.** It is frozen and hashable, so it can be the key of a
  selection, and two rules read from the same text, ruleset and path are equal.

## Reading a manifest

[`read_manifest`](manifest.py) turns the text of one `ruleset.toml` into a
[`Manifest`](../models/rule.py), on the same terms as `read_rule`: text in, no
input or output, every fault of the text at once, and no raising. Its
[tests](../../../tests/unit/rules/test_manifest.py) say how each case reads.

- **A fault has a key path.** A manifest has no lines to point at, except for
  TOML that does not parse, so a fault is the file followed by `#` and the key
  path, such as `#rule_presets.x.rules_include[0]`. A person finds the key in a
  file of a few lines, and the same text names the key in a message.
- **An empty manifest is a manifest.** A ruleset can be started before its first
  rule, so nothing is required of it.
- **The families and the rule presets keep the order written,** so a listing
  shows them as the author arranged them.
- **A rule preset has the shape of the config's.** One type serves both, so the
  forms of a name and of a list are not decided twice. Whether the entries of a
  preset name a family or a code that exists is not judged here, because that
  needs the rule files.
- **An unknown key is a warning that suggests the key it is close to,** as for a
  rule file, and the manifest is still returned.

## Discovering the rulesets

[`discover`](discovery.py) walks `.agents/wio/rules` through the `FileSystem`
port and returns the rulesets as [`LoadedRuleset`](../models/rule.py)s, each
with its manifest and its rules, and every fault it met. Its docstring says
where each diagnostic lies, and its
[tests](../../../tests/unit/rules/test_discovery.py) say how each case reads.

- **A fault is reported and the rest is still read.** A ruleset whose directory,
  manifest or name is at fault is left out, a ruleset whose rules are at fault
  loses those rules, and nothing is raised for a file, so `wio rules check` can
  show every fault of a repository in one run.
- **The result does not depend on the order of the listing.** The rulesets are
  sorted by name, the rules by family, then the number of the code, then the
  text of the code, and the diagnostics by `sort_diagnostics`, so the same files
  give the same bytes on any file system.
- **A ruleset is named by its directory.** A name of the wrong form, a symbolic
  link and a hidden directory are not rulesets, and a link is an error because
  the walk follows none, so a ruleset copied in by a link would otherwise be
  silently empty. A directory that cannot be listed is one error at the
  directory.
- **The discovery repeats what `wio config check` reports, on purpose.** A
  directory without a `ruleset.toml` and a ruleset name of the wrong form are
  errors of `wio config check` already, which stops every other command before
  the discovery runs, so only a call of the discovery reaches them. `wio rules
  check` shows them again with the other faults of the rules. `wio config check`
  follows symbolic links and accepts a link to a ruleset, so the error of the
  discovery is the only report of one. The checks are not redundant, and
  removing them from the discovery loses a report.
- **A rule is judged against its own ruleset only.** A family its manifest does
  not declare, a code or a name that two rules share, are errors that leave the
  rules out, while the same code in two rulesets is no fault, because a
  qualified code is unique. A name is unique as well as a code, as the scope of
  v0.1 says.
- **A rule file outside a ruleset and a manifest below one are errors.** They
  would be skipped, and a skipped file is a rule that nobody gets. An unmarked
  Markdown file in the rules directory, such as a README, is ignored, as in any
  other directory of rules.
- **One function refuses a discovery.** `refuse_on_errors` raises for the errors
  of a discovery and not for its warnings, so every command that must not work
  from a broken ruleset refuses alike and none decides for itself.
- **The rules directory is judged before it is walked.** It is missing without
  fault, and a symbolic link or a file there is one error and is not entered,
  as for the templates and the Works.

## Expanding rule presets

[`expand`](expansion.py) turns a list of includes and excludes into the rules it
selects, and every layer of the selection is built on it. It works on values:
the rulesets, their aliases and the config's rule presets arrive as a
[`RuleCatalog`](expansion.py), so it reads no file. Its docstring and
[tests](../../../tests/unit/rules/test_expansion.py) say what each case returns,
and [Rule presets](../../../docs/concepts.md#rule-presets) says what a rule
preset is.

- **A reference is read in the scope it is written in.** In the config a bare
  name is a rule preset of the config, and in a manifest it is a family, a code
  or a rule preset of that ruleset. So the same text can mean two things, and
  the scope is a value that the caller gives. A bare upper-case name stays
  malformed in the config, as `wio config check` judges it, because the grammar
  is the one that `wio.formats` shares with it.
- **An exclude reaches only its own level.** A rule preset resolves before
  anything uses it, so an exclude inside it cannot remove what an outer rule
  preset includes on its own. What a nested rule preset removed stays in
  `removed`, so `--explain` can say that a rule was taken out there even when an
  outer entry brought it back.
- **Every rule carries the routes by which it was reached.** A route is the
  canonical references from the outermost rule preset to the entry that named
  the rule, and a rule reached twice has both, sorted. The route is what lets
  `--explain` answer where a rule came from, and it never shows an alias, so one
  ruleset has one spelling in every output. A `Route` is in
  [`wio.models`](../models/rules.py), because a `Decision` holds routes and a
  model may not import a component.
- **What cannot be expanded is a problem and selects nothing.** An unknown name,
  a malformed reference, a qualified name inside a manifest and a cycle each
  become a `Problem` that names the entry and the rule presets it was found in,
  and the other entries are still expanded. Expanding never raises, because
  `wio rules check` has to show every fault at once, and a manifest is text that
  anyone may write.
- **A family that is declared and holds no rule is not a problem.** A ruleset
  can be started before its first rule, and a preset that includes the family
  keeps working once the rules arrive.
- **The rulesets that the includes name are returned apart from the rules.** A
  root reaches a ruleset by the rules it selects, but an exclude can leave none
  of them, and the ruleset is still the one the author meant, so the
  expansion names it. An exclude and an entry that names nothing name no
  ruleset.
- **The result does not depend on the order of the inputs.** The rules are
  sorted by ruleset, family, number and code text, the routes of a rule are
  sorted, and the problems are sorted by route, reference and kind, so the same
  files give the same bytes.
- **Nested rule presets are expanded from a list and not by recursion.** The
  depth of a chain is limited by memory and never by the recursion limit, so a
  long chain of rule presets does not raise.
- **The cost grows with the paths through nested rule presets.** A rule keeps
  every route, so a rule preset that two others include is expanded once for
  each, and a diamond of presets takes time and memory that grow exponentially
  with its depth, even when it selects nothing. A repository's own rule presets
  are shallow, so this has not been bounded; a rule preset that is expanded by
  value, once, with its routes rebased, would remove the cost.

## The inputs of the selection

[`inputs.py`](inputs.py) holds what every consumer of the selection would
otherwise build for itself: the rulesets of a discovery by canonical name
(`ruleset_map`), the [`RuleCatalog`](expansion.py) that `expand` resolves its
references in (`build_rule_catalog`), the resolution of a ruleset's name or
alias (`resolve_ruleset`), and the labels and the text of the chain that says
where a rule came from (`layer_label`, `chain_labels`, `chain_text`). Their
docstrings say what each takes and returns, and their
[tests](../../../tests/unit/rules/test_inputs.py) say how each case reads.

- **Each shape is built in one place.** The layers, the rules selected anywhere,
  the checks and the commands all need the same catalog and the same chain, and
  a second builder could differ from the first in an alias or a label, so that
  `list --explain` and `new` would print different text for one rule. The one
  place that knows what a catalog is made of is this module and `expand`, so a
  change to the catalog is made there. `expand` resolves a ruleset through
  `resolve_ruleset` and keeps no resolution of its own.
- **A name wins over an alias.** A ruleset is named by its directory, and the
  config keeps an alias from naming another ruleset, so the order only matters
  to a config that is not valid; there the directory name is the one that cannot
  change under an edit of the config.
- **An alias is kept for a ruleset whose files were not read, and names
  nothing.** The catalog holds every alias of the config, because it is the
  config's, but resolves one only when its ruleset is in the catalog, so a
  command can tell a ruleset it does not know from one it could not read, by
  looking at the config, and neither is expanded as if its rules were there.
- **The rulesets and the labels are in a fixed order and a fixed text.** The
  rulesets are keyed in the order of ruleset name whatever the order of the
  discovery, and a layer's label and a chain are the text that the text and the
  JSON of `list --explain` and `new` both print, so the two cannot disagree. A
  listing of references has no layer and so no label; its chain is the route
  alone.
- **The two modules import each other lazily.** `inputs` builds a `RuleCatalog`
  and `expansion` resolves a ruleset, so either would need the other at import
  time, and both use lazy imports to break the cycle. Importing `wio.rules`
  loads neither.
