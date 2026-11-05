<!-- wio
id = "be2081"
template = "feature.draft"
roots = []
depends_on = ["jsymcg", "ms5t0t", "41wfqk"]
-->

# The wio templates command

## Purpose

People and agents must find contracts under `wio contracts` and templates under
`wio templates`, because each command should cover only the term of wio that
it names.

## Intent

Settled with the driver on 2026-11-05. A leaf of `2fh1ar`; planned roots:
`repo` and `wio`.

- **The split**, which follows `wio rules` having a command of its own:

  | Today | After |
  | --- | --- |
  | `wio contracts new <kind>` | `wio contracts new [<kind>]` |
  | `wio contracts list` (templates) | `wio templates list` |
  | `wio contracts template <name> [--work <id>]` | `wio templates show <name> [--work <id>]` |
  | — | `wio contracts list` (Works) |
  | `wio contracts check` | `wio contracts check`, without template checks |
  | — | `wio templates check` |
  | `wio contracts show <id>` | `wio contracts show <id or file>` |
  | `wio contracts tree` | folded into `wio contracts list` |

- **`wio contracts list`** prints each Work's id, title, path, template, roots
  and dependencies, and no status. Under `nesting` it indents children below
  their parents; under `flat`, the default, it is a list.
- **`wio templates show`** keeps what `wio contracts template` does, the
  skeleton with `--work` and `--keep`; `show` matches `wio contracts show`
  instead of a noun used as a verb.
- **`wio templates check`** checks the templates themselves: their keys, kinds
  and directives. `wio contracts check` still reports a contract that names a
  missing or broken template, without checking the template again.
- **A seventh component.** Every component describes one subcommand
  (`src/wio/cli/table.py`), so `wio.templates` becomes a component: the
  `Component` type in `src/wio/cli/table.py`, the "Component" entry of
  `src/wio/GLOSSARY.md`, `src/wio/README.md` and `tach.toml` change. Reading
  templates serves both components, so it lives in a shared layer, probably
  `wio.formats`, since components do not import one another.
- It depends on the command table (`41wfqk`), which owns the `Component` type.
- A guarantee of this leaf (moved here from the parent's review): the
  documents state the two commands with no subcommand in common, and no
  mention of a removed form, such as `wio contracts template` or
  `wio contracts tree`, is left.
- **Links back.** The `wio contracts show <id or file>` signature, and how a
  path is told from an id (a `/` or a `.md` ending), are this leaf's, and
  link to the reasons the marked-files leaf (`bgctsc`) states.
- Other documents that name `wio contracts template` change with it:
  `docs/concepts.md`, `docs/workflow.md`, `docs/split-exercises.md` and the
  define skill's steps in `docs/v0.1-scope.md`.
