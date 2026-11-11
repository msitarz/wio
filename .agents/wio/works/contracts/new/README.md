<!-- wio
id = "pv47sz"
template = "feature.leaf"
roots = ["wio"]
depends_on = ["h8qpxd", "sz1zsq"]
-->

# Creating a Work

## Purpose

A person or an agent starts a Work with one command and gets a contract that
follows the template of its kind, carries a new id, and is ready for the define
stage to fill in. The code that puts an id and roots into a contract's metadata
block must be one that `wio contracts skeleton` reuses, so that no second editor
of the block exists.

## Goals

- A Work is created from the entry template of a kind, from any template, or as
  a bare contract.
- The new contract carries the id, the title and the roots that were asked for,
  and keeps the template's authoring as it was written.
- The person is told the id and the path of the new Work, in a form a script can
  read.
- Nothing is created when anything that was asked for is wrong.
- Setting keys in a contract's metadata block is done by one function in
  `wio.formats`.

## Glossary

- **Bare contract**: a contract that follows no template, holding only the
  block with its `id` and a first heading.

## Non-Goals

- Filling in the body, changing the parent, or running `check`.
- Rewriting an existing Work in another template, which the skeleton leaf does
  with the function made here.
- Choosing a template from what the Work is, which the define stage does.
- Listing the templates that exist, which `wio templates list` does.

## Assumptions

- **A-1**: The new-location and command leaves are delivered, so the id and the
  path are decided, a guard writes one new file, and the group and the catalog
  exist.
- **A-2**: `prepare_skeleton` gives a template's skeleton in the template's
  block form, with the `template` key and no `id`, as it is delivered.
- **A-3**: `tomlkit` replaces a value in place and keeps the order of the keys
  and the rest of the text, and adding a first key is done on the text of the
  block.

## Mechanisms

- A function in `wio.formats` that sets keys in the metadata block of a
  contract's text, any top-level key or table: the `id` first, after `wio = 1`
  for `+++` front matter, and any other key in place, or after the last key
  that holds a value and before the first table when the block has none. The
  block's form, its other keys and its body are not changed.
- `prepare_skeleton` and `read_outline` of `wio.formats`, the last to find the
  first heading that `--title` replaces.
- The decision and the guard of the new-location leaf, and the catalog's `find`
  and `is_rejected`.
- `Config` for the kinds, their entry templates and the declared roots, and
  `json` for `--json` only.
- A `new` entry in the table of the group, with the argument `kind` and the
  options `--template`, `--parent`, `--slug`, `--title`, `--path`, `--root` and
  `--json`.
- The names and the signatures above are provisional, for the architecture stage
  to decide.

## Constraints

- **The template decides.** `new <kind>` starts from the entry template of the
  kind and `--template <name>` from that template. Given both, the template's
  kind must be the kind. Given neither, it writes the bare contract.
- **Only three things change.** The `id` is added first, `roots` is replaced
  when `--root` is given, and the first heading is replaced when `--title` is
  given. The block's form, the template's line endings, its authoring comments
  and its sections stay as they were. Without `--title` the template's heading
  stays, and a bare contract has `# Title`.
- **Roots are a set of declared names.** `--root` is repeatable, each name is a
  declared root or `@descendants`, and a name given twice counts once.
- **Everything is checked before anything is written.** A mistake of the user is
  a `ContractsError`, exit 2, and no file is created.
- **The errors say what to do.** No kinds declared says so, an undeclared kind
  names it and the declared ones, a kind whose entry template is missing or
  rejected points to `wio templates check`, and a template that no file has
  points to `wio templates list`.
- **One file is written.** It is written once, through the guard, and the report
  follows the write.
- **The report is short.** The human form is `Created Work <id>  <title>` and
  the path on the next line, indented two spaces, and `--json` is one object
  with `id`, `title`, `path`, `template` and `parent`, with `null` for none.

## Acceptance criteria

### **AC-1** A Work is created from the entry template of a kind

The file is the template's skeleton with the id, the roots and the title that
were asked for, and the report names the id and the path.

#### A kind with roots and a title

- **Given** a config with the kind `feature` whose entry template
  `feature.draft` has the block `kind = "feature"`, `[contract]` with
  `roots = []` and `depends_on = []`, and the body `# <Work name>`, `## Purpose`
  and `<!-- Why. -->`, the root `wio` declared, and an `Entropy` that gives the
  bytes 19, 3, 20, 9, 29 and 23.
