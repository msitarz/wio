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

- **A-1**: No other tool writes `<!-- wio` followed by whitespace on a
  Markdown file's first line, or a `wio` key in `+++` front matter, so the
  marked forms are wio's alone.

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

- **Links point back.** This leaf is delivered before its siblings, so its
  sections link to no section a sibling writes; each sibling that depends on
  it adds the links between its own sections and this leaf's. Verified by
  docs-review here, and by each sibling's docs-review for its links.

## Visuals

Prose, because the change is a rule, not a structure. The before state is
drawn from `docs/concepts.md` and `docs/v0.1-scope.md` on `main` at commit
`55706d117db746a0269431956c65777c4dfa0afe`.

- **Before:** a Work is a directory whose `README.md` holds a `wio` block, in
  `.agents/wio/works/`, a path that "will be configurable". A directory without
  a contract between two Works is an error. `+++` front matter makes a Work
  without any marker.
- **After:** a Work is any `.md` file under `[works] dir` whose metadata block
  starts on its first line, after an optional byte-order mark: a `<!-- wio`
  comment, or `+++` front matter with `wio = 1`. `wio contracts show`, given a
  file, says why it is not a Work.

## Acceptance criteria

### **AC-1** Any marked file under the Works directory is a Work

`docs/concepts.md` states which files are Works, so a project can name and
place its contracts as it likes. It states these rules:

- A Work is a file whose name ends in `.md`, matched case-sensitively, under
  the Works directory, whose metadata block starts on the file's first line: a
  `<!-- wio` comment, where `wio` is followed by whitespace or the end of the
  line, or `+++` front matter that holds the marker. A leading UTF-8
  byte-order mark is skipped. A block that starts on any later line, a blank
  line included, does not make the file a Work.
- The file's name and the directories above it play no part in whether it is a
  Work.
- The Works directory is `[works] dir`, a path relative to the repository root
  whose default is `.agents/wio/works`; a path that leaves the repository is an
  error, as for root paths.
- The symbol tables of section 2 say the same, including a `[works] dir` entry
  in the config table, and no longer mention a directory's `README.md`.
- `GLOSSARY.md` defines Work and Work contract by the marked file, and adds
  Marked file, with the first-line rule, and Marker.

### **AC-2** The walk finds every marked file and nothing else

`docs/concepts.md` states how wio finds the files it checks, so its result does
not depend on a setting or on git. It states these rules:

- wio walks the Works directory recursively and reads every `.md` file in it.
- Below the Works directory, it skips directories whose names start with `.`,
  and it follows no symbolic link, to a directory or to a file, so every Work
  has exactly one path.
- A Works directory that does not exist holds no Works when it is the default,
  and is an error when `[works] dir` sets it; a Works directory that is not a
  directory, or is a symbolic link, is an error.
- A `.md` file that cannot be read or decoded as UTF-8 is an error that names
  the file.
- It reads the working tree, so a Work that is not committed yet is found, and
  it consults neither `.gitignore` nor a glob setting.

### **AC-3** The marker tells wio's front matter from any other

`docs/concepts.md` states the marker, so front matter that another tool wrote
is never read as a Work and a Work wio cannot read is never dropped silently.
It states these rules:

- The marker is `wio = 1`, whose value is the version of the metadata format.
- In `+++` front matter the marker is required, because those delimiters are
  not specific to wio; front matter without it is silently not a Work.
- In the comment form the marker is optional, because `<!-- wio` already marks
  the file and implies version 1; a marker given there is checked.
- A marker with a version wio does not know, such as `2`, or of the wrong type,
  such as `true` or `"1"`, is an error that names the versions wio knows.
- A `<!-- wio` block that does not close, or whose TOML does not parse, is an
  error that names the file. `+++` front matter that does not close or parse
  is the same error when its text contains `wio =`, and is otherwise silently
  not a Work, because wio cannot tell it from another tool's.
- The section says how a forgotten marker still shows: a `depends_on` that
  names the missing Work's id is an unknown id, and the Work is absent from
  the list of Works.

### **AC-4** wio says why a file is not a Work

`docs/concepts.md` and the outcome of Show in `docs/v0.1-scope.md` state the
reasons `wio contracts show` gives when it is given a file that is not a Work,
so a person or an agent can learn why it is not. They state at least these
reasons, and the siblings may add their own:

- the path does not exist, or is not a file;
- the name does not end in `.md`;
- the file has no metadata block, or its block does not start on the first
  line;
- its `+++` front matter has no readable marker;
- the path is outside the Works directory, or under a directory below it whose
  name starts with `.`;
- the path is, or runs through, a symbolic link.

An unreadable `<!-- wio` block, or unreadable front matter that contains
`wio =`, is not among these reasons, because it is the error AC-3 states. The
reasons are required; their exact wording is provisional.

### **AC-5** Importing specs without a marker is recorded for later

The deferred import item, which the Non-Goals exclude from this leaf, is stated
once, so it is neither lost nor promised for v0.1. The documents state:

- The Open points of `docs/concepts.md` state one item for importing existing
  specs: a mode that takes every `.md` file with front matter and an `id` as a
  Work, configurable id generation, and an id format that admits ids such as
  `SPEC-012`.
- The item says that the mode needs default actions for contracts without a
  template.
- "Not in v0.1" of `docs/v0.1-scope.md` lists the item, linking to the open
  point.

## Additional context

- A leaf of [Finding Work contracts in any Markdown file](../README.md)
  (`2fh1ar`), whose constraints it inherits and whose AC-1 and AC-3 join this
  leaf's rules with those of its siblings.
- There is no glob setting because the marker already rules out foreign files;
  one can be added later without breaking anything.
