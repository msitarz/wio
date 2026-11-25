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
- In a config that loads, the lookup finds the skill of every stage that names
  one.

## Non-Goals

- Loading or running a skill, which a harness does.
- Reading the text of `SKILL.md`, which the bundle never includes.

## Assumptions

### A-1

The search that `wio.config` uses to check that a stage's skill exists, which is
private to `wio.config.paths` today and answers only whether a skill is found,
can be refactored to return the directory of the first match without changing
what `wio config check` reports, and the files of a directory are listed and
read through `FileSystem` of `wio.io`, which already lists a directory and reads
bytes.

### A-2

The lookup leaves out a path with a fault and rejects a name that is empty, `.`,
`..` or holds `/`, as the check does, so a directory it returns is normalized.

### A-3

Every regular file on disk below a skill's directory counts toward its hash, so
a skill's directory holds only the skill's own files, and the same commit can
give another hash on a machine with a stray file in it. A symbolic link never
counts, so a skill whose `SKILL.md` is a link is found, as the check accepts it,
and its hash leaves the link out.

### A-4

A config loads only when `wio config check` finds no error in it, and the
`Settings` port raises for any other, so while a skill path has a fault or a
stage's skill is not found, every lookup raises that error and gives no answer.

## Mechanisms

The names and the shapes below are provisional, except the hash, which is
required.

- **The skill search** — in `wio.config`, which looks in `[skills] paths` and
  then in `.agents/skills` and `.claude/skills`, and which this Work refactors
  and exposes through a port of `wio.context`.
- **The lookup** — `find_skill(name: str) -> FoundSkill | None`, where
  `FoundSkill` holds the directory, relative to the repository and with `/`
  separators, and the files hash; `None` means that no directory holds the
  skill.
- **The files hash** — the SHA-256, as 64 lower-case hexadecimal digits, of the
  concatenation, for every regular file below the skill's directory at any depth
  in the order of the UTF-8 bytes of their relative paths written with `/`, of
  the path in UTF-8, a NUL byte, the file's bytes and a NUL byte.

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

### **AC-2** What gives no skill

In a config that loads, a directory that has no `SKILL.md`, a skill that is only
in the user's home, and a name that is empty, `.`, `..` or holds `/` give
`None`; a config that does not load, such as one with a skill path that has a
fault, ends the lookup with the error of the settings instead of an answer.

#### A directory without `SKILL.md`, and a skill only in the home

- **Given** `.agents/skills/wio-define` with no `SKILL.md`, and `wio-define` in
  the user's home directory.
- **When** `wio-define` is looked up.
- **Then** the lookup gives `None`.

#### A path with a fault

- **Given** `[skills] paths = ["./a"]` and `a/wio-define/SKILL.md`.
- **When** `wio-define` is looked up and `wio config check` runs.
- **Then** the check reports the path, and the lookup raises the error of the
  settings.

#### Names that are not skill names

- **Given** a repository with a skill `wio-define`.
- **When** `..`, `a/b` and the empty name are looked up.
- **Then** each lookup gives `None`.

### **AC-3** The hash covers every file and only the files

The hash of a skill changes when a file's bytes change, when a file is added or
renamed, and not when only a modification time or a mode changes, and a symbolic
link adds nothing.

#### The bytes of the hash

- **Given** a skill with `SKILL.md` holding `x` and a newline and
  `references/a.md` holding `y` and a newline.
- **When** its hash is computed.
- **Then** it is
  `1a47c19b09044a025c5c5b147b88adffccd800023e4e1c1ee70c730329c16fe2`, the
  SHA-256 of `SKILL.md`, a NUL, `x` and a newline, a NUL, `references/a.md`, a
  NUL, `y` and a newline, and a NUL.

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

In a config that loads, the skill of every stage that names one is found, and a
config in which the check rejects a skill does not load, so it ends the lookup
with the error of the settings.

#### Every stage's skill exists

- **Given** a config that loads, with one stage whose skill is in
  `.agents/skills` and one whose skill is in `.claude/skills`.
- **When** `wio config check` runs and each skill is looked up.
- **Then** the check reports no error, and both skills are found.

#### A stage with a skill and one without

- **Given** a repository where one stage names a skill that exists and another
  names one that exists nowhere.
- **When** `wio config check` runs and each skill is looked up.
- **Then** the check reports an error only for the second, and each lookup
  raises the error of the settings.
