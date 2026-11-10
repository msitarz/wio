<!-- wio
id = "776g94"
template = "feature.leaf"
roots = ["wio", "repo"]
depends_on = ["p8vtzx"]
-->

# Finding and listing templates

## Purpose

People and agents must be able to find the templates of a project and see which
one each kind starts from, and every command that reads a template needs the
same way of finding and building them.

## Goals

- The templates of a project are found in its templates directory, each named by
  its file, with its kind, shape and description.
- The entry template of each kind is marked.
- A problem in finding or reading a template is reported as a diagnostic, and
  the commands that only read templates refuse to run on one.
- `wio templates list` shows the templates grouped by kind for a person and as
  plain data for a program, and can be limited to one kind.
- A template is named by its file, and its `name` key is gone.
- `wio templates` tells what the component offers.

## Non-Goals

- Judging a template's keys, directives, actions or kinds beyond what is needed
  to build it, which `wio templates check` does.
- Printing a template, which the show leaf does.
- Finding Works, which the contracts Work does.

## Assumptions

- **A-1**: The `FileSystem` port can list a directory, read a text and say
  whether a path is a directory or a file, and gains what the walk needs beyond
  that, which is to tell a symbolic link.
- **A-2**: The shape of `[templates]` is already checked by `wio config check`,
  so the component can rely on a normalized `dir` and on kinds that map to
  non-empty names.

## Mechanisms

- A component in `wio.templates` that walks the templates directory and builds a
  `Template` for each marked file, which returns the templates and the
  diagnostics it found.
- The block reader of `wio.formats`, which reads each file's metadata block.
- `Diagnostic` of `wio.models`, which carries each problem.
- The `FileSystem` port of `wio.io` and the `Settings` port of `wio.ports`.
- `wio.cli`'s table of commands, which gains `templates` with `list`.
- A plain immutable type `Template` in `wio.models`, with the name, the kind,
  the shape, the description and the path, provisional for the architecture
  stage to fix.

## Constraints

- **The walk is the Works directory's.** It reads the files whose names end in
  `.md`, matched with their case, skips directories below the templates
  directory whose names start with `.`, follows no symbolic link, and takes a
  file as a template when its metadata block starts on its first line; any other
  file is ignored.
- **A template is named by its file.** The name is the file's name without
  `.md`, and two files with one name are an error that names both.
- **A missing default directory holds no templates.** A `[templates] dir` that
  is set and missing, is not a directory or is a symbolic link is an error.
- **Output is deterministic.** Kinds and templates are sorted by name, and the
  output has no timestamps.
- **Nothing is imported before it is needed.** `list` without `--json` imports
  neither `json`, `tomlkit` nor a Markdown parser.
- **Verification.** The walk is verified by AC-1, the fields by AC-2, the
  problems by AC-3, the help by AC-4, the output by AC-5, the refusal by AC-6,
  the repository's templates by AC-7 and the imports of `list` by the parent's
  AC-2.

## Acceptance criteria

### **AC-1** The walk finds the marked files and names them by their file

The component returns a template for each marked `.md` file under the templates
directory, named by the file's name without `.md`, and nothing else.

#### What is found and what is not

- **Given** a templates directory holding `feature.leaf.md` with a metadata
  block, `notes.md` with none, `sub/feature.parent.md` with one, `.hidden/x.md`
  with one, `Upper.MD` with one, and a symbolic link `link.md` to a template.
- **When** the templates are found.
- **Then** they are `feature.leaf` and `feature.parent`, and the other four
  files are not templates and raise no error.

### **AC-2** A template has its kind, shape, description, path and entry mark

A template carries its `kind`, its `shape` and `description` when it has them,
its path in the repository, and whether it is the entry template of its kind.

#### The fields

- **Given** the kinds `feature = "feature.draft"` and templates `feature.draft`
  and `feature.leaf`, both of kind `feature`, the first with a shape and a
  description and the second with neither.
- **When** the templates are found.
- **Then** `feature.draft` is the entry and has its shape and description,
  `feature.leaf` is not and has neither, and each has its path.

