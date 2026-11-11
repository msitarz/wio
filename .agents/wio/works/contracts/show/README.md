<!-- wio
id = "bhrjjs"
template = "feature.leaf"
roots = ["wio"]
depends_on = ["h3jhtw", "sz1zsq", "ces6tf", "xtgz9z", "h69nf8", "mb4q2g"]
-->

# Showing a Work

## Purpose

People and agents need to see one Work with everything that applies to it: where
it sits, what it waits for and what waits for it, which actions it has and
where each comes from, and its contract with what its ancestors pass on.

## Goals

- A person can read one Work in one command: its facts, its actions and its
  resolved contract.
- A person can tell where each action of a Work comes from, so that an override
  is never hidden.
- A script can read the same facts and the contract as JSON.
- A person who names a file that is not a Work, or an id that no Work has, is
  told what is wrong.

## Non-Goals

- The description of an action, which the config holds. By the driver's decision
  `show` does not print it, so the sentence of `docs/concepts.md` that says it
  does changes when the documents are promoted.
- Judging the Work, which `check` does, and the rules that apply to it.
- Explaining the fields of a contract.

## Assumptions

- **A-1**: The resolve and command leaves are delivered, so the resolved view,
  the hierarchy it builds on, and the group and its table exist.
- **A-2**: `Config` gives the actions in the order the config declares them,
  with `on_demand`, the stage presets with their stages, and
  `[works.defaults.actions]`.
- **A-3**: The `Environment` port gives the working directory, against which a
  path argument is resolved.

## Mechanisms

- A `show` entry in the table of the group, and a function in `wio.contracts`
  that renders a Work, as text or as JSON.
- The resolved view of the resolve leaf, the hierarchy of the hierarchy leaf for
  the parent, the resolved roots, the dependencies and the dependents, and the
  explanation of why a path is not a Work from the discovery leaf.
- The resolution of a Work's actions that the check-works leaf defines, with the
  catalog's `find`, `FileSystem` and `read_metadata_block` to read a template's
  `[actions]` from its file at the catalog's path, `Repository` for the root
  that paths are relative to, and `Config` for the actions, stage presets and
  defaults.
- The `Environment` port for the working directory, `closest_key` for a
  mistyped id, and `json` for `--json` only.
- The names and the signatures above are provisional, for the architecture stage
  to decide.

## Constraints

- **The layout is facts, actions, a rule, then the view.** The first line is
  `Work <id>  <title>`, with `(no title)` for a Work with none. The facts
  follow, each line written only when it has something to say and in this order:
  `Path`, `Template`, `Parent`, `Roots`, `After`, `Needed by`. `After` lists the
  ids of `depends_on` only, in the order listed, and a parent's wait for its
  children is not shown. Each is indented two spaces, its label is padded to a
  fixed 13 characters, so that every value starts at column 15, and a second
  dependency or dependent is on the next line, in that column. Then a blank
  line, `Actions` at column 0, the actions, a blank line, a line of `----` at
  column 0, a blank line and the resolved view, exactly as the resolve leaf
  renders it. The text ends in one line ending and is UTF-8.
- **Related Works are `<id>  <title>`.** A dependency that no Work has is
  `<id>  (not found)`, a Work with no title is `<id>  (no title)`, and an id
  that two Works share is written once for each of them.
- **Roots show what they resolve to.** A Work that lists `@descendants` shows
  its roots as written, an arrow and the resolved roots, or `none` when they
  resolve to nothing. Any other Work shows them as written.
- **Actions are the resolved actions, in the order of the config.** They are
  those that the check-works leaf defines: the template's, or the config
  defaults for a Work with no template and only then, with the Work's own
  replacing them. The actions the config declares come first, in its order, then
  the names it does not declare, whatever gives them, in the order that the
  Work's own `[actions]`, the template's and the defaults list them, printed as
  written. Each line is indented two spaces and has the action padded to the
  widest action name plus two spaces, the stage preset it names and, in
  parentheses, where it comes from: `from the template`, `from the contract` or
  `from the config defaults`, preceded by `on demand,` for an action the config
  marks on demand. A list of stages has no preset name. The stages follow on a
  line indented two spaces past the preset's column, joined by a comma and a
  space, and a preset that the config does not declare is printed with no stages
  line. An action that the contract empties is `removed (by the contract)`
  without the on-demand mark, and an action that is empty and that nothing else
  gives is not shown. A template that is missing from the catalog or rejected
  gives no actions, so the Work's own are all there is.
- **A path or an id.** An argument that contains `/` or ends in `.md` is a path,
  resolved against the working directory, and any other is an id. An id that
  contains `/` or ends in `.md` can therefore be shown only by its path, which
  is a known limit.
