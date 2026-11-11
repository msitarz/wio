<!-- wio
id = "q6wxj6"
template = "feature.leaf"
roots = ["wio"]
depends_on = ["ces6tf", "sz1zsq"]
-->

# Listing the Works

## Purpose

People and agents need to see the Works of a project and their hierarchy at a
glance, and to see at once where a Work departs from its template's defaults, so
that an override is never hidden.

## Goals

- A person can read every Work with its title, its place in the hierarchy and
  its template in one command.
- The roots, the dependencies and the actions that a Work states itself are
  visible, and what the template supplies is not repeated.
- A script can read the same facts as JSON.

## Non-Goals

- A status of a Work, which wio does not keep, and the roots with
  `@descendants` resolved, which `show` does.
- A filter, such as by parent or by root. It can be added without breaking
  anything.
- Judging the Works, which `check` does.

## Assumptions

- **A-1**: The hierarchy and command leaves are delivered, so the Works with
  their parents, and the group and its table, exist.
- **A-2**: A Work found by discovery carries the id, title, path, template,
  roots, dependencies and action overrides that are listed here.

## Mechanisms

- A `list` entry in the table of the group, and a function in `wio.contracts`
  that renders the Works found, with their hierarchy, as text or as JSON.
- `Work` and the hierarchy of the earlier leaves, and `ContractsError` of the
  command leaf for a refusal.
- `json` imported only for `--json`.
- The names and the signatures above are provisional, for the architecture stage
  to decide.

## Constraints

- **The order is the hierarchy's.** Under `nesting` a Work comes before its
  children, each child is indented two spaces more than its parent, and
  siblings are in the order of their paths. Under `flat` every Work is at the
  same indent, in the order of the paths.
- **A Work is a few lines.** The first line is the id, the title and the
  template in brackets, none when the Work names none, and the id is padded to
  the widest id of the output so that titles line up. A Work with no title
  prints `(no title)`. The detail lines are indented to the title and each is
  written only when it has something to say: the path always, then `roots:`
  as written, `after:` once for each dependency with its title, and
  `actions:`.
- **A dependency not in the tree is marked.** It reads `after: y4k2mq (not
  found)`, and it is never an error of `list`.
- **Only overrides show.** `actions:` lists what the Work's own `[actions]`
  name, a stage preset bare, a list of stages in brackets and an empty list as
  `none`, separated by a comma and a space.
- **A line is as written.** Nothing is cut or wrapped, and the output has no
  timestamp.
- **JSON is one array.** It is sorted by path, and each object has `id`,
  `title`, `path`, `template`, `roots`, `depends_on`, `actions` and `parent`, in
  that order. Roots and dependencies are as written, `title` and `template` are
  `null` when there is none, `parent` is the parent's id or `null`, and an
  absent `[actions]` is `{}`.
- **Discovery errors refuse the listing.** A tree with an error of finding the
  Works lists nothing, writes the errors, says that `wio contracts check` shows
  every problem, and exits 2. Errors of the metadata or the graph do not stop
  it.
- **Nothing is written.** The command reads and prints, and a tree with no Work
  prints nothing, or `[]` with `--json`.

## Acceptance criteria

### **AC-1** The Works are listed with their hierarchy and their overrides

Under `nesting` each Work is a block, its children are indented below it, and
only what the Work states itself is shown.

#### A parent and two children

- **Given** `hierarchy = "nesting"` and Works: `p5n2hv` titled `Parent` at
  `p/README.md` from `feature.parent` with `roots = ["@descendants"]`; `k3m9xq`
  titled `Child one` at `p/a/README.md` from `feature.leaf` with
  `roots = ["wio"]`, `[actions]` of `deliver = ["build"]`,
  `define = "define-feature"` and `amend = []`; and `a7b2c4` titled
  `Child two` at `p/b/README.md` with no template that lists `k3m9xq` and
  `y4k2mq` in `depends_on`, which no Work has.
- **When** `wio contracts list` runs.
- **Then** it prints exactly this, and exits 0:

  ```text
  p5n2hv  Parent  [feature.parent]
          .agents/wio/works/p/README.md
          roots: @descendants
    k3m9xq  Child one  [feature.leaf]
            .agents/wio/works/p/a/README.md
            roots: wio
            actions: deliver = [build], define = define-feature, amend = none
    a7b2c4  Child two
            .agents/wio/works/p/b/README.md
            after: k3m9xq Child one
            after: y4k2mq (not found)
  ```

### **AC-2** Under flat every Work is at the same indent

Under `flat` there is no nesting, the order is the order of the paths, and the
id column is as wide as the widest id.

#### Three Works

- **Given** `hierarchy = "flat"` and Works `k3m9xq` titled `Alpha` at
  `a/README.md` from `feature.leaf`, `spec0012` titled `Beta` at `b/README.md`
  with `roots = ["api"]` and no template, and `n5p7qr` with no heading at
  `c/README.md`.
- **When** `wio contracts list` runs.
- **Then** it prints exactly this, and exits 0:

  ```text
  k3m9xq    Alpha  [feature.leaf]
            .agents/wio/works/a/README.md
  spec0012  Beta
            .agents/wio/works/b/README.md
            roots: api
  n5p7qr    (no title)
            .agents/wio/works/c/README.md
  ```

### **AC-3** `--json` is one array with the same facts

The JSON has one object for each Work in the order of the paths, with the fields
in a fixed order.

#### The same Works as JSON

- **Given** the Works of AC-1 and of AC-2.
- **When** `wio contracts list --json` runs on each.
- **Then** each prints one array that parses, on one line. The first array
  starts with this object, shown here over several lines:

  ```json
  {
    "id": "p5n2hv",
    "title": "Parent",
    "path": ".agents/wio/works/p/README.md",
    "template": "feature.parent",
    "roots": ["@descendants"],
    "depends_on": [],
    "actions": {},
    "parent": null
  }
  ```

  Its second object has `"parent": "p5n2hv"` and the actions
  `{"deliver": ["build"], "define": "define-feature", "amend": []}`, and the
  second array has `"title": null` for `n5p7qr` and `"parent": null` for each
  Work.

### **AC-4** A tree with no Work prints nothing

An empty tree is not an error.

#### No Works

- **Given** a repository with no Work.
- **When** `wio contracts list` and `wio contracts list --json` run.
- **Then** the first prints nothing and the second prints `[]`, and each exits
  0.

### **AC-5** An error of finding the Works refuses the listing

A tree with an error of discovery lists nothing and points to `check`, and an
error of the metadata or the graph does not stop the listing.

#### A shared id

- **Given** two Works with one id.
- **When** `wio contracts list` runs.
- **Then** it writes nothing to standard output, writes the error that names
  both paths and a line that says `wio contracts check` shows every problem, to
  standard error, and exits 2.

#### An undeclared root and a cycle

- **Given** a Work with `roots = ["nosuch"]`, and two Works that list each
  other.
- **When** `wio contracts list` runs.
- **Then** it lists all three and exits 0.

### **AC-6** Nothing is written and the output is the same every time

The command changes no file, and two runs print the same bytes.

#### Twice

- **Given** the Works of AC-1 and a hash of each contract.
- **When** `wio contracts list` and `wio contracts list --json` each run twice.
- **Then** the two outputs of each are identical, and the hash of every contract
  is unchanged.

## Additional context

- The format mirrors `wio templates list`: a block for each item, details below
  it, and a line as written.
- A reader who wants the roots resolved, the dependents or where each action
  comes from uses `wio contracts show`.
