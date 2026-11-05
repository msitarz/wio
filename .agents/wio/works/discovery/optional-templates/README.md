<!-- wio
id = "ms5t0t"
template = "feature.draft"
roots = []
depends_on = ["bgctsc"]
-->

# Optional templates

## Purpose

A project must be able to run wio on its contracts without writing a template,
so adopting wio takes a marker and an id per file and a few lines of config.

## Intent

Settled with the driver on 2026-11-05. A leaf of `2fh1ar`; planned roots:
`repo`.

- **`template` becomes optional** in a contract.
- **Default actions in config.** A contract without `template` takes its
  default actions from `[works.defaults.actions]`, such as
  `deliver = ["implementation"]`. Its own `[actions]` replace them one action
  at a time, as they replace a template's.
  - The defaults are not a template: they have no name, kind, body, directives
    or `shape`, a contract cannot name them in `template`, and
    `wio templates list` does not show them. The name `defaults` says so.
  - They apply only to a contract without `template`, and are never layered
    under a named template, so each contract has one source of defaults.
  - With neither a template nor defaults, a contract needs its own `[actions]`,
    and `wio contracts check` reports a Work with no actions.
  - `wio contracts show` says where each action comes from: the contract, its
    template or the config defaults.
- **A contract without a template** gets only the metadata checks: no required
  sections, no item ids, no inheritable sections.
- **`wio contracts new [<kind>]`**, the kind optional. `new <kind>` and
  `new --template <name>` work as today. With neither, it writes a bare
  contract in the comment form, which marks itself and which forges hide:

  ```markdown
  <!-- wio
  id = "k3m9xq"
  -->

  # Title
  ```

  `--slug`, `--title`, `--root` and `--parent` (in `nesting` only) work as
  before.
- **The templates table.** `[templates] dir`, relative to the repository root
  with `.agents/wio/templates` as its default, and `[kinds]` moves to
  `[templates.kinds]`, because a kind exists only to choose an entry template.
  Both are optional: a project without templates has no `[templates]` table.
  Templates keep a required `kind`. wio's own `.agents/wio/config.toml`
  declares its kinds in `[templates.kinds]`, with no `[kinds]` table left, a
  guarantee of this leaf (moved here from the parent's review).
- **Open points** for `docs/concepts.md`:
  - a named file template as the default, `[works] default_template`, for
    defaults that need directives, such as a section required in every
    adopted spec; setting it together with `[works.defaults]` would be an
    error;
  - where a template's `shape` lives and how it relates to wio now: it stays in
    the template's metadata, or moves to config beside the kinds, such as a
    table `[templates.kinds.<name>]` holding the entry template and the
    shapes; and what `shape` still means when the hierarchy is `flat`, where it
    is not checked. The define stage settles it with the driver or records it
    as open;
  - the roadmap of the parent (`2fh1ar`): `wio init` and
    `wio contracts adopt` in v0.2, and generated integrations with workflows
    such as Kiro later.
