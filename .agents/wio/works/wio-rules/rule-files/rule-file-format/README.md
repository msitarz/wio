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
- The faults of a rule file are reported together as errors with their place,
  and its doubtful keys as warnings, without raising.
- A file that is not marked is not a rule and costs no diagnostic.

## Non-Goals

- Walking a directory, reading a file from disk and judging a rule against its
  ruleset, such as an undeclared family or a code that two rules share, which
  the discovery of `8zn10d` does.
- Judging the body, such as a Markdown heading in it, which `wio rules check`
  does.
- Writing a rule file, which `wio rules new` does.

## Assumptions

### A-1

A blank line is a line that is empty or holds only whitespace.

## Mechanisms

The names of the types and the functions below are provisional.

- **`Rule`** — a frozen dataclass in `wio.models.rule` with
  `ruleset: str`, `code: str`, `name: str`, `description: str | None`,
  `summary: str`, `body: str` and `path: PurePosixPath`, and the properties
  `family: str`, `number: int` and `qualified: str`; it replaces the stub `Rule`
  of `wio.models.rules`, whose stub keeps `Decision` and `Selection` and imports
  it.
- **`read_rule(ruleset: str, path: PurePosixPath, text: str) -> RuleReading`** —
  in `wio.rules`; a `RuleReading` holds `rule: Rule | None` and
  `diagnostics: tuple[Diagnostic, ...]`.
- **The block reader and `closest_key`** — `read_metadata_block` and
  `closest_key` of `wio.formats`, which read either block form and suggest the
  known key that a mistyped one is close to.
- **`Diagnostic`** — of `wio.models.diagnostics`, with the severity `error` or
  `warning`, a place and a message.

## Constraints

### C-1

`read_rule` does no input or output: it reads only the text it is given. Every
criterion below runs it on text alone.

## Acceptance criteria

### **AC-1** A marked file is read into a rule

A file whose metadata block holds a `code` and a `name` is read into a `Rule`
with the ruleset's name, the path, the code and its family and number, the
qualified code, the name, the description when there is one, the summary and the
body, and no diagnostic.

#### A rule with a description

- **Given** the text of `.agents/wio/rules/demo/ARC001-keep-it-small.md` whose
  block holds `code = "ARC001"`, `name = "keep-it-small"` and
  `description = "A rule is one instruction."`, followed by a blank line, the
  paragraph `State one instruction` and `in each rule.` on two lines, a blank
  line and the paragraph `Why: a long rule hides several decisions.`.
- **When** `read_rule` reads it as a rule of the ruleset `demo`.
- **Then** the rule is `demo.ARC001`, its family is `ARC`, its number is 1, its
  name is `keep-it-small`, its description is `A rule is one instruction.`, its
  summary is `State one instruction in each rule.`, its body is the two
  paragraphs as written, its path is the path given, and there is no
  diagnostic.

#### A rule without a description

- **Given** a block that holds only `code = "ARC002"` and `name = "other-rule"`.
- **When** `read_rule` reads it.
- **Then** the rule has no description.

### **AC-2** Either block form gives the same rule

A rule file whose metadata is `+++` front matter with `wio = 1` is read into the
same `Rule` as one with a `<!-- wio -->` block that holds the same keys and
body, read as the same ruleset at the same path.

#### Both forms

- **Given** two texts with the same keys and body, one with the comment block
  and one with `+++` front matter that holds `wio = 1`.
- **When** `read_rule` reads each as a rule of `demo` at the same path.
- **Then** the two rules are equal and neither has a diagnostic.

### **AC-3** The keys have a form

A `code` is a family of upper-case letters followed by digits, a `name` is
lower-case words of letters and digits joined by single hyphens and starting
with a letter, and a `description` is one line that is not blank; a key of
another form or type is an error.

#### Codes

- **Given** one file each with the code `ARC001`, `A1`, `ARC1000`, `arc001`,
  `ARC`, `001`, `ARC-001` and `ARC001a`.
- **When** `read_rule` reads each.
- **Then** the first three are read, and each of the others is one error that
  names the file and returns no rule.

#### Names

- **Given** one file each with the name `keep-it-small`, `keep-it-small2`, `x`,
  `Keep-It-Small`, `keep--it`, `keep-it-`, `-keep`, `2fast` and `keep_it`.
