<!-- wio
id = "2fh1ar"
template = "feature.draft"
roots = []
depends_on = []
-->

# Finding Work contracts in any Markdown file

## Purpose

A project with its own spec files must be able to adopt wio by marking those
files, without moving them into one directory per Work, naming them `README.md`
or writing templates first.

## Intent

Settled with the driver in a design brainstorm on 2026-11-05. The design
documents (`docs/concepts.md`, `docs/v0.1-scope.md`, `docs/workflow.md`,
`GLOSSARY.md`) still describe the old model; this Work changes them before any
component that reads contracts is implemented.

- Planned shape: a `feature.parent` with four leaves, delivered as children of
  this directory in the order their `depends_on` gives:
  - **Marked files are Works** (`bgctsc`): which files are Works, and the
    `wio = 1` marker.
  - **Hierarchy modes** (`jsymcg`): `[works] hierarchy = "flat" | "nesting"`.
  - **Optional templates** (`ms5t0t`): `template` becomes optional, with
    default actions in config.
  - **The `wio templates` command** (`be2081`): templates leave
    `wio contracts` for a command of their own.
- Planned roots: `@descendants`.
- The integration stage judges that the documents read as one design once the
  four leaves are delivered: no section still says that a Work is a directory
  whose `README.md` is its contract, that `template` is required, or that
  `wio contracts` lists templates.
- Common spec layouts the design should admit without restructuring: Spec Kit
  (`specs/001-name/spec.md`), Kiro (`.kiro/specs/<feature>/requirements.md`),
  OpenSpec (`openspec/changes/<change>/proposal.md`) and flat ADR or RFC
  folders (`docs/adr/0001-title.md`). In these tools a directory groups one
  unit's files, not a hierarchy of units.
- Roadmap the leaves record as open points, not in v0.1:
  - v0.2: `wio init`, which writes a config whose
    `[works.defaults.actions]` is `deliver = ["implementation"]`;
    `wio contracts adopt <file>...`, which adds the marker and a generated id
    to an existing file;
  - v0.2: one item for importing existing specs: a mode that treats every
    `.md` file with front matter and an `id` as a Work, configurable id
    generation, and a looser id format;
  - v0.3 and later: `wio init` detects an existing workflow such as Kiro and
    generates config for it. Integrations are generated config, never code
    paths in the engine.
- The `config` Work (`hwn995`), still a draft, picks up the `[works]` and
  `[templates]` tables when it is defined; this Work changes nothing in it.
