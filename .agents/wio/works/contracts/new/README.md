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
- The new contract is the template's skeleton with the id, the title and the
  roots that were asked for.
- The person is told the id and the path of the new Work, in a form a script can
  read.
- Nothing is created when anything that was asked for is wrong.
- Setting keys in a contract's metadata block is done by one function in
  `wio.formats`, whose behaviour is fixed.

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
  block form, with the `template` key and no `id`, and drops the template's own
  keys, its metadata comments and the directive lists, as it is delivered.
- **A-3**: `tomlkit` replaces a value in place and keeps the order of the keys
  and the rest of the text, and adding a first key is done on the text of the
  block.

## Mechanisms

- A function in `wio.formats` that takes the text of a contract and the plain
  keys and tables to set, a table being given after the plain keys and in order,
  and returns the text with them set in its metadata block: the `id` first,
  after `wio = 1` for `+++` front matter, an `id` that is already there replaced
  in place, and any other key in place, or, when the block has none, a plain key
  after the last plain key and a table after the last table, or after the plain
  keys when there is none. An inline table counts as a plain key, and only an
  added table is preceded by one empty line. An added key or table is written
  with the line ending of the text, and a byte-order mark is kept.
- `prepare_skeleton` and `read_outline` of `wio.formats`, the last to find the
  first level-1 heading that `--title` replaces.
- The decision and the guard of the new-location leaf, the catalog's `find` and
  `is_rejected`, the `FileSystem` port to read the template's text at the
  catalog's path, and `Repository` for the root that the report's path is
  relative to. The parent of a new Work is computed here: the Work of the
  nearest directory above its path that holds a discovered Work, none under
  `flat`, which serves `--path` as well as `--parent`.
- `Config` for the kinds, their entry templates and the declared roots, the
  `Entropy` port, which `wio.cli` wires into the group for this leaf, and `json`
  for `--json` only.
- A `new` entry in the table of the group, with the argument `kind` and the
  options `--template`, `--parent`, `--slug`, `--title`, `--path`, `--root` and
  `--json`.
- The names and the signatures above are provisional, for the architecture stage
  to decide.

## Constraints

- **The template decides.** `new <kind>` starts from the entry template of the
  kind and `--template <name>` from that template. Given both, the template's
  kind must be the kind. Given neither, it writes the bare contract.
- **The skeleton is the baseline, and three things change.** The text is what
  `prepare_skeleton` gives. On top of it the `id` is added first, `roots` is
  replaced when `--root` is given, and the first level-1 heading is replaced
  when `--title` is given. A title is trimmed, and must then be one non-blank
  line, or the error is ``The title must be one non-blank line``, or, when the
  template has none, inserted before the first line of the body that is not
  empty and followed by one empty line, in the template's line ending, or at the
  end of the body when it has no such line. Nothing else changes: the block's
  form, the line endings, the authoring comments and the sections stay as the
  skeleton has them. A bare contract has `# Title` unless `--title` is given.
- **Roots are a set of declared names.** `--root` is repeatable, each name is a
  declared root or `@descendants`, and a name given twice counts once, in the
  order of its first appearance. On a bare contract it adds the key `roots`.
- **Everything is checked before anything is written.** A mistake of the user is
  a `ContractsError`, exit 2, and no file is created.
- **One error for each call, the first of these.** No kinds, the kind, the
  template, a root, the title, then the errors of placement in the order of the
  new-location leaf. A blank title is the title error, and not the slug error.
- **The errors say what to do.** `new <kind>` with no kinds declared says so, an
  undeclared kind names it and the declared ones, a template that is missing or
  rejected, whether it is a kind's entry template or comes from `--template`,
  points to `wio templates check` when it is rejected or is an entry template,
  and a name that no file has points to `wio templates list`.
- **One file is written.** It is written once, through the guard, and ends as
  the skeleton does, with one line ending. The report follows the write, so a
  write that fails reports nothing on standard output.
- **The report is short.** The human form is `Created Work <id>  <title>` and
  the path on the next line, indented two spaces, and `--json` is one object
  with `id`, `title`, `path`, `template` and `parent`, with `null` for none, the
  `path` being relative to the repository root and written with `/`, and the
  parent being the new Work's parent in the tree, whether it came from
  `--parent` or from the place of `--path` under `nesting`, and `null` under
  `flat`. The title is the first level-1 heading of the text written,
  `(no title)` in the human form and `null` in JSON when there is none.

## Acceptance criteria

### **AC-1** A Work is created from the entry template of a kind

The file is the template's skeleton with the id, the roots and the title that
were asked for, and the report names the id and the path.

#### A kind with roots and a title

