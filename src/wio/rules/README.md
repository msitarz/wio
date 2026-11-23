# `wio.rules`

The component behind `wio rules`. So far it holds the reader of one rule file,
the reader of a ruleset's manifest and the discovery of the rulesets, which
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
