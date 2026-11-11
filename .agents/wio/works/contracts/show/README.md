<!-- wio
id = "bhrjjs"
template = "feature.leaf"
roots = ["wio"]
depends_on = ["h3jhtw", "sz1zsq"]
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

- The description of an action, which the config holds and `wio config show`
  prints.
- Judging the Work, which `check` does, and the rules that apply to it.
- Explaining the fields of a contract, which a later command may do.

## Assumptions

- **A-1**: The resolve and command leaves are delivered, so the resolved view,
  the hierarchy it builds on, and the group and its table exist.
- **A-2**: `Config` gives the actions in the order the config declares them,
  with `on_demand`, and the stage presets with their stages.
- **A-3**: The `Environment` port gives the working directory, against which a
  path argument is resolved.

## Mechanisms

- A `show` entry in the table of the group, and a function in `wio.contracts`
  that renders a Work, as text or as JSON.
- The resolved view of the resolve leaf, the hierarchy of the hierarchy leaf for
  the parent, the resolved roots, the dependencies and the dependents, and the
  explanation of why a path is not a Work from the discovery leaf.
- `Config` for the actions and stage presets, the `Environment` port for the
  working directory, `closest_key` for a mistyped id, and `json` for `--json`
  only.
- The names and the signatures above are provisional, for the architecture stage
  to decide.

## Constraints

- **The layout is facts, actions, a rule, then the view.** The first line is
  `Work <id>  <title>`. The facts follow, each line written only when it has
  something to say and in this order: `Path`, `Template`, `Parent`, `Roots`,
  `After`, `Needed by`. The values start at one column, and a second dependency
  or dependent is on the next line, in that column. Then a blank line, the
  `Actions` block, a blank line, a line of `----`, a blank line and the
  resolved view, exactly as the resolve leaf renders it.
- **Roots show what they resolve to.** A Work that lists `@descendants` shows
  its roots as written, an arrow and the resolved roots. Any other Work shows
  them as written.
- **Actions are in the order of the config.** Each line is the action, the stage
  preset it names and where it comes from, written `(from the template)`,
  `(from the contract)` or `(from the config defaults)`, and `on demand,` before
  that for an action the config marks on demand. A list of stages has no preset
  name. The stages follow on a line of their own, joined by a comma and a space.
  An action that the contract empties is `removed (by the contract)`, and a name
  that the config does not declare is printed as written.
- **A path or an id.** An argument that contains `/` or ends in `.md` is a path,
  resolved against the working directory, and any other is an id.
- **Mistakes are errors of the user.** An id that no Work has names the id and
  the closest one when there is one, a shared id is refused with the error of
  discovery, and a file that is not a Work names the reason. Each exits 2.
- **Discovery errors refuse the command.** A tree with an error of finding the
  Works shows nothing, writes the errors, says that `wio contracts check` shows
  every problem, and exits 2. Errors of the metadata or the graph do not stop
  it.
- **JSON is one object.** It has `id`, `title`, `path`, `template`, `parent`,
  `roots`, `resolved_roots`, `depends_on`, `dependents`, `actions` and `view`,
  in that order. Each action has `name`, `source`, `on_demand`, `preset` and
  `stages`, `view` is the resolved Markdown as one string, and `title`,
  `template`, `parent` and `preset` are `null` when there is none.
- **The output is deterministic and nothing is written.** `json` is imported
  only for `--json`.

## Acceptance criteria

### **AC-1** A Work is shown with its facts, its actions and its resolved contract

The output is the facts, the actions with their sources, a rule and the resolved
view.

#### A child with an override

- **Given** `hierarchy = "nesting"`, a config that declares the actions
  `define`, `deliver` and `amend`, with `amend` on demand, and the stage presets
  `define-feature` of `define` and `review-contract` and `amend-contract` of
  `amend`; a Work `p5n2hv` titled `Parent` at `p/README.md`; a Work `a7b2c4`
  titled `Sibling` at `p/s/README.md`; and a Work `k3m9xq` titled `Child` at
  `p/c/README.md` from the template `feature.leaf`, whose actions are
  `define = "define-feature"`, `deliver = ["build"]` and
  `amend = "amend-contract"`, with `roots = ["wio"]`, `depends_on = ["a7b2c4"]`
  and its own `[actions]` of `deliver = ["ship"]` and `amend = []`. Its body is
  `# Child`, `## Purpose` and the line `Own text.`, and `Parent` has an
  inheritable `## Glossary` with the line `- **Term**: a word.`.
- **When** `wio contracts show k3m9xq` runs.
- **Then** it prints exactly this, and exits 0:

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

### **AC-2** Roots resolve, dependents are listed and flat has no relatives

`@descendants` is shown with what it resolves to, the Works that depend on a
Work are listed, and under `flat` there is no parent and nothing is inherited.

#### A parent and its dependents

- **Given** the Works of AC-1 with `Parent` having
  `roots = ["e2e", "@descendants"]`, a Work `k5m8ps` titled `Other` that also
  lists `a7b2c4`, and the Child's `roots` being `["api"]`.
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

A path is resolved against the working directory, an unknown id and a file that
is not a Work are errors that say what is wrong.

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
- **Then** each prints an error that names the path and the reason it is not a
  Work, and exits 2.

#### A shared id

- **Given** two Works with the id `k3m9xq`.
- **When** `wio contracts show k3m9xq` runs.
- **Then** it prints the error of discovery that names both paths and exits 2.

### **AC-4** Discovery errors refuse the command

An error of finding the Works refuses it, and an error of the metadata or the
graph does not.

#### Each case

- **Given** a tree with an unreadable Work file elsewhere, and another tree
  whose Works have an undeclared root and a cycle.
- **When** `wio contracts show` runs on a good Work of each.
- **Then** the first writes nothing to standard output, writes the error and a
  line that says `wio contracts check` shows every problem, to standard error,
  and exits 2, and the second prints the Work and exits 0.

### **AC-5** `--json` is one object with the same facts and the view

The JSON has the fields in a fixed order and the resolved Markdown as one
string.

#### The child as JSON

- **Given** the Works of AC-1.
- **When** `wio contracts show k3m9xq --json` runs.
- **Then** it prints one object that parses, whose fields are in the order of
  the constraint, with `"parent": "p5n2hv"`, `"resolved_roots": ["wio"]`,
  `"dependents": []`, the action `deliver` with `"source": "contract"`,
  `"preset": null` and `"stages": ["ship"]`, the action `amend` with
  `"stages": []`, and a `view` that holds `## Inherited from: Parent (p5n2hv)`.

### **AC-6** Nothing is written and the output is the same every time

The command changes no file, and two runs print the same bytes.

#### Twice

- **Given** the Works of AC-1 and a hash of each contract.
- **When** `wio contracts show k3m9xq` and the same with `--json` each run
  twice.
- **Then** the two outputs of each are identical, and the hash of every contract
  is unchanged.

## Additional context

- The layout is the one the driver approved in the interview: the facts first,
  as the header of a bundle will be, then the contract.
- `wio contracts list` shows the same overrides in one line for each Work, and
  `show` is where a Work is read in full.
