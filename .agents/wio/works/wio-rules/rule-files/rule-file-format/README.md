<!-- wio
id = "ht39xt"
template = "feature.leaf"
roots = ["wio"]
depends_on = []
-->

# Rule file format

## Purpose

A rule is a Markdown file that nothing reads yet, so its code, its name and its
body cannot be used to select, check, list or show it.

## Goals

- A marked file is read into an immutable `Rule` with its ruleset, code, name,
  optional description, summary, body and path, in either metadata block form.
- A fault of a rule file is reported as an error with its place, and a doubtful
  key as a warning, without raising.
- A file that is not marked is not a rule and costs no diagnostic.

## Non-Goals

- Walking a directory, reading a file and judging a rule against its ruleset,
  such as an undeclared family or a code that two rules share, which the
  discovery of `8zn10d` does.
- Judging the body, such as a Markdown heading in it, which `wio rules check`
  does.
- Writing a rule file, which `wio rules new` does.

## Assumptions

### A-1

A blank line is a line that is empty or holds only whitespace.

## Mechanisms

The names of the types and the functions below are provisional.

- **`Rule`** — in `wio.models.rule` as a `.py`, which replaces the stub in
  `wio.models.rules`, whose stub keeps `Decision` and `Selection` and imports
  `Rule`; a frozen dataclass with the ruleset's name, the code, the name, the
  description or none, the summary, the body and the path relative to the
  repository root, and the family and the number of the code and the qualified
  code as properties.
- **`read_rule(ruleset: str, path: PurePosixPath, text: str) -> RuleReading`** —
  in `wio.rules`, reads the text of one file and does no input or output; a
  `RuleReading` holds the `Rule`, or none when the text is not a rule or has an
  error, and the diagnostics.
- **The block reader and `closest_key`** — `read_metadata_block` and
  `closest_key` of `wio.formats`, which read either block form and suggest the
  known key a mistyped one is close to.
- **`Diagnostic`** — of `wio.models.diagnostics`, with the severity `error` or
  `warning`, a place and a message.

## Constraints

### C-1

A place is the path of the file written with `/`, followed by `:<line>` for a
fault of the block that has a line, as `wio.templates` writes it. AC-3 verifies
it.

## Acceptance criteria

### **AC-1** A marked file is read into a rule

A file whose metadata block holds a `code` and a `name` is read into a `Rule`
with the ruleset's name, the path, the code and its family and number, the
qualified code, the name, the description when there is one, the summary and the
body, and no diagnostic.

#### A rule with a description

- **Given** the text of `.agents/wio/rules/demo/ARC001-keep-it-small.md` whose
  block holds `code = "ARC001"`, `name = "keep-it-small"` and
  `description = "Keep each rule to one instruction."`, followed by a blank
  line, the paragraph `Keep each rule` and `to one instruction.` on two lines, a
  blank line and the paragraph `Why: a long rule hides several decisions.`.
- **When** `read_rule` reads it as a rule of the ruleset `demo`.
- **Then** the rule is `demo.ARC001`, its family is `ARC`, its number is 1, its
  name is `keep-it-small`, its description is
  `Keep each rule to one instruction.`, its summary is
  `Keep each rule to one instruction.`, its body is the two paragraphs as
  written, its path is the path given, and there is no diagnostic.

#### A rule without a description

- **Given** a block that holds only `code = "ARC002"` and `name = "other-rule"`.
- **When** `read_rule` reads it.
- **Then** the rule has no description.

### **AC-2** Either block form gives the same rule

A rule file whose metadata is `+++` front matter with `wio = 1` is read into the
same `Rule` as one with a `<!-- wio -->` block that holds the same keys and
body.

#### Both forms

- **Given** two texts with the same keys and body, one with the comment block
  and one with `+++` front matter that holds `wio = 1`.
- **When** `read_rule` reads each.
- **Then** the two rules are equal and neither has a diagnostic.

### **AC-3** A fault of a rule file is an error with its place

Each fault of the block or of its keys is an error that names the place and
leaves the rule out, and all the faults of one file are reported together.

#### Faults of the keys

- **Given** a block with no `code`, a block with no `name`, a `code` of
  `arc001`, a `code` of `ARC`, a `name` of `Keep It Small`, a `description` that
  is a number, a `description` of two lines and a `description` that is blank,
  each in a file of its own.
- **When** `read_rule` reads each.
- **Then** each is one error that names the file, and none returns a rule.

#### More than one fault

- **Given** a block with no `code` and a `name` of `Keep It Small`.
- **When** `read_rule` reads it.
- **Then** it reports two errors, one for each key, both naming the file.

#### A block that cannot be read

- **Given** a comment block that does not close, and a block whose TOML does not
  parse, whose fault is on line 3.
- **When** `read_rule` reads each.
- **Then** each is one error whose place is the file's path followed by `:` and
  the line of the fault, and no rule is returned.

### **AC-4** A doubtful key is a warning

A key that the block does not know is a warning that names the key and the known
key it is close to, and the rule is still returned.

#### A mistyped key

- **Given** a block with `code`, `name` and `descriptions = "Keep it small."`.
- **When** `read_rule` reads it.
- **Then** it reports one warning that names `descriptions` and suggests
  `description`, and returns the rule without a description.

#### A key that is close to nothing

- **Given** a block with `code`, `name` and `owner = "me"`.
- **When** `read_rule` reads it.
- **Then** it reports one warning that names `owner` and suggests no key, and
  returns the rule.

### **AC-5** A file that is not marked is not a rule

A text with no metadata block on its first line, or with `+++` front matter that
has no `wio = 1`, is not a rule and gives no diagnostic.

#### Not a rule

- **Given** a text with no block, a text whose block starts on its second line,
  and a text with `+++` front matter that has no `wio = 1`.
- **When** `read_rule` reads each.
- **Then** each returns no rule and no diagnostic.

#### Front matter that is wio's but broken

- **Given** `+++` front matter that holds `wio = 1` and does not close.
- **When** `read_rule` reads it.
- **Then** it reports one error and returns no rule.

### **AC-6** The summary and the body are cut from the text

The body is the text after the block without its leading and trailing blank
lines, and the summary is the first paragraph of the body with its line breaks
turned into single spaces.

#### Blank lines around the body

- **Given** a text whose block is followed by two blank lines, one of them with
  spaces, then the paragraphs `Keep it small.` and `Why: it is easier to check.`
  separated by a blank line, then two blank lines.
- **When** `read_rule` reads it.
- **Then** the body is the two paragraphs as written, with no blank line before
  the first or after the last and the blank line between them kept, and the
  summary is `Keep it small.`.

#### No body

- **Given** a block followed by nothing but blank lines.
- **When** `read_rule` reads it.
- **Then** the rule's body and summary are empty and there is no diagnostic.

#### Windows line endings

- **Given** a text whose lines end in CRLF and whose first paragraph spans two
  lines.
- **When** `read_rule` reads it.
- **Then** the summary joins the two lines with one space and holds no carriage
  return, and the body keeps its CRLF line endings inside.

### **AC-7** A rule is a value

Two rules read from the same text, ruleset and path are equal and have the same
hash, and rules that differ in any field are not equal, so a rule can be a key
of a mapping.

#### Equal and unequal rules

- **Given** the same text read twice, and the same text read with another code.
- **When** the rules are compared and used as keys of one mapping.
- **Then** the first two are equal with one hash and share one key, and the
  third is a different key.

## Additional context

- `wio.rules` and `wio.models.rule` are new modules, and `tach.toml` and the
  type stubs change with them; `uv run tach check` verifies the dependency
  direction that the inherited constraints name.
