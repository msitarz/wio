<!-- wio
id = "zfx8h2"
template = "feature.leaf"
roots = ["wio", "repo"]
depends_on = ["1n1p8j", "776g94", "vyjmpc"]
-->

# Checking the templates

## Purpose

A broken template must be caught before a contract follows it, and the person or
agent that broke it must be told what is wrong and where, all at once.

## Goals

- `wio templates check` prints every problem of the project's templates in one
  run, or says that they pass.
- A misspelled key, a wrong directive, a name that the config does not declare
  and a kind that does not agree with the config are each reported with the file
  they are in.
- A problem that only looks suspicious is a warning and does not fail the check.
- The diagnostics are the shared ones, in text and as JSON.

## Non-Goals

- Limiting the check to one file.
- Judging a contract against its template, which `wio contracts check` does.
- Finding the items of a section, which the contracts Work decides.
- Checking the config's own shape or references, which `wio config check` does.

## Assumptions

- **A-1**: The discovery, directives and outline leaves are delivered, so
  templates are found with their diagnostics, a heading's directive list is
  parsed and a body's real headings are found.
- **A-2**: The config holds the declared actions, stage presets, stages and
  kinds, and `Settings` returns them.

## Mechanisms

- The component of `wio.templates`, which gains one check for each concern, each
  a function from the templates and the config to diagnostics, run together
  after discovery.
- The directive parser and the outline of `wio.formats`, which read each
  template's headings.
- `Diagnostic` of `wio.models` and the renderers of `wio.formats`, which print
  the diagnostics as text and as JSON.
- `wio.cli`'s table of commands, which gains `check` under `templates`.

## Constraints

- **Every problem is reported at once.** A check never stops at the first
  problem, and the diagnostics are printed in one sorted order.
- **Only an error fails.** An error exits 1, and a warning is printed and exits
  0.
- **Unknown keys are errors.** The keys a template's metadata may have are
  `kind`, `shape`, `description`, `[actions]` and `[contract]`, and the keys
  under `[contract]` are free.
- **Directives are read on level-2 headings only.** A directive list on any
  other level is an error.
- **A diagnostic names its place.** It is the file and, where there is one, the
  line of the heading or the key path of the config entry.
- **Verification.** The output is verified by AC-1, discovery's problems by
  AC-2, the keys by AC-3, the directives by AC-4, the actions by AC-5, the kinds
  by AC-6, the warning by AC-7 and the documents by AC-8.

## Acceptance criteria

### **AC-1** A project that passes says so and a failing one prints every problem

`wio templates check` says that the templates pass and exits 0 when there is no
error, and otherwise prints every diagnostic sorted and exits 1, as text or with
`--json` as an array.

#### A passing project

- **Given** a project whose templates have no problem.
- **When** `wio templates check` and `wio templates check --json` run.
- **Then** the first says that the templates pass and the second prints `[]`,
  each exiting 0.

#### Two problems at once

- **Given** a project with an unknown key in one template and a wrong directive
  in another.
- **When** `wio templates check` runs.
- **Then** it prints both as `<severity>: <where>: <message>` lines in sorted
  order and exits 1.

### **AC-2** The problems that discovery finds are errors of the check

A file that cannot be read, a block that cannot be read, a missing or mistyped
`kind`, `shape` or `description`, two templates with one name and a bad
templates directory are printed as errors.

#### Discovery's problems

- **Given** a project with a comment block that does not close and two files
  named `a.md` in different directories.
- **When** `wio templates check` runs.
- **Then** it prints an error for the block that names its file and one for the
  duplicate that names both files, and exits 1.

### **AC-3** An unknown key is an error and the contract's keys are free

A key outside `kind`, `shape`, `description`, `[actions]` and `[contract]` is an
error, and so is a `[contract]` or an `[actions]` that is not a table.

#### The keys

- **Given** a template with `name = "x"`, one with `descriptions = "y"`, one
  with `contract = 1`, and one whose `[contract]` holds `ticket = ""`.
- **When** `wio templates check` runs.
- **Then** the first three each give an error that names the file and the key,
  the first one saying that a template is named by its file, and the fourth
  gives none.

### **AC-4** A wrong directive list is an error with its file, line and column

A directive list that the parser refuses, a list that does not close on its
line, and a list on a heading that is not level 2 are errors that name the file,
the line and, where the parser gives one, the column.

#### The directive errors

- **Given** a template with `## A <!-- wio: mandatory -->` on line 12,
  `## B <!-- wio: required,` on line 14 and `### C <!-- wio: required -->` on
  line 16.
- **When** `wio templates check` runs.
- **Then** it prints an error for each that names the file and its line, the
  first and the second with their columns, and the third saying that directives
  are read on level-2 headings only.

### **AC-5** A name in `[actions]` that the config does not declare is an error

An action that the config does not declare, a stage preset that it does not
declare and a stage that it does not declare are errors, and an empty list is
not.

#### The names

- **Given** a config declaring the action `define`, the stage preset
  `define-feature` and the stage `implementation`, and templates whose
  `[actions]` hold `define = "nosuch"`, `nosuch = "define-feature"`,
  `define = ["nosuch"]`, `define = []` and `define = ["implementation"]`.
- **When** `wio templates check` runs.
- **Then** the first three each give an error that names the file and the
  undeclared name, and the last two give none.

### **AC-6** A kind that does not agree with the config is an error

A template whose `kind` is not declared in `[templates.kinds]`, an entry
template that does not exist and an entry template of another kind are errors.

#### The kinds

- **Given** the kinds `feature = "feature.draft"` and `bugfix = "missing"`, a
  template `feature.draft` of kind `bugfix`, and a template `other` of kind
  `nokind`.
- **When** `wio templates check` runs.
- **Then** it prints an error for `other` that names its file and the kind, an
  error for the entry of `bugfix` that names the config entry and `missing`, and
  an error for `feature.draft` that names its file and says its kind differs
  from the one it starts.

### **AC-7** A repeated `##` heading is a warning

Two `##` headings of one template with the same text, ignoring case, spaces and
a trailing directive list, are a warning, and the check still exits 0.

#### A repeated heading

- **Given** a template with `## Goals <!-- wio: required -->` and `## goals`.
- **When** `wio templates check` runs.
- **Then** it prints a warning that names the file and both lines, and exits 0.

### **AC-8** The documents describe the check

`docs/concepts.md` and `docs/v0.1-scope.md` list what `wio templates check`
judges, which are the discovery's problems, the keys, the directives, the names
in `[actions]`, the kinds and the repeated heading, with which are errors and
which is a warning, and that it checks the whole project.

## Additional context

- [Kinds and entry templates](../../../../../docs/concepts.md#kinds-and-entry-templates)
  and [Directives](../../../../../docs/concepts.md#directives) are what it
  judges against.
- The [discovery](../discovery/README.md), [directives](../directives/README.md)
  and [outline](../outline/README.md) leaves are what it reads through, and the
  [hooks](../hooks/README.md) leaf runs it after an edit.