- **Given** a config with the kind `feature` whose entry template
  `feature.draft` has the block `kind = "feature"`, `[contract]` with
  `roots = []` and `depends_on = []`, and the body `# <Work name>`, `## Purpose`
  and `<!-- Why. -->`, the root `wio` declared, and an `Entropy` that gives the
  bytes 19, 3, 20, 9, 29 and 23. The skeleton drops the template's `kind` and
  `[contract]`, so the file has neither.
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

- **Given** a config that declares the kinds `feature`, with the entry template
  `feature.draft`, and `other`, with the entry template `other.note`, and the
  root `wio`, the templates of AC-1, a template `feature.leaf` of the kind
  `feature` whose `[contract]` has `roots = ["wio"]`, a valid template
  `other.note` of the kind `other`, a Work `p5n2hv` at `p/README.md` under
  `nesting`, an `Entropy` that gives the bytes 19, 3, 20, 9, 29 and 23, and a
  tree of its own for each run.
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

- **Given** `hierarchy = "nesting"`, an `Entropy` that gives the bytes 19, 3,
  20, 9, 29 and 23, and an empty tree for each run, with the root `wio`
  declared.
- **When** `wio contracts new --slug note`, `wio contracts new --title Read` and
  `wio contracts new --path .agents/wio/works/x/spec.md --root wio` run.
- **Then** the first writes `.agents/wio/works/note/README.md` that holds
  exactly `<!-- wio`, `id = "k3m9xq"`, `-->`, an empty line and `# Title`, each
  line ending in a line feed, the second writes
  `.agents/wio/works/read/README.md` whose heading is `# Read`, the third writes
  `.agents/wio/works/x/spec.md` whose block has `id = "k3m9xq"` and
  `roots = ["wio"]`, and each reports its id and path.

### **AC-4** The block is edited and nothing else is

The `id` goes first, the roots are replaced or added, the title is replaced or
added, and the form, the keys, the line endings and the body are kept.

#### Front matter, roots and line endings

- **Given** a config declaring the roots `api` and `web` and the kind `feature`,
  an `Entropy` that gives the bytes 19, 3, 20, 9, 29 and 23 and a tree of its
  own for each run, and templates of the kind, each with `kind = "feature"` and
  a `[contract]` table: `t.front` in `+++` form with `wio = 1` whose
  `[contract]` has `roots = ["a"]`; `t.plain` whose `[contract]` has no `roots`
  and has a table `[contract.x]`; and `t.crlf` written with CRLF line endings,
  with no title heading and a `[contract]` that has `depends_on = []`.
- **When** `wio contracts new --template t.front --slug a` runs with
  `--root api --root web --root api`, `wio contracts new --template t.plain
  --slug b --root api` runs, and `wio contracts new --template t.crlf --slug c`
  runs.
- **Then** the first has `wio = 1`, `id`, `template` and
  `roots = ["api", "web"]` in that order, the second has `roots = ["api"]` right
  after `template` and its `[x]` as it was, and the third has CRLF endings
  throughout and the same body as its template.

#### CRLF with roots

- **Given** the template `t.crlf` with CRLF endings and a `[contract]` that has
  `depends_on = []` and no `roots`.
- **When** `wio contracts new --template t.crlf --slug g --root api` runs.
- **Then** the block has `roots = ["api"]` added, written with CRLF, and every
  line ending of the file is CRLF.

#### A template with no title

- **Given** a template `t.notitle` whose text is the block, an empty line and
  `## Purpose`, with no level-1 heading.
- **When** `wio contracts new --template t.notitle --title Mine --slug d` runs,
  and then the same without `--title` with `--slug e`, and
  `wio contracts new --template t.crlf --title Mine --slug f` runs.
- **Then** the first file ends with the lines `-->`, an empty line, `# Mine`, an
  empty line and `## Purpose`, so the heading comes after the body's leading
  empty line and before its first line that is not empty, the second is the
  template's text with the `id` added and reports `(no title)`, and the third
  has its added heading and empty line with CRLF endings.

### **AC-5** A mistake creates nothing

Each mistake is an error that says what to do, and no file is written.

#### Each mistake

- **Given** a config with no kinds, a config with the kind `feature` whose entry
  template is missing, one whose entry template `bad` is rejected by
  `wio templates check`, the config of AC-1, an `Entropy` that gives the bytes
  19, 3, 20, 9, 29 and 23, and a tree of its own for each run.
- **When** `wio contracts new feature --slug a` runs on the first three,
  `wio contracts new nosuch --slug a`,
  `wio contracts new feature --template nosuch --slug a` and
  `wio contracts new feature --root nosuch --slug a` run on the last, and
  `wio contracts new --slug a` runs on the first.