- **The tree is judged first.** An error of finding the Works that leaves the
  tree incomplete, a Work left out, a collision or a directory that cannot be
  walked, writes nothing to standard output, writes the errors and a line that
  says `wio contracts check` shows every problem, and exits 2, for an id and a
  path alike. Errors of the metadata or the graph do not stop the command.
- **Then the argument is looked up.** An id that no Work has names the id and
  the closest one when there is one, a shared id refuses only its own lookup
  with the error of discovery and the same line, and a file that is not a Work
  names the reason of the discovery leaf for it. Each exits 2, with its message
  on standard error.
- **JSON is one object on one line.** It is the `json.dumps` of the object with
  its default separators, followed by one line ending. It has `id`, `title`,
  `path`, `template`, `parent`, `roots`, `resolved_roots`, `depends_on`,
  `dependents`, `actions` and `view`, in that order. `depends_on` and
  `dependents` are arrays of ids. Each action has `name`, `source`, `on_demand`,
  `preset` and `stages`. `source` is `template`, `contract` or `defaults`,
  `on_demand` is the config's flag, and `view` is the resolved Markdown as one
  string. `title`, `template`, `parent` and `preset` are `null` when there is
  none, a removed action has the source `contract`, no preset and no stages, and
  a preset that the config does not declare has `preset` as written and `stages`
  empty. `path` is relative to the repository root and written with `/`.
- **`json` is imported only for `--json`.** A run without it imports neither
  `json` nor `tomlkit`.

## Acceptance criteria

In these scenarios the Works directory is the default one.

### **AC-1** A Work is shown with its facts, its actions and its resolved contract

The output is the facts, the actions with their sources, a rule and the resolved
view.

#### A child with an override

- **Given** `hierarchy = "nesting"`, a config that declares the kind of
  `feature.leaf`, the actions `define`, `deliver` and `amend`, with `amend` on
  demand, the stages `define`, `review-contract`, `build`, `ship`, `amend` and
  `review-amendment`, and the stage presets `define-feature` of `define` and
  `review-contract` and `amend-contract` of `amend` and `review-amendment`; a
  Work `p5n2hv` titled `Parent` at `p/README.md`; a Work `a7b2c4` titled
  `Sibling` at `p/s/README.md`; and a Work `k3m9xq` titled `Child` at
  `p/c/README.md` from the template `feature.leaf`, whose actions are
  `define = "define-feature"`, `deliver = ["build"]` and
  `amend = "amend-contract"`, with `roots = ["wio"]`, `depends_on = ["a7b2c4"]`
  and its own `[actions]` of `deliver = ["ship"]` and `amend = []`. Its body is
  `# Child`, `## Purpose` and the line `Own text.`, and `Parent` has no template
  and an inheritable `## Glossary <!-- wio: inherit -->` with the line
  `- **Term**: a word.`.
- **When** `wio contracts show k3m9xq` runs.
- **Then** it prints exactly this, ending in one line ending, and exits 0:

  ```text
  Work k3m9xq  Child
    Path         .agents/wio/works/p/c/README.md
    Template     feature.leaf
    Parent       p5n2hv  Parent
    Roots        wio
    After        a7b2c4  Sibling

  Actions
    define   define-feature  (from the template)
               define, review-contract
    deliver  (from the contract)
               ship
    amend    removed (by the contract)

  ----

  # Child

  ## Purpose

  Own text.

  ## Inherited from: Parent (p5n2hv)

  ### Glossary

  - **Term**: a word.
  ```

#### Defaults, an on-demand action and an undeclared name

- **Given** a config that declares the actions `deliver` and `amend`, with
  `amend` on demand, the stages `build`, `amend`, `review-amendment` and `ship`,
  the stage preset `amend-contract` of `amend` and `review-amendment`, and
  `[works.defaults.actions]` of `deliver = ["build"]`
  and `amend = "amend-contract"`, and a Work `k3m9xq` titled `Solo` with no
  template whose own `[actions]` is `ratify = ["ship"]`.
- **When** `wio contracts show k3m9xq` runs.
- **Then** the actions block is exactly this:

  ```text
  Actions
    deliver  (from the config defaults)
               build
    amend    amend-contract  (on demand, from the config defaults)
               amend, review-amendment
    ratify   (from the contract)
               ship
  ```

### **AC-2** Roots resolve, dependents are listed and flat has no relatives

`@descendants` is shown with what it resolves to, the Works that depend on a
Work are listed, and under `flat` there is no parent and nothing is inherited.

