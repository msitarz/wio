<!-- wio
id = "ms5t0t"
template = "feature.leaf"
roots = ["repo"]
depends_on = ["bgctsc", "jsymcg"]

[actions]
deliver = ["promote-docs", "docs-review"]
-->

# Optional templates

## Purpose

A project must be able to run wio on its contracts without writing a template,
so adopting wio takes a marker and an id per file and a few lines of config.

## Goals

- A project runs wio on its contracts without writing a template.
- A contract without a template takes its default actions from one place in
  the config.
- A contract without a template can still require sections, give its items
  ids and pass sections on to its descendants.
- A project configures its templates and kinds in one table, or leaves it out.
- `wio contracts new` creates a Work without a template.
- An agent's bundle shows a contract's content without the metadata and
  directives that only wio reads.

## Non-Goals

- Splitting `wio contracts` from `wio templates`, which the templates-command
  leaf (`be2081`) does.
- What `shape` means under `flat`, which the hierarchy leaf (`jsymcg`) settles.
- A named file template as the default, which this leaf records for later.
- Moving `shape` into the config, which this leaf records for later.
- `wio init` and `wio contracts adopt`, which this leaf records for later.

## Assumptions

None.

## Mechanisms

- `docs/concepts.md`, section 4 "Templates and kinds", whose subsections "What
  a template is", "From template to contract", "Kinds and entry templates",
  "Directives" and "Checking a contract against its template" state what a
  template gives a contract.
- `docs/concepts.md`, "Anatomy" and "Identity and location" in section 3,
  which state a contract's title and what `wio contracts new` writes.
- `docs/concepts.md`, "What it is" in section 3 and the resolved contract in
  section 11 "The context compiler", which say what a bundle shows of a
  contract.
- `docs/concepts.md`, "Inheritance, computed" in section 5, "Where the pipeline
  comes from" in section 6, "Invariants wio checks", the symbol tables of
  section 2, and section 15 "Open points".
- `docs/v0.1-scope.md`, whose `wio contracts` outcome lists what Create does
  and what Check verifies, and whose list "Not in v0.1" names deferred
  features.
- `GLOSSARY.md`, whose entries Work contract, Template and Kind change.
- `.agents/wio/config.toml`, wio's own config, whose `[kinds]` table moves.

## Constraints

- **Links point back.** This leaf links to the sections of the marked-files
  leaf (`bgctsc`) and the hierarchy leaf (`jsymcg`), which are delivered before
  it, and to no section the templates-command leaf (`be2081`) writes after it;
  that leaf adds the links from its command section to this leaf's. Verified
  by docs-review.

## Visuals

Prose, because the change is a rule, not a structure. The before state is
drawn from `docs/concepts.md` and `docs/v0.1-scope.md` on `main` at commit
`55706d117db746a0269431956c65777c4dfa0afe`.

- **Before:** every contract names a template, which gives its default
  actions, its directives and its kind. Directives are removed from a contract
  at creation and read only from its template. Kinds are declared in `[kinds]`,
  and `wio contracts new` needs a kind.
- **After:** `template` is optional. A contract without one takes its default
  actions from `[works.defaults.actions]` and its directives from its own
  headings. Templates and kinds live in an optional `[templates]` table, and
  `wio contracts new` without a kind writes a bare contract.

## Acceptance criteria

### **AC-1** A contract may name no template

`docs/concepts.md` states that `template` is optional, so a project can run wio
without writing one. It states these rules:

- A contract may leave out `template`; a contract that names a template that
  does not exist is still an error.
- A contract without a template gets the metadata checks of every contract,
  takes its title from its first heading, and has its `##` headings checked
  only by its own directives (AC-3).
- A contract without a template has no `shape`, so the check of its children
  against a `shape` does not apply to it, under either mode.
- The row for `template` in the symbol table of section 2 says it is optional,
  and the table of what a template supplies says what a contract without one
  takes instead.
- "Invariants wio checks" no longer requires every contract to name a
  template.
- `GLOSSARY.md` says that a Work contract follows a template if it names one,
  in its entries Work contract and Template.

### **AC-2** Default actions come from the config

`docs/concepts.md`, in "Where the pipeline comes from", states the default
actions of a contract without a template, so they come from one place. It
states these rules:

- A contract without a template takes its default actions from
  `[works.defaults.actions]`, and its own `[actions]` replace them one action
  at a time, as they replace a template's.
- The defaults are not a template: they have no name, kind, body, directives or
  `shape`, and no contract can name them in `template`.
- They apply only to a contract without a template and are never layered under
  a named template, so every contract has one source of default actions.
- `[works.defaults.actions]` is checked as a contract's `[actions]` is: its
  actions, stage presets and stages exist; an empty list there is the same as
  leaving the action out.
- A contract with neither a template nor defaults needs its own `[actions]`,
  and a Work that resolves to no action is the error "Invariants wio checks"
  already lists.
- `wio contracts show` says where each of a Work's actions comes from: the
  contract, its template or the config defaults.
- The config table of section 2 lists `[works.defaults.actions]`, and the
  import item that the marked-files leaf (`bgctsc`) records links to this
  section for the default actions it needs.

### **AC-3** Directives have one source per contract

`docs/concepts.md`, in "Directives" and "Checking a contract against its
template", states where a contract's directives come from, so a contract
without a template can still be checked. It states these rules:

- A contract's directives come from its template if it names one, and
  otherwise from its own `##` headings, in the same grammar.
