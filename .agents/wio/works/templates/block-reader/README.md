<!-- wio
id = "p8vtzx"
template = "feature.leaf"
roots = ["wio", "repo"]
depends_on = []
-->

# Reading the metadata block

## Purpose

Every file that carries wio metadata needs one reader that finds the metadata
block and splits it from the body, so that no command has its own idea of where
a block starts and ends.

## Goals

- A text with a metadata block gives the block's form, its version, its data and
  the body that follows it, and a text without one gives nothing.
- Both forms of the block give the same data, and the form is kept so a writer
  can restore it.
- A block that claims to be wio's but cannot be read is an error that says
  where.
- The marker is checked, so a format that wio does not know is refused and not
  misread.

## Glossary

- **Body start line**: the line of the text, counted from 1, on which the body
  begins, which is the line after the closing delimiter when nothing follows the
  delimiter on its own line.

## Non-Goals

- Reading a file, finding files or naming a file in an error, which the caller
  does.
- Judging the keys of the data, which belong to the template and to the
  contract.
- Writing a block, which the skeleton leaf does.
- Finding the sections of the body or their directives.

## Assumptions

- **A-1**: `decode_toml` and `TomlSyntaxError` stay as they are, so a TOML error
  carries its line and column within the text it was given.
- **A-2**: Callers decode a file as UTF-8 and pass the text, which may still
  start with the byte-order mark U+FEFF.

## Mechanisms

- A function in `wio.formats` that takes the text of a file, with a name and a
  signature that the architecture stage fixes.
- `decode_toml` of `wio.formats`, which decodes the TOML of a block.
- A plain immutable type in `wio.models` for the block, whose fields are the
  form, the version, the data and the body with its start line, provisional for
  the architecture stage to fix.
- An error in `wio.formats.errors` that extends `WioError`, for a block that
  cannot be read.

## Constraints

- **The reader touches no file.** It takes text and returns data or raises,
  as every codec of `wio.formats` does.
- **A text with no block never loads `tomllib`.** The decoder loads it on its
  first call, so reading an unmarked file costs no import of it.
- **Lines count from 1 in the text.** An error names the line of the text that
  the reader was given, and the caller names the file.
- **Verification.** The returned parts are verified by AC-1 and AC-2, the
  silence for an unmarked text by AC-3, the errors and their lines by AC-4, the
  line endings by AC-5 and the imports by AC-6.

## Acceptance criteria

### **AC-1** Both forms give their form, version, data and body

A text that opens with a comment block or with `+++` front matter on its first
line is read into its form, its version, its data and its body with the body's
start line.

#### The comment form

- **Given** the text `<!-- wio`, `id = "k3m9xq"`, `-->`, an empty line and
  `# Title`, each on its own line.
- **When** the reader reads it.
- **Then** the form is the comment form, the version is 1, the data is
  `{"id": "k3m9xq"}`, and the body is the empty line and `# Title`, starting on
  line 4.

#### The `+++` form

- **Given** the text `+++`, `wio = 1`, `id = "k3m9xq"`, `+++`, an empty line and
  `# Title`, each on its own line.
- **When** the reader reads it.
- **Then** the form is the `+++` form, the version is 1, the data is
  `{"id": "k3m9xq"}` with no `wio` key, and the body starts on line 5.

#### A comment that closes at the first `-->`

- **Given** the text `<!-- wio`, `s = "a-->b"`, `-->`, each on its own line.
- **When** the reader reads it.
- **Then** the block ends at the first `-->`, so its TOML is `s = "a`, and the
  reader raises an error that names line 2.

### **AC-2** The marker is optional in the comment form and checked everywhere

The marker is the integer `1`. It may be left out of a comment block, where
the version is then 1, and it is required in `+++` front matter, and no other
value is accepted.

#### An absent marker

- **Given** a comment block with no `wio` key, and another with `wio = 1`.
- **When** the reader reads each.
- **Then** both give version 1 and data with no `wio` key.

#### A marker that is not 1

- **Given** a comment block and a `+++` block whose `wio` is `2`, `true`, `"1"`
  or `1.0`, in turn.
- **When** the reader reads each.
- **Then** it raises an error that says the marker must be the integer 1.

### **AC-3** A text that is not marked gives nothing

A text that has no block on its first line, or whose `+++` front matter is not
wio's, gives nothing and no error.

#### Texts without a block

- **Given** a text with no block, a text whose first line is blank and whose
  second line opens a comment block, a text that quotes `<!-- wio` after its
  first line, a text that starts `<!-- wiox`, and `+++` front matter with no
  `wio =` in it.
- **When** the reader reads each.
- **Then** each gives nothing and raises no error.

### **AC-4** A block that cannot be read is an error with its line

A comment block that does not close or whose TOML does not parse, and `+++`
front matter that does not close or parse and contains `wio =`, raise an error
that names the line.

#### A comment block that is wrong

- **Given** a comment block that never closes, and a comment block whose third
  line is not valid TOML.
- **When** the reader reads each.
- **Then** the first raises an error that says the block does not close and
  names line 1, and the second raises an error that names line 3.

#### `+++` front matter that is wrong

- **Given** `+++` front matter that contains `wio = 1` and never closes, and
  `+++` front matter with no `wio =` that never closes.
- **When** the reader reads each.
- **Then** the first raises an error that names line 1, and the second gives
  nothing.

### **AC-5** Line endings and the byte-order mark do not change the result

A text with CRLF line endings, or with a leading byte-order mark, gives the same
data and the same body start line as the same text with LF endings and no mark.

#### The same text three ways

- **Given** one block of each form written with LF, with CRLF and with a leading
  U+FEFF.
- **When** the reader reads each.
- **Then** the form, the version, the data and the body start line are equal
  across the three.

### **AC-6** Reading an unmarked text loads no TOML decoder

Reading a text that has no block does not import `tomllib`.

#### A fresh interpreter

- **Given** a new Python process.
- **When** the reader reads a text with no block and `sys.modules` is read.
- **Then** `tomllib` is not there.

### **AC-7** The README of `wio.formats` describes the reader

`src/wio/formats/README.md` states that the reader of the metadata block lives
in `wio.formats`, and no longer says that reading the block belongs to the
contracts Work. It states the closing delimiters, the marker rules, what the
reader returns and which cases give nothing and which raise.

## Additional context

- [Metadata forms](../../../../../docs/concepts.md#metadata-forms) says what the
  two forms and the marker are, and
  [Which files are Works](../../../../../docs/concepts.md#which-files-are-works)
  says which files carry a block.
- [The `wio.formats` README](../../../../../src/wio/formats/README.md) holds the
  decoder this reader builds on.
- The [skeleton](../skeleton/README.md) and [discovery](../discovery/README.md)
  leaves read through it.