- **When** `read_rule` reads each.
- **Then** the first three are read, and each of the others is one error that
  names the file and returns no rule.

#### Descriptions and types

- **Given** one file each with a description of one line, a blank description, a
  description of two lines, a description that is a number, a `code` that is a
  number and a `name` that is a number.
- **When** `read_rule` reads each.
- **Then** the first is read, and each of the others is one error that names the
  file and returns no rule.

### **AC-4** The faults of a file are reported together

Every fault and every doubtful key of one file is reported, each with its place,
and an error leaves the rule out.

#### Missing keys

- **Given** a block with no `code`, a block with no `name`, and a block with
  neither.
- **When** `read_rule` reads each.
- **Then** the first two are one error each and the third is two errors, all
  naming the file, and none returns a rule.

#### An error and a warning

- **Given** a block with a `code` of `arc001` and a key `owner = "me"`.
- **When** `read_rule` reads it.
- **Then** it reports one error for the code and one warning for the key, and
  returns no rule.

#### A block that cannot be read

- **Given** a comment block that does not close, and a block whose TOML does not
  parse, whose fault is on line 3 of the file.
- **When** `read_rule` reads each.
- **Then** each is one error whose place is the file's path followed by `:` and
  the line of the fault, and no rule is returned.

### **AC-5** A doubtful key is a warning

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

### **AC-6** A file that is not marked is not a rule

A text with no metadata block on its first line, or with `+++` front matter that
has no `wio` key, is not a rule and gives no diagnostic, while front matter that
has a `wio` key the reader cannot accept is an error.

#### Not a rule

- **Given** a text with no block, a text whose block starts on its second line,
  and a text with `+++` front matter that has no `wio` key.
- **When** `read_rule` reads each.
- **Then** each returns no rule and no diagnostic.

#### A `wio` key that is wrong

- **Given** `+++` front matter with `wio = 2`, front matter with `wio = "1"`,
  and front matter with `wio = 1` that does not close.
- **When** `read_rule` reads each.
- **Then** each is one error and returns no rule.

### **AC-7** The summary and the body are cut from the text

The body is the text after the block without its leading and trailing blank
lines and without a final line ending, and the summary is the lines of the first
paragraph, each stripped, joined with single spaces.

#### Blank lines around the body

- **Given** a text whose block is followed by two blank lines, one of them with
  spaces, then the paragraph `Keep it small.` with two leading spaces and the
  paragraph `Why: it is easier to check.` separated by a blank line, then two
  blank lines.
- **When** `read_rule` reads it.
- **Then** the body is `Keep it small.`, a blank line and
  `Why: it is easier to check.` with no blank line before the first or after the
  last and the leading spaces kept, and the summary is `Keep it small.`.

#### A paragraph of several lines

- **Given** a first paragraph of three lines, the second indented by four
  spaces.
- **When** `read_rule` reads it.
- **Then** the summary joins the three stripped lines with single spaces.

#### No body

- **Given** a block followed by nothing but blank lines.
- **When** `read_rule` reads it.
- **Then** the rule's body and summary are empty and there is no diagnostic.

#### Windows line endings

- **Given** a text whose lines end in CRLF and whose first paragraph spans two
  lines.
- **When** `read_rule` reads it.
- **Then** the summary joins the two lines with one space and holds no carriage
  return, and the body keeps its CRLF line endings between its lines.

### **AC-8** A rule is a value

Two rules read from the same text, ruleset and path are equal and have the same
hash, rules that differ in any field are not equal, and no field can be
assigned, so a rule can be a key of a mapping.

#### Equal, unequal and frozen

- **Given** the same text read twice, and the same text read with another code.
- **When** the rules are compared, used as keys of one mapping, and a field of
  one is assigned.
- **Then** the first two are equal with one hash and share one key, the third is
  a different key, and the assignment raises.

## Additional context

- `wio.rules` is a package with a docstring only today and `wio.models.rule` is
  new, so the delivery adds the module and the code, makes `wio.models.rules`
  import `Rule` from it, and changes `tach.toml` for the tests.
- The place of a missing-key error and of an unknown-key warning is the file's
  path without a line, as C-6 of [wio rules](../../README.md) says for a fault
  that has none.
