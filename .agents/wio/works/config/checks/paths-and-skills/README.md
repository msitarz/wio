<!-- wio
id = "2xpnv0"
template = "feature.leaf"
roots = ["wio", "repo"]
depends_on = ["mcn1xg"]
-->

# Checking paths, skills and templates

## Purpose

Root paths, the directories a skill is looked up in and the `[templates]` table
must be usable and stay inside the repository before a command relies on them.

## Goals

- A root path that is not normalized, leaves the repository or repeats is an
  error, and one that does not exist yet is a warning.
- A stage's skill is found in the repository, or the stage is an error that says
  where wio looked, and the skill paths of the config stay inside it.
- The Works directory, when set, is inside the repository.
- The `[templates]` table has the right shape and its directory is inside the
  repository.

## Glossary

- **Normalized path**: relative to the repository root, with `/` as separator,
  without a `.` or `..` segment, a trailing slash or a leading `/`; `.` alone is
  the whole repository.

## Non-Goals

- Reading any template, or checking that a kind's entry template exists: that is
  `wio templates check`'s.
- Whether the Works, templates or skills directories exist: the commands that
  read them check that.
- Looking in the user's home for a skill, or a built-in list of the directories
  that every harness reads.

## Assumptions

- **A-1**: The project directories that wio looks in for skills are
  `.agents/skills` and `.claude/skills`, and other harnesses' directories are
  added through `[skills] paths`.

- **A-2**: The driver decided that a kind's template name that is an empty
  string is an error.

## Mechanisms

- `FileSystem.exists` and `is_dir`, through the port, for paths and
  `<dir>/<skill>/SKILL.md`.
- `pathlib.PurePosixPath` to normalize a path and tell whether it leaves the
  repository.
- Checks appended to `CHECKS` in `wio.config`.

## Acceptance criteria

### **AC-1** Root paths are normalized, inside the repository and unique

Each path of a root is normalized, stays inside the repository, and is listed
once in its root.

#### The errors

- **Given** a root `a` with paths `src/`, `../x`, `/abs` and `a/./b`, and a root
  `b` with the path `src` twice; a repeat is judged on the normalized text.
- **When** the checks run.
- **Then** each of the first four is an error at its path that names the rule
  and the normalized form where one exists, and the repeat is an error that
  names the first occurrence; the same path in two roots is allowed.

#### A missing path

- **Given** a root path `docs/new` that does not exist.
- **When** `wio config check` runs.
- **Then** a warning at the path says it does not exist yet, and the command
  exits 0 when no other diagnostic is an error.

### **AC-2** A stage's skill is found in the repository

A stage's `skill` is a directory with a `SKILL.md` in `[skills] paths`, in
`.agents/skills` or in `.claude/skills`, searched in that order, and never in
the user's home.

#### Found and not found

- **Given** skills `a` in `.claude/skills`, `b` in a configured path, and a
  stage naming `c`, which exists only in the user's home.
- **When** the checks run.
- **Then** `a` and `b` pass, and `c` is an error at `stages.<name>.skill` that
  lists the directories searched in the order `[skills] paths`,
  `.agents/skills`, `.claude/skills`, and says the user's home is not searched.

#### A skill path outside the repository

- **Given** `[skills] paths = ["../skills"]`; a skill path follows the same rule
  as a root path, normalized and inside the repository.
- **When** the checks run.
- **Then** an error at `skills.paths[0]` says the path must stay inside the
  repository.

### **AC-3** The `[templates]` table has its shape

`[templates] dir`, when set, is a normalized path inside the repository, and
`kinds` maps each kind to a template name.

#### The errors

- **Given** `[templates] dir = "../t"`, and a kind whose template name is an
  empty string.
- **When** the checks run.
- **Then** each is an error that names the key path and what a valid value is.

#### No templates

- **Given** a config without a `[templates]` table.
- **When** the checks run.
- **Then** there is no diagnostic about templates.

### **AC-4** The Works directory is inside the repository

`[works] dir`, when set, is a normalized path inside the repository.

#### Outside

- **Given** `[works] dir = "/abs"`.
- **When** the checks run.
- **Then** an error at `works.dir` says the path must be inside the repository.

## Additional context

- [Stage](../../../../../../docs/concepts.md#7-stage) describes where skills are
  found.
