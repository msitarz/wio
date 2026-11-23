# `wio.rules`

The component behind `wio rules`. So far it holds the reader of one rule file,
which the discovery of rulesets, `wio rules check`, `list` and `show` build on.
[A rule file](../../../docs/concepts.md#a-rule-file) says what the file holds
and [Codes and families](../../../docs/concepts.md#codes-and-families) what its
code and name mean. Its terms are in the
[glossary](../../../GLOSSARY.md).

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
