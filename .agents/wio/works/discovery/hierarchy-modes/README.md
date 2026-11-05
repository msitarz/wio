<!-- wio
id = "jsymcg"
template = "feature.leaf"
roots = ["repo"]
depends_on = ["bgctsc"]

[actions]
deliver = ["promote-docs", "docs-review"]
-->

# Hierarchy modes

## Purpose

Most spec workflows keep their specs flat, so wio must work without a Work
hierarchy by default and derive one from directories only for a project that
asks for it.

## Goals

- A project with flat specs uses wio with no hierarchy, without setting
  anything.
- A project that wants parents and children gets them from its directories by
  setting one key.
- wio's own repository keeps its parents and children.
- A person or an agent learns why a file breaks the rules of the `nesting` mode.
- `wio contracts new` writes a Work where the workflow's convention puts it,
  and otherwise into a directory of its own for its artifacts.
- A project can switch modes without migrating a file.

## Non-Goals

- Which files are Works, which the marked-files leaf (`bgctsc`) states.
- A hierarchy given by a `parent` field, or a config default for the path that
  `wio contracts new` writes, which this leaf records as open points.
- Changing what a parent does with its children, such as inheritance or
  `@descendants`, beyond saying what each mode gives them.

## Assumptions

- **A-1**: In the spec tools the parent surveys, the files of one directory are
  parts of one unit and never a hierarchy of units, so a file beside a Work
  should never be its child.

## Mechanisms

- `docs/concepts.md`, section 5 "Nesting", whose subsections "Parent and leaf",
  "Roots of a Work", "Inheritance, computed" and "Dependencies" state the
  hierarchy and what it gives.
- `docs/concepts.md`, "Invariants wio checks" in section 6, "Identity and
  location" in section 3 for `wio contracts new`, the config table of section
  2, and section 15 "Open points".
- `docs/v0.1-scope.md`, whose `wio contracts` outcome lists what Create does
  and what Check verifies, and whose list "Not in v0.1" names deferred
  features.
- `GLOSSARY.md`, whose entries Parent and Leaf change and which gains Hierarchy
  mode and Sibling split.
- `docs/concepts.md` "Splitting" and "Dependencies", and
  `docs/split-exercises.md`, which speak of flat splits.
- `.agents/wio/config.toml`, wio's own config, which sets the mode.

## Constraints

- **Links point back.** This leaf's sections link to those of the marked-files
  leaf (`bgctsc`), which is delivered before it, and to no section that the
  templates-command leaf (`be2081`) writes after it; that leaf adds the links
  from its command section to this leaf's. Verified by docs-review.

## Visuals

Prose, because the change is a rule, not a structure. The before state is
drawn from `docs/concepts.md` and `docs/v0.1-scope.md` on `main` at commit
`55706d117db746a0269431956c65777c4dfa0afe`.

- **Before:** the directory tree is always the hierarchy. A child is a
  subdirectory whose `README.md` is a Work, and every directory between the
  Works directory and a Work must be a Work.
- **After:** `[works] hierarchy` chooses. Under `flat`, the default, no Work
  has a parent. Under `nesting`, a directory holds at most one Work, and a
  Work's parent is the Work of the nearest directory above it; plain
  directories only group files in both modes.

## Acceptance criteria

### **AC-1** One key chooses the hierarchy

`docs/concepts.md` states the setting, so a project chooses whether directories
give its Works parents and children. It states these rules:

- `[works] hierarchy` is `"flat"` or `"nesting"`, two exclusive modes; a
  missing key means `"flat"`.
- Any other value, or a value of another type, is a config error, which
  "Invariants wio checks" and the Check outcome of `docs/v0.1-scope.md` list.
- The config table of section 2 lists the key with both values and its default.
- `GLOSSARY.md` adds Hierarchy mode as the parent's Glossary defines it, and
  its entries Parent and Leaf say that only `nesting` gives a Work children.
- `.agents/wio/config.toml` sets `hierarchy = "nesting"` in a `[works]` table.

### **AC-2** Under `nesting`, directories are the hierarchy

`docs/concepts.md`, in "Parent and leaf" and in the "Directory layout" row of
section 2, states how `nesting` derives parents and children, so the hierarchy
is still computed and never stored. It states these rules:

- A directory holds at most one Work, in a marked file of any name.
- When a directory holds two or more marked files, none of them is a Work, and
  `wio contracts check` reports one error that names them all.
- A marked file directly in the Works directory is not a Work, because it
  would be the parent of every Work, and `wio contracts check` reports it as an
  error. The Works directory may hold an unmarked file, such as a `README.md`
  index for people.
- A Work's parent is the Work of the nearest directory above its own that
  holds exactly one Work; a Work's children are the Works whose parent it is.
  A directory whose marked files collide therefore gives no parent, until the
  collision is resolved.
- A file beside a Work, in the same directory, is never its child.
- There is still no `parent` field and no `children` list.
- What makes a file a Work links to the section of the marked-files leaf
  (`bgctsc`).
- "Invariants wio checks" in `docs/concepts.md` and the Check outcome of
  `docs/v0.1-scope.md` list both errors.

### **AC-3** Under `flat`, no Work has a parent

`docs/concepts.md` states what `flat` gives, so a flat project meets no rule
that only a hierarchy needs. It states these rules:

- No Work has a parent or children, and any number of Works may share a
  directory.
- `@descendants` in `roots` resolves to nothing, and the existing warning for
  a Work without children that lists it applies in both modes; the config's
  `@descendants:<action>` in `invalidated_by` matches nothing and warns about
  nothing.
- No Work inherits a section, because no Work has an ancestor.
- The cycle check sees only `depends_on`, because no parent depends on
  children.
- The template's `shape` is not checked, because a `parent` shape could never
  be met; what `shape` means is the workflow's. This leaf settles what `shape`
  means under `flat`; where `shape` lives is the optional-templates leaf's.
- What `new --parent` does under `flat` is AC-6's.

### **AC-4** The no-gap rule is gone in both modes

The documents no longer require a Work between two Works, so a project can
group its spec files in plain directories. They state:

- "Parent and leaf" in `docs/concepts.md` says that a directory between the
  Works directory and a Work need not be a Work, in either mode, and that a
  plain directory only groups files.
- Neither "Invariants wio checks" in `docs/concepts.md` nor the Check outcome
  of `docs/v0.1-scope.md` lists a check that every such directory is a Work.

### **AC-5** wio says why a file breaks the `nesting` rules

`docs/concepts.md` and the outcome of Show in `docs/v0.1-scope.md` state the
reasons `wio contracts show` adds under `nesting`, so a person or an agent can
learn why a file is not a Work there. They state:

- each marked file in a directory that holds another is not a Work, and its
  reason names the others;
- a marked file directly in the Works directory is not a Work, and the reason
  says why;
- both reasons are added to the reasons of the marked-files leaf (`bgctsc`),
  linking to them; the exact wording is provisional.

### **AC-6** `wio contracts new` writes where the workflow says

`docs/concepts.md`, in "Identity and location", and the Create outcome of
`docs/v0.1-scope.md` state where `new` writes a Work in each mode, so a
workflow can keep its own file names and every other Work gets a directory for
its artifacts. They state these rules:

- By default `new` writes `<slug>/README.md`, in both modes, because the
  directory gives the Work's artifacts a home and forges render a `README.md`.
- `--path <path>` writes the Work at that path instead, relative to the
  repository root, such as `spec.md` in a directory of its own or a dated file
  in a flat folder, so the agent can follow the workflow's convention. It
  creates the directories the path needs. An absolute path, or one that
  contains `..`, is an error.
- The path must name a file that would be a Work by the rules of the
  marked-files leaf (`bgctsc`), linking to them. A path that exists already is
  an error, so a Work is never overwritten.
- `--path` and `--slug` exclude each other.
- Under `nesting`, the path decides the parent, so `--path` and `--parent`
  exclude each other; a path in a directory that already holds a marked file,
  or directly in the Works directory, is an error.
- `--parent` creates the Work inside its parent's directory under `nesting`,
  and is an error under `flat`.
- A Work a person writes or moves may have any name; only the default of `new`
  uses `README.md`.

### **AC-7** Switching modes migrates nothing

`docs/concepts.md` states what a change of mode does, so a project can switch
without fear for its history. It states:

- Changing `[works] hierarchy` rewrites no file, and keeps every record and
  every `depends_on`, because they refer to ids.
- What follows from the hierarchy changes with it: parents and children, the
  implicit dependency of a parent on its children, the inherited sections and
  what `@descendants` and `@descendants:<action>` resolve to.
- Switching to `nesting` makes errors of each directory that holds two marked
  files and of each marked file directly in the Works directory, until they
  are moved.

### **AC-8** The deferred hierarchy designs are recorded for later

The two designs the Non-Goals leave out are stated once, so they are neither
lost nor promised for v0.1. The documents state:

- The Open points of `docs/concepts.md` hold a third exclusive mode, where a
  `parent` id field gives the hierarchy and directories mean nothing, never
  mixed with `nesting`, and a config default for the path `new` writes, such
  as `[works] new_path = "{slug}/spec.md"`, whose key and placeholder are
  provisional, so that people and agents need not pass `--path` each time.
- The open point on the `parent` mode notes that a `parent` key already exists
  in some tools' front matter, such as MADR's for Jekyll navigation, as the
  parent's survey reports (its A-3).
- "Not in v0.1" of `docs/v0.1-scope.md` lists both, marking the config default
  for v0.2, and links to the open points.

### **AC-9** A sibling split is not the `flat` mode

The documents keep "flat" for the mode, so a reader never confuses it with a
way of splitting a Work. They state:

- What the documents called a flat split is a **sibling split** in
  "Splitting" and "Dependencies" of `docs/concepts.md`, in its Open points,
  in "Not in v0.1" of `docs/v0.1-scope.md` and in `docs/split-exercises.md`.
- `GLOSSARY.md` defines Sibling split as splitting a Work into sibling Works,
  ordered by `depends_on`, instead of into its children, which both modes
  allow, and says it is not the `flat` mode.
- No document uses "flat" for anything about Works except the mode.

## Additional context

- A leaf of [Finding Work contracts in any Markdown file](../README.md)
  (`2fh1ar`), whose AC-3 joins this leaf's `nesting` rules with those of its
  siblings over wio's own Works.
- The `nesting` mode keeps the hierarchy the documents describe today, so
  wio's own Works need no change.
