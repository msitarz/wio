<!-- wio
id = "bgctsc"
template = "feature.leaf"
roots = ["repo"]
depends_on = []

[actions]
deliver = ["promote-docs", "docs-review"]
-->

# Marked files are Works

## Purpose

wio must find a project's Work contracts wherever they sit in the Works
directory and whatever they are named, and must never mistake another tool's
Markdown file for a Work.

## Goals

- A project makes any `.md` file under its Works directory a Work by giving it
  a metadata block, whatever the file's name or directory.
- A project chooses where its Works directory is.
- Another tool's Markdown file, front matter included, is never taken for a
  Work.
- A person or an agent can ask wio why a file is not a Work and get the reason.

## Non-Goals

- How directories relate Works, which the hierarchy leaf (`jsymcg`) states.
- What a contract without a template gets, which the optional-templates leaf
  (`ms5t0t`) states.
- Changing the form of ids or how they are generated.
- Reading YAML front matter, which is expected in v0.2 and takes the same
  marker.
- Importing specs that carry no marker, which this leaf records as an open
  point.

## Assumptions

None.

## Mechanisms

- `docs/concepts.md`, section 2 "What wio reads", whose symbol tables list what
  makes a file a Work and the Works directory.
- `docs/concepts.md`, section 3 "Work contract", whose subsections "What it
  is", "Anatomy", "Metadata forms" and "Identity and location" state the
  contract model, and section 15 "Open points".
- `docs/v0.1-scope.md`, whose `wio contracts` outcome lists what Check verifies
  and what Show prints, and whose list "Not in v0.1" names deferred features.
- `GLOSSARY.md`, whose entries Work and Work contract change and which gains
  Marked file and Marker.

## Constraints

- **Rules of the engine.** What makes a file a Work is stated once, as a rule
  of the engine in `docs/concepts.md`, so every component that reads contracts
  applies the same rule and links to it. Verified by docs-review.

## Visuals

Prose, because the change is a rule, not a structure. The before state is
drawn from `docs/concepts.md` and `docs/v0.1-scope.md` on `main` at commit
`55706d117db746a0269431956c65777c4dfa0afe`.

- **Before:** a Work is a directory whose `README.md` holds a `wio` block, in
  `.agents/wio/works/`, a path that "will be configurable". A directory without
  a contract between two Works is an error. `+++` front matter makes a Work
  without any marker.
- **After:** a Work is any `.md` file under `[works] dir` whose metadata block
  starts on its first line: a `<!-- wio` comment, or `+++` front matter with
  `wio = 1`. Plain directories only group files. `wio contracts show <file>`
  says why a file is not a Work.

## Acceptance criteria

### **AC-1** Any marked file under the Works directory is a Work

`docs/concepts.md` states which files are Works, so a project can name and
place its contracts as it likes.

- A Work is a `.md` file under the Works directory whose metadata block starts
  on the file's first line, in the comment form `<!-- wio` or as `+++` front
  matter that holds the marker. A block that starts on any later line, a blank
  line included, does not make the file a Work.
- The file's name and the directories above it play no part in whether it is a
  Work.
- The Works directory is `[works] dir`, a path relative to the repository root
  whose default is `.agents/wio/works`; a path that leaves the repository is an
  error, as for root paths.
- The symbol tables of section 2 say the same, including a `[works] dir` entry
  in the config table, and no longer mention a directory's `README.md`.
- `GLOSSARY.md` defines Work and Work contract by the marked file, and adds
  Marked file and Marker as the parent's Glossary defines them.

### **AC-2** The walk finds every marked file and nothing else

`docs/concepts.md` states how wio finds the files it checks, so its result does
not depend on a setting or on git.

- wio walks the Works directory recursively and reads every `*.md` file in it.
- It skips directories whose names start with `.`, and it follows no symbolic
  link, to a directory or to a file, so every Work has exactly one path.
- It reads the working tree, so a Work that is not committed yet is found, and
  it consults neither `.gitignore` nor a glob setting.
- A directory between the Works directory and a Work need not be a Work: the
  no-gap rule is gone from `docs/concepts.md` and from the checks that
  `docs/v0.1-scope.md` lists, and how directories relate Works links to the
  section the hierarchy leaf (`jsymcg`) writes.

### **AC-3** The marker tells wio's front matter from any other

`docs/concepts.md` states the marker, so front matter that another tool wrote
is never read as a Work and a Work wio cannot read is never dropped silently.

- The marker is `wio = 1`, whose value is the version of the metadata format.
- In `+++` front matter the marker is required, because those delimiters are
  not specific to wio; front matter without it is silently not a Work.
- In the comment form the marker is optional, because `<!-- wio` already marks
  the file and implies version 1; a marker given there is checked.
- A marker with a version wio does not know, such as `2`, or of the wrong type,
  such as `true` or `"1"`, is an error that names the versions wio knows.
- The section says how a forgotten marker still shows: a `depends_on` that
  names the missing Work's id is an unknown id, and the Work is absent from
  the list of Works.

### **AC-4** wio says why a file is not a Work

`docs/v0.1-scope.md` and `docs/concepts.md` state that `wio contracts show`
takes a file, so a person or an agent can learn why a file is not a Work.

- `wio contracts show` takes a Work's id or a file's path; an argument that
  contains `/` or ends in `.md` is a path.
- For a file that is a Work it shows that Work, as it does for its id.
- For a file that is not a Work it fails and names the reason: no metadata
  block, a block that does not start on the first line, `+++` front matter
  without the marker, a path outside the Works directory, a path under a
  directory whose name starts with `.`, or a symbolic link.
- The reasons the hierarchy modes add link to the section of the hierarchy leaf
  (`jsymcg`) instead of being listed here, and the rest of `wio contracts`
  links to the command section that the templates-command leaf (`be2081`)
  writes.

### **AC-5** Importing specs without a marker is recorded for later

The deferred import item is stated once, so it is neither lost nor promised for
v0.1.

- The Open points of `docs/concepts.md` state one item for importing existing
  specs: a mode that takes every `.md` file with front matter and an `id` as a
  Work, configurable id generation, and an id format that admits ids such as
  `SPEC-012`.
- The item says that the mode needs default actions, and links to the section
  on them that the optional-templates leaf (`ms5t0t`) writes.
- "Not in v0.1" of `docs/v0.1-scope.md` lists the item, linking to the open
  point.

## Additional context

- A leaf of [Finding Work contracts in any Markdown file](../README.md)
  (`2fh1ar`), whose constraints it inherits and whose AC-1 and AC-3 join this
  leaf's rules with those of its siblings.
- Reading only the start of each file keeps the walk cheap, because a file whose
  first line opens no block is ruled out at once.