- A contract with a template keeps today's rule: its directives are read from
  the template, so a template change reaches every contract that follows it
  and a contract cannot loosen its own checks. A directive comment in such a
  contract is ignored, with a warning that says so.
- A contract without a template may mark its own headings `required`,
  `items>=N`, `pattern=...` and `inherit`, and `wio contracts check` validates
  them as it validates a template's; its `pattern` directives give its item
  ids.
- "From template to contract" still removes the template's directives from a
  contract created from it.

### **AC-4** Every parent can pass sections on

`docs/concepts.md`, in "Inheritance, computed", states which sections an
ancestor passes on, so a parent's constraints reach its leaves whether or not
it names a template. It states these rules:

- An ancestor passes on the sections that its source of directives marks
  `inherit`: its template's directives, or its own headings when it names no
  template.
- An ancestor whose source marks nothing passes nothing on, and the walk goes
  on to the ancestors above it.
- What a descendant inherits does not depend on whether it names a template
  itself.
- Under `flat` no Work has an ancestor, so `inherit` passes nothing on and is
  neither an error nor a warning, linking to the hierarchy leaf's (`jsymcg`)
  section on `flat`.

### **AC-5** `wio contracts new` needs no kind

`docs/concepts.md`, in "Identity and location", and the Create outcome of
`docs/v0.1-scope.md` state what `new` writes without a template, so a project
without templates can create Works. This leaf owns the optional kind and the
bare contract; the signature of `new` is written once, in the command section
of the templates-command leaf (`be2081`). They state these rules:

- `new` may be given no kind; `new <kind>` and `new --template <name>` work as
  before.
- Given neither, `new` writes a bare contract in the comment form, holding
  only the generated `id` and a first heading for the title:

  ```markdown
  <!-- wio
  id = "k3m9xq"
  -->

  # Title
  ```

- `new <kind>` when no kinds are declared is an error that says no kinds are
  declared.
- `--slug`, `--title` and `--root` work as before, and `--parent` follows the
  hierarchy leaf (`jsymcg`), linking to it.

### **AC-6** Templates and kinds live in one optional table

`docs/concepts.md`, in "Kinds and entry templates" and the symbol tables of
section 2, states the `[templates]` table, so a project configures templates
in one place or leaves it out. It states these rules:

- `[templates] dir` is a path relative to the repository root whose default is
  `.agents/wio/templates`; a path that leaves the repository is an error. A
  missing default directory holds no templates; a `[templates] dir` that is
  set and missing, that is not a directory or that is a symbolic link is an
  error.
- The walk of that directory follows these rules of the marked-files leaf
  (`bgctsc`), linking to them: names end in `.md`, matched case-sensitively;
  directories below it whose names start with `.` are skipped; no symbolic
  link is followed; and a file that cannot be read or decoded as UTF-8 is an
  error that names it.
- A file there is a template when its `<!-- wio` block, or `+++` front matter
  with the marker, starts on its first line, as for a Work; any other file is
  ignored.
- The kinds are declared in `[templates.kinds]`, because a kind exists only to
  choose an entry template; both tables are optional.
- A template keeps a required `kind`, and `shape` stays in its metadata.
- A `[kinds]` table left at the top level of the config is an unknown key,
  with the warning every unknown key gets, and no other mention of `[kinds]`
  remains in `docs/concepts.md`, the `name` row of section 2 and section 14
  included.
- The config table of section 2 lists `[templates] dir` and
  `[templates.kinds]` in place of `[kinds]`.
- `.agents/wio/config.toml` declares its kinds in `[templates.kinds]`, with no
  `[kinds]` table left.

### **AC-7** The deferred template designs are recorded for later

The designs the Non-Goals leave out are stated once, so they are neither lost
nor promised for v0.1. The documents state:

- The Open points of `docs/concepts.md` hold a named file template as the
  default, `[works] default_template`, for defaults that need directives, such
  as a section every adopted spec must have, an error together with
  `[works.defaults.actions]`; and moving `shape` into the config beside the
  kinds.
- "Not in v0.1" of `docs/v0.1-scope.md` lists the named default template,
  `wio init`, which writes a minimal config with `[works.defaults.actions]`,
  and `wio contracts adopt`, which adds the marker and a generated id to an
  existing file, linking to their open points.
- The Open points also hold generated integrations with workflows such as
  Kiro, written by `wio init` as config, never as code paths in the engine.

### **AC-8** A bundle leaves out what only wio reads

`docs/concepts.md`, in "What it is" and in the resolved contract of section 11
"The context compiler", states what a bundle shows of a contract, so the agent
reads the contract's content and none of wio's own markup. It states these
rules:

- A bundle shows each contract, and each section it inherits, without its
  metadata block, in the comment form or as `+++` front matter.
- It also leaves out every directive comment at the end of a heading, now that
  a contract without a template may carry directives (AC-3), and those of the
  inherited sections.
- Every other HTML comment stays in the bundle as written: what it says is the
  workflow's, not wio's.
- The Work's id still reaches the agent, through the command that the bundle's
  header names.

## Additional context

- A leaf of [Finding Work contracts in any Markdown file](../README.md)
  (`2fh1ar`), whose AC-2 joins this leaf's default actions with the marked
  files and the `flat` mode.
- A contract without a template can loosen its own checks by editing its own
  directives. That is accepted: such a contract has no template whose checks
  it could escape, and a project that wants checks it cannot loosen writes a
  template.
- It depends on the hierarchy leaf (`jsymcg`) as well as the marked-files leaf,
  so that its links to `flat` and `--parent` point back.
