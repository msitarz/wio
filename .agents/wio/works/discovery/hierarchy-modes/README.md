<!-- wio
id = "jsymcg"
template = "feature.draft"
roots = []
depends_on = ["bgctsc"]
-->

# Hierarchy modes

## Purpose

Most spec workflows keep their specs flat, so wio must work without a Work
hierarchy by default and derive one from directories only for a project that
asks for it.

## Intent

Settled with the driver on 2026-11-05. A leaf of `2fh1ar`; planned roots:
`repo`.

- **The setting.** `[works] hierarchy = "flat" | "nesting"`, two exclusive
  modes. `flat` is the default; wio's own `.agents/wio/config.toml` sets
  `nesting`, a guarantee of this leaf (moved here from the parent's review).
- **`nesting`** keeps the hierarchy that the documents describe today, with
  directories as the hierarchy:
  - a directory holds at most one Work, in a marked `.md` file of any name; two
    marked files in one directory are an error naming both. A file beside a
    Work is never its child, unlike Hugo or Docusaurus sections, because in
    spec tools the files of one directory are parts of one unit;
  - a Work's parent is the Work of the nearest directory above it that holds
    one; unmarked directories in between only group files;
  - no Work file sits directly in the Works directory, because it would be the
    parent of every Work; the Works directory may still hold an unmarked
    `README.md`, such as an index for people;
  - `wio contracts show <file>` names these as the reasons a file is not a
    Work, beside those of the marked-files leaf (`bgctsc`).
- **`flat`**: no Work has a parent or children.
  - Any number of Works may share a directory.
  - `@descendants` is empty, and there is no implicit dependency of a parent on
    its children in the cycle check; only `depends_on` remains.
  - The template's `shape` is not checked, since a `parent` shape could never
    be satisfied and its warning never cleared. What `shape` means is the
    workflow's business.
  - `wio contracts new --parent` is an error.
- **`wio contracts new`** writes `<slug>/README.md` in both modes, because a
  directory gives the Work's artifacts a home and forges render a `README.md`.
  Files a person writes or moves may have any name.
- **Open points** for `docs/concepts.md`:
  - a third exclusive mode, perhaps in v0.2, where a `parent` id field gives the
    hierarchy and directories mean nothing; never mixed with `nesting`, so the
    two cannot disagree;
  - a configurable file name or layout for `wio contracts new`, such as
    `spec.md` or `<slug>.md`, possibly in v0.2.
