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

## Non-Goals

- Loading or running a skill, which a harness does.
- Reading the text of `SKILL.md`, which the bundle never includes.

## Assumptions

### A-1

The search that `wio.config` uses to check that a stage's skill exists can be
shared by changing only who may call it, so that the check and the lookup cannot
disagree.

## Mechanisms

- **The skill search** — in `wio.config`, which looks in `[skills] paths` and
  then in `.agents/skills` and `.claude/skills`, and which this Work exposes
  through a port of `wio.context`.
- **The skill hash** — a hash of the relative path and the bytes of every file
  of the skill, in the order of the paths.

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

### **AC-2** A directory without `SKILL.md` and the home are not searched

A directory that has no `SKILL.md` is not a skill, and the user's home is never
looked in.

#### No `SKILL.md`, and a skill only in the home

- **Given** `.agents/skills/wio-define` with no `SKILL.md`, and `wio-define` in
  the user's home directory.
- **When** the skill is looked up.
- **Then** nothing is found.

### **AC-3** The hash covers every file and only the files

The hash of a skill changes when a file's bytes change, when a file is added or
renamed, and not when only a modification time or a mode changes.

#### Four changes

- **Given** a skill with `SKILL.md` and `reference.md`.
- **When** a byte of `reference.md` changes, then a file is added, then a file
  is renamed, and then only the modification time of `SKILL.md` changes.
- **Then** the first three give a hash that differs from the one before, and the
  last gives the same hash.

### **AC-4** The directory is relative to the repository

The directory of the skill is returned relative to the repository root and with
`/` separators.

#### A found skill

- **Given** a skill in `.agents/skills/wio-define` of a repository.
- **When** it is looked up from another working directory of the repository.
- **Then** the directory is `.agents/skills/wio-define`.