### **AC-3** A problem in reading a template is an error diagnostic

A file that cannot be read or decoded, a metadata block that cannot be read, a
`kind` that is missing or not a string, a `shape` or `description` that is not a
string, two templates with one name, and a templates directory that is set and
missing, not a directory or a symbolic link are each an error diagnostic that
names its place.

#### The problems

- **Given** in turn a file that is not UTF-8, a comment block that does not
  close, a block with no `kind`, a block with `shape = 1`, two files named
  `a.md` in different directories, and a `[templates] dir` that does not exist.
- **When** the templates are found.
- **Then** each gives an error diagnostic whose place is the file, or for the
  two files both of them, or the directory, and the other templates are still
  returned.

### **AC-4** Bare `wio templates` shows the component's help

`wio templates` with no subcommand prints the usage and the subcommands it has
and exits 0.

#### The help

- **Given** a repository.
- **When** `wio templates` runs.
- **Then** the output names `list` and the exit code is 0.

### **AC-5** `wio templates list` shows the templates for a person and a program

The human form groups the templates by kind in sorted order, each with its name,
its shape and its entry mark on one line and its description indented under it,
`--kind` limits it to one declared kind, and `--json` prints one array.

#### The grouped layout

- **Given** the kinds `feature = "feature.draft"`, templates `feature.draft`
  with shape `draft`, `feature.leaf` with shape `leaf` and a description, and
  `bugfix.fix` with no shape and no description.
- **When** `wio templates list` runs.
- **Then** it prints `bugfix`, then `bugfix.fix`, then `feature`, then
  `feature.draft  draft, entry`, `feature.leaf  leaf` and the description of
  each indented by four spaces under its line, with no description line for one
  that has none.

#### One kind

- **Given** the same project.
- **When** `wio templates list --kind feature` and
  `wio templates list --kind nosuch` run.
- **Then** the first prints the `feature` group alone, and the second prints an
  error that names `nosuch` and the declared kinds and exits 2.

#### JSON

- **Given** the same project.
- **When** `wio templates list --json` and
  `wio templates list --kind feature --json` run.
- **Then** the first prints one array sorted by kind and then name, each object
  with `name`, `kind`, `shape`, `entry`, `description` and `path`, and `null`
  for a missing shape or description, and the second prints the objects of that
  kind only.

#### No templates

- **Given** a project with no templates.
- **When** `wio templates list` and `wio templates list --json` run.
- **Then** the first prints nothing and the second prints `[]`, each exiting 0.

### **AC-6** A project with a template error is refused

`wio templates list` prints the errors it found, says that `wio templates check`
shows every problem, and exits 2 without listing anything.

#### A broken template

- **Given** a project with one valid template and one whose comment block does
  not close.
- **When** `wio templates list` and `wio templates list --json` run.
- **Then** each prints an error that names the broken file, mentions
  `wio templates check`, lists no template, and exits 2.

### **AC-7** This repository's templates are named by their files

The three `feature` templates of this repository have no `name` key, and
`wio templates list` names them by their files.

#### The repository's templates

- **Given** this repository.
- **When** `wio templates list` runs.
- **Then** it lists `feature.draft` as the entry, `feature.leaf` and
  `feature.parent` under `feature`, and none of the three files has a `name`
  key.

### **AC-8** The documents describe finding and listing templates

`docs/concepts.md`, `docs/v0.1-scope.md` and `GLOSSARY.md` say that a template
is named by its file, that it has no `name` key, how the walk finds templates,
that discovery reports problems as diagnostics and `list` and `show` refuse on
an error, what `list` prints in its human and its JSON form, `--kind` and the
entry mark, and the glossary defines Template name and no longer gives a
template a `name` in its metadata.

## Additional context

- [Kinds and entry templates](../../../../../docs/concepts.md#kinds-and-entry-templates)
  holds the rules of the walk this Work follows.
- The [show](../show/README.md), [check](../check/README.md) and
  [directives reference](../directives-reference/README.md) leaves add their
  subcommands to the `wio templates` that this one wires.
