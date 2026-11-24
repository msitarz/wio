<!-- wio
id = "bgc8q9"
template = "feature.leaf"
roots = ["wio"]
depends_on = []
-->

# Skill lookup

## Purpose

The bundle points to a stage's skill, names where it was found and counts its
files in the id, but nothing returns the directory of a skill or the hash of its
files, because `wio.config` only checks that the skill exists.

## Goals

- The directory of a stage's skill is found by the order that the concepts give,
  and the first match wins.
- A skill is never looked for in the user's home.
- The files of a skill have one hash that changes when any of them changes.
- The directory is given relative to the repository.
- The lookup finds a skill exactly when `wio config check` accepts it.

## Non-Goals

- Loading or running a skill, which a harness does.
- Reading the text of `SKILL.md`, which the bundle never includes.

## Assumptions

### A-1

The search that `wio.config` uses to check that a stage's skill exists, which is
private to `wio.config.paths` today and answers only whether a skill is found,
can be refactored to return the directory of the first match without changing
what `wio config check` reports, and a port of `wio.context` lists the files of
a directory and reads their bytes, which the check does not need.

### A-2

The lookup leaves out a path with a fault and rejects a name that is empty, `.`,
`..` or holds `/`, as the check does, so a directory it returns is normalized.

## Mechanisms

The names and the shapes below are provisional.

- **The skill search** — in `wio.config`, which looks in `[skills] paths` and
  then in `.agents/skills` and `.claude/skills`, and which this Work refactors
  and exposes through a port of `wio.context`.
- **The lookup** — `find_skill(name: str) -> FoundSkill | None`, where
  `FoundSkill` holds the directory, relative to the repository and with `/`
  separators, and the files hash; `None` means that no directory holds the
  skill.
- **The files hash** — the SHA-256, as 64 lower-case hexadecimal digits, of the
  concatenation, for every regular file below the skill's directory at any depth
  in the order of their relative paths as `/`-separated text, of the path, a NUL
  byte, the file's bytes and a NUL byte; dotfiles count and a symbolic link does
  not.

## Constraints

### C-1

The hash depends on the paths and the bytes of the files and on nothing else, so
a change of a modification time or of a file mode leaves it as it was.

## Acceptance criteria

### **AC-1** The first match wins in the documented order

A skill is looked for in the directories of `[skills] paths`, in their order,
and then in `.agents/skills` and `.claude/skills`, and the first directory that
holds `<name>/SKILL.md` is the skill's.

#### A skill in two places

- **Given** `wio-define` in `.agents/wio/skills`, named by `[skills] paths`, and
  also in `.agents/skills`.
- **When** the skill is looked up.
- **Then** the directory is `.agents/wio/skills/wio-define`.

### **AC-2** What is not a skill is not found

A directory that has no `SKILL.md`, a skill that is only in the user's home, and
a name that is empty, `.`, `..` or holds `/` give `None`.

#### Four ways not to find one

- **Given** `.agents/skills/wio-define` with no `SKILL.md`, `wio-define` in the
  user's home directory, and a repository with a skill `wio-define`.
- **When** `wio-define` is looked up, then `..`, then `a/b`, then the empty
  name.
- **Then** each lookup gives `None`.

### **AC-3** The hash covers every file and only the files

The hash of a skill changes when a file's bytes change, when a file is added or
renamed, and not when only a modification time or a mode changes, and a symbolic
link adds nothing.

#### The bytes of the hash

- **Given** a skill with `SKILL.md` and `references/a.md`.
- **When** its hash is computed.
- **Then** it is the SHA-256 of `SKILL.md`, a NUL, the bytes of `SKILL.md`, a
  NUL, `references/a.md`, a NUL, the bytes of `references/a.md` and a NUL.

#### Five changes

- **Given** the same skill.
- **When** a byte of `references/a.md` changes, then a file is added, then a
  file is renamed, then a symbolic link to a file is added, and then only the
  modification time of `SKILL.md` changes.
- **Then** the first three give a hash that differs from the one before, and the
  last two give the same hash as before.

### **AC-4** The directory is relative to the repository

The directory of the skill is returned relative to the repository root and with
`/` separators.

#### A found skill

- **Given** a skill in `.agents/skills/wio-define` of a repository.
- **When** it is looked up from another working directory of the repository.
- **Then** the directory is `.agents/skills/wio-define`.

### **AC-5** The lookup and the check agree

A skill that `wio config check` accepts for a stage is found, and a skill that
it rejects is not.

#### A stage with a skill and one without

- **Given** a repository where one stage names a skill that exists and another
  names one that exists nowhere.
- **When** `wio config check` runs and each skill is looked up.
- **Then** the check reports an error only for the second, and the lookup finds
  only the first.
