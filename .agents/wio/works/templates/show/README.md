<!-- wio
id = "6k795v"
template = "feature.leaf"
roots = ["wio", "repo"]
depends_on = ["0nfz54", "776g94"]
-->

# Showing a template

## Purpose

An agent must be able to see the shape of a template without creating a Work, so
that it can rewrite a contract in that shape.

## Goals

- `wio templates show <name>` prints the skeleton of that template and nothing
  else.
- A name that no template has is refused with the names that exist, so the
  caller can correct it in one step.
- A project with a template error is refused, as `list` refuses it.
- `wio templates` tells that `show` exists.

## Non-Goals

- `--work` and `--keep`, which need to find and read a Work and belong to the
  contracts Work.
- `--json`, because the skeleton is text that is consumed as it is.
- A header, a summary or anything on standard error on success, which `list`
  already gives.
- Choosing a template by its kind.

## Assumptions

- **A-1**: The discovery leaf is delivered, so templates are found, named by
  their files and returned with their diagnostics.

## Mechanisms

- The component of `wio.templates`, which finds the template by its name and
  reads its text through the `FileSystem` port.
- The skeleton function of `wio.formats`, which prepares the text.
- The command spec of `wio.templates`, which gains the `show` subparser; the
  table of commands of `wio.cli` already names `templates`.
- `Stdio` of `wio.io`, through which the skeleton is written.

## Constraints

- **Standard output is the skeleton.** On success it is exactly the skeleton's
  text, and nothing is written to standard error.
- **The name is matched exactly.** It is the template's name with its case, and
  a kind is not a template's name.
- **Exit codes follow the command line's contract.** A template error, which
  includes one that the skeleton function finds in the shown template, or an
  unknown name is an error the user must fix and exits 2, and a wrong command
  line is a usage mistake that exits 2.
- **Verification.** The output is verified by AC-1, the unknown name by AC-2,
  the refusal by AC-3, the command line by AC-4 and the documents by AC-5.

## Acceptance criteria

### **AC-1** `show` prints the skeleton of the named template

Standard output is exactly the skeleton of the template with that name, standard
error is empty and the exit code is 0.

#### A named template

- **Given** a project whose templates directory holds `feature.leaf` and
  `feature.parent`.
- **When** `wio templates show feature.leaf` runs.
- **Then** standard output is the skeleton that the skeleton function gives for
  that file's text under the name `feature.leaf`, standard error is empty and
  the exit code is 0; run again, the output is the same.

### **AC-2** A name that no template has is refused with the names that exist

An unknown name, a name with another case and a kind are errors that name what
was asked and list the templates that exist.

#### The unknown names

- **Given** the same project, with the kind `feature`.
- **When** `wio templates show nosuch`, `wio templates show Feature.Leaf` and
  `wio templates show feature` run.
- **Then** each prints an error that names what was given and lists
  `feature.leaf` and `feature.parent`, prints nothing to standard output and
  exits 2.

### **AC-3** A project with a template error is refused

`show` prints the errors that discovery found, says that `wio templates check`
shows every problem and exits 2, even for a valid template.

#### A broken neighbour

- **Given** a project with the valid template `feature.leaf` and a template
  whose comment block does not close.
- **When** `wio templates show feature.leaf` runs.
- **Then** it prints an error that names the broken file and mentions
  `wio templates check`, prints nothing to standard output and exits 2.

#### A bad directive list in the shown template

- **Given** a project whose template `feature.leaf` has
  `## A <!-- wio: mandatory -->` on line 12.
- **When** `wio templates show feature.leaf` runs.
- **Then** it prints an error that names the file, line 12 and the column,
  prints nothing to standard output and exits 2.

### **AC-4** `show` takes one name and no `--json`

A command line without a name, with two names or with `--json` is a usage
mistake, and the help of `wio templates` names `show`.

#### The command line

- **Given** a repository.
- **When** `wio templates show`, `wio templates show a b` and
  `wio templates show feature.leaf --json` run, and then `wio templates`.
- **Then** each of the first three exits 2 with a usage message, and the help
  names `show`.

### **AC-5** The documents describe `show`

`docs/concepts.md`, `docs/v0.1-scope.md` and `docs/workflow.md` say that
`wio templates show <name>` prints the bare skeleton with nothing around it,
that an unknown name lists the names that exist, and that `--work` and `--keep`
belong to `wio contracts` and are no longer options of `wio templates show`.

## Additional context

- [From template to contract](../../../../../docs/concepts.md#from-template-to-contract)
  says how a skeleton is prepared.
- The [skeleton](../skeleton/README.md) leaf prepares the text and the
  [discovery](../discovery/README.md) leaf finds the template.