- **Then** each of the first six exits 2 with its own message: that no kinds are
  declared, that the entry template is missing and points to
  `wio templates check`, that it is rejected and points to the same, that the
  kind `nosuch` is not declared and names `feature`, that the template `nosuch`
  does not exist and points to `wio templates list`, and that the root `nosuch`
  is not declared, no file was written in any case, and the last, which is a
  bare contract, succeeds.

#### A rejected template given by name

- **Given** the config of AC-1 and a template `bad` rejected by
  `wio templates check`.
- **When** `wio contracts new feature --template bad --slug a` runs.
- **Then** it exits 2 with an error that says the template is rejected and
  points to `wio templates check`, and no file is written.

#### Two mistakes at once, a bad title and a placement mistake

- **Given** the config of AC-1, an `Entropy` that gives the bytes 19, 3, 20, 9,
  29 and 23, and a tree of its own for each run.
- **When** `wio contracts new nosuch --root nosuch --slug a`,
  `wio contracts new feature --root nosuch --slug child` with an existing
  directory `.agents/wio/works/child`, `wio contracts new --title " "`,
  `wio contracts new --title "line one"` with a line break in the title, and
  `wio contracts new --parent nosuch --title X` run.
- **Then** the first reports only the kind, the second only the root, the third
  and the fourth the title error, and the fifth that no Work has the id
  `nosuch`, each exits 2, and no file is written.

#### A write that fails

- **Given** a `FileSystem` fake that reports the path free to the decision and
  existing to the guard.
- **When** `wio contracts new feature --slug a` runs.
- **Then** it exits 2 with an error that names the path, writes nothing to
  standard output, and creates no file.

### **AC-6** `--json` is one object with the same facts

The object has the fields in a fixed order and `null` for what there is none.

#### Objects

- **Given** `hierarchy = "nesting"`, the config and templates of AC-2, a Work
  `p5n2hv` at `p/README.md`,
  no `child` or `note` directory, and an `Entropy` that gives the bytes 19, 3,
  20, 9, 29 and 23, in a tree of its own for each run.
- **When** `wio contracts new feature --template feature.leaf --parent p5n2hv
  --title Child --json` and `wio contracts new --slug note --json` run.
- **Then** the first prints one object with `"id": "k3m9xq"`,
  `"title": "Child"`, `"path": ".agents/wio/works/p/child/README.md"`,
  `"template": "feature.leaf"` and `"parent": "p5n2hv"`, in that order, and the
  second has `"title": "Title"`, `"template": null` and `"parent": null`, and
  `wio contracts new feature --template feature.leaf --title Under --path
  .agents/wio/works/p/under/spec.md --json` has `"parent": "p5n2hv"`.

### **AC-7** `new` writes through the one function that sets keys

`new` sets the `id`, the roots and the title through the one function of
`wio.formats` and edits the block nowhere else.

#### A recording stand-in

- **Given** the config of AC-1 and a stand-in for the function that records its
  calls.
- **When** `wio contracts new feature --title "Read config" --root wio` runs.
- **Then** the stand-in was called with the `id` and `roots`, and the block of
  the file is what the stand-in returned.

### **AC-8** The function that sets keys in a block does what it is fixed to do

The one function of `wio.formats` that sets keys in a metadata block puts the
`id` first, replaces a key in place, adds a missing plain key after the last
plain key and a missing table after the last table, and changes nothing else.

#### Cases

- **Given** the text of a contract with a comment block with `template = "t"`,
  `roots = []`, an empty line and a table `[x]` with `a = 1` and the body `# T`,
  and the text of a contract with `+++` front matter with `wio = 1` and
  `template = "t"` and the body `# T`.
- **When** the function sets `id = "k3m9xq"`, `roots = ["wio"]` and
  `depends_on = ["a7b2c4"]` on the first, `id = "k3m9xq"` on the second, and
  then the table `[actions]` with `deliver = ["build"]` on the first.
- **Then** the first block reads `id = "k3m9xq"`, `template = "t"`,
  `roots = ["wio"]`, `depends_on = ["a7b2c4"]`, an empty line, `[x]` with
  `a = 1`, an empty line, and then `[actions]` with `deliver = ["build"]`, the
  second reads `wio = 1`, `id = "k3m9xq"`, `template = "t"`, and the body and
  the delimiters of each are as they were.

## Additional context

- [Identity and location](../../../../../docs/concepts.md#identity-and-location)
  says what a bare contract is and how `new` is used.
- A Work from a lenient entry template, such as the draft, passes `wio contracts
  check` at once. A Work from a strict one fails until its required items are
  written, as the check-body leaf says.
- The skeleton leaf uses the function that sets keys in the block to carry an
  existing Work's `id` and dependencies.