- **When** `wio contracts new feature --title "Read config" --root wio` runs.
- **Then** the file `.agents/wio/works/read-config/README.md` holds exactly
  this, and the command prints the two lines below and exits 0:

  ```text
  <!-- wio
  id = "k3m9xq"
  template = "feature.draft"
  roots = ["wio"]
  depends_on = []
  -->

  # Read config

  ## Purpose

  <!-- Why. -->
  ```

  ```text
  Created Work k3m9xq  Read config
    .agents/wio/works/read-config/README.md
  ```

### **AC-2** Any template can be used, and kind and template must agree

`--template` starts the Work from that template, and a template of another kind
is an error.

#### A template under a parent

- **Given** the config and templates of AC-1, a template `feature.leaf` of the
  kind `feature`, a template `other.note` of the kind `other`, and a Work
  `p5n2hv` at `p/README.md` under `nesting`.
- **When** `wio contracts new feature --template feature.leaf --parent p5n2hv
  --title Child` runs, `wio contracts new --template feature.leaf --slug a`
  runs, and `wio contracts new feature --template other.note --slug b` runs.
- **Then** the first writes `.agents/wio/works/p/child/README.md` with
  `template = "feature.leaf"` and the leaf's roots, the second writes a Work
  from `feature.leaf` with no kind given, and the third is an error that says
  the template is of the kind `other`, not `feature`.

### **AC-3** A bare contract holds the id and a heading

With no kind and no template, the file is the block with the `id` and a heading.

#### Bare

- **Given** an `Entropy` that gives the bytes 19, 3, 20, 9, 29 and 23, and an
  empty tree for each run.
- **When** `wio contracts new --slug note` and `wio contracts new --title Read`
  run.
- **Then** the first writes `.agents/wio/works/note/README.md` that holds
  exactly `<!-- wio`, `id = "k3m9xq"`, `-->`, an empty line and `# Title`, the
  second writes `.agents/wio/works/read/README.md` that holds `# Read`, and each
  reports its id and path.

### **AC-4** The block is edited and nothing else is

The `id` goes first, the roots are replaced or added, and the form, the keys,
the line endings and the body are kept.

#### Front matter, roots and line endings

- **Given** a template in `+++` form with `wio = 1`, `template` and
  `roots = ["a"]`, one with no `roots` key whose block has the tables `[x]`, and
  one written with CRLF line endings.
- **When** `wio contracts new` runs on each, the first with
  `--root api --root web --root api`, the second with `--root api`.
- **Then** the first has `wio = 1`, `id`, `template` and
  `roots = ["api", "web"]` in that order, the second has `roots = ["api"]` right
  after `template` and its `[x]` as it was, and the third has CRLF endings
  throughout and the same body as its template.

### **AC-5** A mistake creates nothing

Each mistake is an error that says what to do, and no file is written.

#### Each mistake

- **Given** a config with no kinds, a config with the kind `feature` whose entry
  template is missing, one whose entry template `bad` is rejected by
  `wio templates check`, and the config of AC-1.
- **When** `wio contracts new feature --slug a` runs on the first three,
  `wio contracts new nosuch --slug a` runs on the last,
  `wio contracts new feature --template nosuch --slug a` and
  `wio contracts new feature --root nosuch --slug a` run on the last.
- **Then** each exits 2 with its own message: that no kinds are declared, that
  the entry template is missing and points to `wio templates check`, that it is
  rejected and points to the same, that the kind `nosuch` is not declared and
  names `feature`, that the template `nosuch` does not exist and points to
  `wio templates list`, and that the root `nosuch` is not declared, and no file
  was written in any case.

### **AC-6** `--json` is one object with the same facts

The object has the fields in a fixed order and `null` for what there is none.

#### Objects

- **Given** the Works of AC-2 and AC-3.
- **When** `wio contracts new feature --template feature.leaf --parent p5n2hv
  --title Child --json` and `wio contracts new --slug note --json` run.
- **Then** the first prints one object with `"id"`, `"title": "Child"`, the
  path, `"template": "feature.leaf"` and `"parent": "p5n2hv"`, in that order,
  and the second has `"title": "Title"`, `"template": null` and
  `"parent": null`.

## Additional context

- [Identity and location](../../../../../docs/concepts.md#identity-and-location)
  says what a bare contract is and how `new` is used.
- A Work from a lenient entry template, such as the draft, passes `wio contracts
  check` at once. A Work from a strict one fails until its required items are
  written, as the check-body leaf says.
- The skeleton leaf uses the function that sets keys in the block to carry an
  existing Work's `id` and dependencies.
