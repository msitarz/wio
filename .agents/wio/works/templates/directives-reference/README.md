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
- `wio templates` tells that `directives` exists.

## Non-Goals

- Reading or checking any template, which `list` and `check` do.
- Documenting the grammar in prose, which the README of `wio.formats` does.
- Listing the directives that a particular template uses.

## Assumptions

- **A-1**: The directives leaf is delivered, so the table has an entry for each
  directive with its name, syntax, meaning and examples, in a fixed order.
- **A-2**: `wio.cli` can run a command without finding the repository or loading
  the config, as bare `wio config` does.

## Mechanisms

- The table of directives in `wio.formats`, which the command prints.
- `wio.cli`'s table of commands, which gains `directives` under `templates`.
- `Stdio` of `wio.io`, through which the output is written.

## Constraints

- **The table is the only source.** The command prints the table and adds no
  text about a directive of its own.
- **The order is the table's.** It is `required`, `items`, `pattern`, `inherit`,
  and the output has no timestamps.
- **The command reads nothing.** It reads no file, no config and no repository.
- **Nothing is imported before it is needed.** Without `--json` it imports no
  `json`, `tomllib`, `tomlkit` or Markdown parser.
- **Verification.** The human form is verified by AC-1, the JSON by AC-2, the
  independence of the repository by AC-3, the imports by AC-4, the command line
  by AC-5 and the documents by AC-6.

## Acceptance criteria

### **AC-1** The human form lists every directive with its details

`wio templates directives` prints each directive in the table's order as a name,
with its syntax, its meaning and each example indented under it, and exits 0.

#### The listing

- **Given** any working directory.
- **When** `wio templates directives` runs.
- **Then** it prints `required`, `items`, `pattern` and `inherit` in that order,
  each followed by an indented `Syntax:` line, an indented meaning and an
  indented `Example:` line for each of its examples, two for `pattern`, writes
  nothing to standard error and exits 0.

### **AC-2** `--json` prints the table as one array

`wio templates directives --json` prints one JSON array in the table's order,
each object with `name`, `syntax`, `description` and `examples`, where
`examples` is an array.

#### The array

- **Given** any working directory.
- **When** `wio templates directives --json` runs.
- **Then** the output parses as one array of four objects whose fields equal the
  table's, with two examples for `pattern`, and the exit code is 0.

### **AC-3** The command works outside a repository and with a broken config

The command prints the same output whether or not the working directory is in a
repository and whatever its config holds.

#### No repository and a bad config

- **Given** a directory that is not in a git repository, and a repository whose
  config has an error.
- **When** `wio templates directives` runs in each.
- **Then** both print the same output as in any other directory and exit 0.

### **AC-4** Without `--json` the command loads no parser or writer

`wio templates directives`, without `--json`, imports none of `json`, `tomllib`,
`tomlkit` and `markdown_it`.

#### A fresh interpreter

- **Given** a new Python process.
- **When** `main(["templates", "directives"], stdio)` of `wio.cli` runs in it
  and `sys.modules` is read.
- **Then** none of the four modules is there.

### **AC-5** The command line takes only `--json`

An argument other than `--json` is a usage mistake, and the help of
`wio templates` names `directives`.

#### The command line

- **Given** any working directory.
- **When** `wio templates directives extra` runs, and then `wio templates`.
- **Then** the first exits 2 with a usage message, and the help names
  `directives`.

### **AC-6** The documents describe the command

`docs/concepts.md` and `docs/v0.1-scope.md` say that `wio templates directives`
prints every directive with its syntax, meaning and examples, as an indented
list or as an array with `--json`, that it reads no file or config and so works
outside a repository, and that what it prints is the parser's own table.

## Additional context

- [Directives](../../../../../docs/concepts.md#directives) in the concepts
  describes the grammar the command prints.
- The [directives](../directives/README.md) leaf owns the table and the
  [discovery](../discovery/README.md) leaf wires `wio templates`.