#### A parent and its dependents

- **Given** the Works of AC-1 with `Parent` having
  `roots = ["e2e", "@descendants"]`, the Child's `roots` being `["api"]`, the
  Sibling having none, and a Work `k5m8ps` titled `Other` at `p/o/README.md`,
  with no roots, that also lists `a7b2c4`.
- **When** `wio contracts show a7b2c4` and `wio contracts show p5n2hv` run.
- **Then** the first has the lines `Needed by    k3m9xq  Child` and, on the next
  line in the same column, `k5m8ps  Other`, and the second has the line
  `Roots        e2e, @descendants → api, e2e`.

#### Under flat

- **Given** `hierarchy = "flat"` and the same Works.
- **When** `wio contracts show k3m9xq` runs.
- **Then** there is no `Parent` line and the view holds the Work's own contract
  only.

### **AC-3** The argument is a path or an id, and mistakes are told

A path is resolved against the working directory, and an unknown id and a file
that is not a Work are errors that say what is wrong.

#### A path from a subdirectory

- **Given** the Works of AC-1 and the working directory `.agents/wio/works/p`.
- **When** `wio contracts show c/README.md` runs.
- **Then** it prints the same as `wio contracts show k3m9xq`.

#### An id that no Work has

- **Given** the same Works.
- **When** `wio contracts show k3m9xr` and `wio contracts show zzzzzz` run.
- **Then** the first prints ``No Work has the id `k3m9xr`. Did you mean
  `k3m9xq`?`` and the second the same without the question, and each exits 2.

#### A file that is not a Work

- **Given** an unmarked `p/notes.md`, a path that does not exist, and a file
  outside the Works directory.
- **When** `wio contracts show` runs on each.
- **Then** each prints an error that names the path and the reason that the
  discovery leaf gives for it, the three reasons being different, and exits 2.

#### A shared id

- **Given** two Works with the id `a7b2c4`, titled `Twin` and `Twin two`,
  besides the Work `k3m9xq` that lists `a7b2c4`.
- **When** `wio contracts show a7b2c4` and `wio contracts show k3m9xq` run.
- **Then** the first prints the error of discovery that names both paths and the
  line that says `wio contracts check` shows every problem, and exits 2, and the
  second shows the Work with the lines `After        a7b2c4  Twin` and, below
  it in the same column, `a7b2c4  Twin two`.

### **AC-4** An incomplete tree refuses the command

An error of finding the Works that leaves the tree incomplete refuses it, and an
error of the metadata or the graph does not.

#### Each case

- **Given** a tree with an unreadable Work file elsewhere, a tree with two
  marked files in one directory under `nesting`, and a tree whose Works have an
  undeclared root and a cycle.
- **When** `wio contracts show` runs on a good Work of each.
- **Then** the first two write nothing to standard output, write the error and a
  line that says `wio contracts check` shows every problem, to standard error,
  and exit 2, and the third prints the Work and exits 0.

### **AC-5** `--json` is one object with the same facts and the view

The JSON has the fields in a fixed order and the resolved Markdown as one
string.

#### The child as JSON

- **Given** the Works of AC-1.
- **When** `wio contracts show k3m9xq --json` runs.
- **Then** it prints one object that parses, whose fields are in the order of
  the constraint, with `"parent": "p5n2hv"`, `"depends_on": ["a7b2c4"]`,
  `"resolved_roots": ["wio"]`, `"dependents": []`, the action `define` with
  `"source": "template"` and `"preset": "define-feature"`, the action `deliver`
  with `"source": "contract"`, `"on_demand": false`, `"preset": null` and
  `"stages": ["ship"]`, the action `amend` with `"on_demand": true`,
  `"source": "contract"` and `"stages": []`, and a `view` that holds
  `## Inherited from: Parent (p5n2hv)`.

### **AC-6** Nothing is written, the output is the same, and `json` is not loaded

The command changes no file, two runs print the same bytes, and a run without
`--json` imports neither `json` nor `tomlkit`.

#### Twice and in a fresh interpreter

- **Given** the Works of AC-1 and a hash of each contract, and a new Python
  process.
- **When** `wio contracts show k3m9xq` and the same with `--json` each run
  twice, and in the new process `main(["contracts", "show", "k3m9xq"], stdio)`
  runs and `sys.modules` is read.
- **Then** the two outputs of each are identical, the hash of every contract is
  unchanged, and neither `json` nor `tomlkit` is in `sys.modules`.

## Additional context

- The layout puts the facts first and then the contract.
- `wio contracts list` shows the same overrides in one line for each Work, and
  `show` is where a Work is read in full.
