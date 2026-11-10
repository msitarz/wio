<!-- wio
id = "whhw53"
template = "feature.leaf"
roots = ["wio", "repo"]
depends_on = ["1n1p8j", "776g94"]
-->

# Printing the directive grammar

## Purpose

A person or an agent that writes a template must be able to learn which
directives exist and how to write them without leaving the command line.

## Goals

- `wio templates directives` prints every directive with its syntax, its meaning
  and its examples, for a person.
- `--json` prints the same as plain data for a program.
- The command works anywhere, in a repository or not, and needs no valid config.
- What it prints is the parser's own table, so it cannot say anything else than
  the parser accepts.
- The human form also says how several directives are written in one comment on
  a heading, with an example, so a reader sees the list form of the grammar
  without searching.
- `wio templates` tells that `directives` exists.

## Non-Goals

- Reading or checking any template, which `list` and `check` do.
- Documenting the grammar in prose, which the README of `wio.formats` does.
- Listing the directives that a particular template uses.

## Assumptions

- **A-1**: The [directives](../directives/README.md) leaf is delivered and its
  AC-7 holds, so the table has an entry for each directive in a fixed order.
- **A-2**: The parser of that leaf reads several directives in one comment,
  separated by commas, so an example of the list form parses into the
  directives it combines.

## Mechanisms

- The table of directives in `wio.formats`, which the command prints, and
  beside it a rule of the same shape that says how directives are combined in
  one comment, with a title, its syntax, its meaning and an example.
- `wio.cli`'s table of commands, which gains `directives` under `templates`.
- `Stdio` of `wio.io`, through which the output is written.

## Constraints

- **The table and the rule of the list are the only sources.** The command
  prints their fields as they are and adds no text about a directive of its own.
- **The order is the table's fixed order, and the rule comes last.** The command
  does not sort or filter.
- **The command reads nothing of the project.** It reads no file of it, no
  config and no repository.
- **It loads no parser or writer.** Without `--json` it imports none of `json`,
  `tomllib`, `tomlkit` or a Markdown parser, so that it starts fast.
- **Verification.** The human form and its fidelity to the table and the rule
  are verified by AC-1, the JSON by AC-2, the independence of the project by
  AC-3, the imports by AC-4, the command line by AC-5, the documents by AC-6 and
  the same output on every run by AC-7.

## Acceptance criteria

### **AC-1** The human form prints the table and the rule of the list

`wio templates directives` prints each entry of the table in the table's order,
the name on a line and under it, indented by two spaces, a `Syntax:` line, the
meaning and an `Example:` line for each example, and then one block of the same
shape for the rule of the list, with the title `several directives` instead of a
name; one empty line separates the blocks, and every field is the table's or the
rule's, character for character, a meaning of several lines having each of its
lines indented by two spaces.

#### The listing

- **Given** any working directory, the table and the rule of the list.
- **When** `wio templates directives` runs.
- **Then** it prints exactly one block for each entry of the table in its
  order and then one block for the rule of the list, each as in this shape,
  writes nothing to standard error and exits 0:

  ```text
  required
    Syntax: <the entry's syntax>
    <the entry's meaning>
    Example: <the entry's example heading>
  ```

  with one `Example:` line for each example heading, each line of the meaning
  printed as it is, an empty line between blocks and none after the last; the
  last block starts with `several directives`, its syntax shows directives
  separated by commas inside one comment, and its example is a whole heading
  line with three directives separated by commas.

### **AC-2** `--json` prints the table as one array

`wio templates directives --json` prints one JSON array in the table's order,
each object with `name`, `syntax`, `meaning` and `examples`, where `examples` is
an array, and every value is the table's.

#### The array

- **Given** any working directory and the table.
- **When** `wio templates directives --json` runs.
- **Then** the output parses as one array with one object for each entry of the
  table, in its order, whose four fields equal the entry's, and the exit code is
  0. The rule of the list is not part of the array.

### **AC-3** The command works outside a repository and with a broken config

The command prints the same output whether or not the working directory is in a
repository and whatever its config holds, which shows that its output does not
depend on the project.

#### No repository and a bad config

- **Given** a directory that is not in a git repository, a repository whose
  config has an error, a repository with no config file and a repository whose
  templates directory is unreadable.
- **When** `wio templates directives` runs in each.
- **Then** all four print the same output as in any other directory and exit 0.

### **AC-4** Without `--json` the command loads no parser or writer

`wio templates directives`, without `--json`, imports none of `json`, `tomllib`,
`tomlkit` and `markdown_it`.

#### A fresh interpreter

- **Given** a new Python process.
- **When** `main(["templates", "directives"], stdio)` of `wio.cli` runs in it
  and `sys.modules` is read.
- **Then** none of the four modules is there.

### **AC-5** The command line takes only `--json`

An argument other than `--json` is a usage mistake, the help of
`wio templates` names `directives`, and the help of `wio templates directives`
says that directives are combined in one comment, separated by commas.

#### The command line

- **Given** any working directory.
- **When** `wio templates directives extra` runs, then `wio templates`, and then
  `wio templates directives --help`.
- **Then** the first exits 2 with a usage message, the help of `wio templates`
  names `directives`, and the last says that directives are combined in one
  comment, separated by commas.

### **AC-6** The documents describe the command

`docs/concepts.md` and `docs/v0.1-scope.md` say that `wio templates directives`
prints every directive with its syntax, meaning and examples, as an indented
list or as an array with `--json`, that the list also says how several
directives are combined in one comment, that it reads no file or config and so
works outside a repository, and that what it prints is the parser's own table.

### **AC-7** The output is the same on every run

Each form of the command prints the same text every time.

#### The same output twice

- **Given** any working directory.
- **When** `wio templates directives` and `wio templates directives --json` each
  run twice.
- **Then** the two outputs of each command are identical.

## Additional context

- [Directives](../../../../../docs/concepts.md#directives) in the concepts
  describes the grammar the command prints.
- The [directives](../directives/README.md) leaf owns the table and the
  [discovery](../discovery/README.md) leaf wires `wio templates`.
