<!-- wio
id = "h8qpxd"
template = "feature.leaf"
roots = ["wio"]
depends_on = ["xtgz9z"]
-->

# The id and the place of a new Work

## Purpose

A new Work needs an id that no Work in the tree has and a place that cannot
clash with another Work or hide the new one from every command. Deciding them is
separate from writing the contract, so that the rules for ids and paths are
stated and tested once, and the generator of ids can be replaced by a project
later.

## Goals

- A new Work gets a short random id that is not the id of a Work in the tree.
- A Work's directory gets a readable name from its title, or the name the person
  gives, and no name can hide the Work.
- A new Work is placed in the Works directory, under a parent, or at a path the
  person names, by the rules of the hierarchy mode.
- A Work that exists is never overwritten.

## Non-Goals

- Writing the contract, its template or its title, which the new leaf does.
- Avoiding ids that were used by a deleted Work, which needs the history and
  belongs to the `wio trailers` Work, and an id generator other than the random
  one, with a config key to pick it.
- Moving or renaming a Work.

## Assumptions

- **A-1**: The discovery leaf is delivered, so the Works of the tree, their
  paths and ids, and the explanation of what makes a path a Work are available.
- **A-2**: `Entropy.random_bytes` gives uniformly random bytes, and a test can
  fix them.
- **A-3**: Two creators racing for one path are not handled, as the parent's A-3
  says, so the guard checks that a path does not exist and then writes.

## Mechanisms

- A function in `wio.contracts` that, given the arguments of `new`, the Works of
  the tree and the hierarchy mode, decides the id and the path of the new Work
  and writes nothing.
- An interface for an id generator with one implementation, the random one,
  drawing from the `Entropy` port.
- A guard in `wio.contracts` that writes a new file through `FileSystem` and
  refuses a path that exists.
- `closest_key` from the shared leaf, for a mistyped parent id, and
  `ContractsError` from the command leaf for every refusal.
- The names, the signatures and the interface of the generator are provisional,
  for the architecture stage to decide.

## Constraints

- **The id is six characters of a fixed alphabet.** They are lowercase Crockford
  base32, `0123456789abcdefghjkmnpqrstvwxyz`, each the low five bits of one
  random byte. The id is drawn again until no Work in the tree has it, a Work
  with a shared id included, and after 100 draws the command gives up with an
  error.
- **A slug is derived by one rule.** From a title it is the title in lowercase,
  with the letters of a fixed table written out (`ł` as `l`, `ø` as `o`, `đ` as
  `d`, `ð` as `d`, `ħ` as `h`, `ı` as `i`, `æ` as `ae`, `œ` as `oe`, `ß` as `ss`
  and `þ` as `th`) and the other accents folded to ASCII, with every run of
  other characters turned into one `-`, with `-` trimmed from both ends, and cut
  at 48 characters with a trailing `-` trimmed again. A character that is still
  not ASCII is dropped, and a slug that is empty is an error that asks for
  `--slug`.
- **A given slug is used as written.** It must be lowercase letters and digits
  in groups joined by single `-`, so it can never start with `.`, hold `/` or
  `..`, and hide the Work.
- **One of three names is required.** At least one of `--slug`, `--title` and
  `--path` is given. `--slug` and `--title` may be given together, `--path`
  excludes `--slug`, and under `nesting` it also excludes `--parent`.
- **The default place is a directory.** It is
  `<Works directory>/<slug>/README.md`, and with `--parent`, under `nesting`
  only, it is `<the directory of the parent's file>/<slug>/README.md`. Under
  `flat`, `--parent` is an error, and a parent that no Work has, or that two
  Works share, is an error.
- **A path is a Work's path.** `--path` is relative to the repository root, has
  no `..` and no segment that starts with `.`, ends in `.md` with that case,
  lies under the Works directory, runs through no symbolic link, and does not
  exist. Under `nesting` it is not directly in the Works directory and its
  directory holds no marked file already, and under `flat` neither applies.
- **Nothing is overwritten.** A directory or a file that exists, an empty
  directory included, is an error that names it.
- **Deciding writes nothing.** Only the guard writes, one new file.

## Acceptance criteria

### **AC-1** A slug is derived from a title by one rule

The slug of a title is ASCII, lowercase, joined by single `-` and at most 48
characters, and a title with no usable letter is an error.

#### Titles

- **Given** the titles `Read config.toml`, `Łódź café`, `Straße æon`,
  `  --A  B--  `, forty-seven letters `a`, a space and `b`, and `Привет`.
- **When** the slug of each is derived.
- **Then** the slugs are `read-config-toml`, `lodz-cafe`, `strasse-aeon`, `a-b`,
  the forty-seven letters, and an error that asks for `--slug` for the last.

### **AC-2** A given slug must be lowercase kebab case

A slug that could hide the Work or leave its directory is an error, and one that
is already kebab case is used as written.

#### Slugs

- **Given** the slugs `login`, `2026-11-02-login-design`, `.draft`, `a/b`, `..`,
  `Login`, `a_b`, `a--b`, `-a` and an empty one.
- **When** each is checked.
- **Then** the first two are used as written, and each of the others is an error
  that shows the rule.

### **AC-3** The place follows the arguments and the hierarchy mode

The default place is a directory of the Works directory or of the parent, and
the options that cannot be combined, or name what does not exist, are errors.

#### Nesting

- **Given** `hierarchy = "nesting"`, a Work `p5n2hv` at `p/README.md`, a Work
  `k3m9xq` at `q/spec.md`, and the title `Child`.
- **When** the place of a new Work is decided with the title alone, with
  `--parent p5n2hv`, with `--parent k3m9xq`, and with
  `--slug child --title Other`.
- **Then** the paths are `.agents/wio/works/child/README.md`,
  `.agents/wio/works/p/child/README.md`, `.agents/wio/works/q/child/README.md`
  and `.agents/wio/works/child/README.md`, the last with the title `Other`.

#### Refusals

- **Given** the same Works, an existing directory `.agents/wio/works/child`, and
  two Works with the id `a7b2c4`.
- **When** the place is decided with no name, with `--path` and `--slug`, with
  `--path` and `--parent`, with `--parent k3m9xr`, with `--parent a7b2c4`, and
  with the title `Child`.
- **Then** each is an error: that a name is required, that the options exclude
  each other, twice, that the parent `k3m9xr` has no Work and the closest is
  `k3m9xq`, that the id is shared, and that the directory `child` exists.

#### Flat

- **Given** `hierarchy = "flat"`.
- **When** the place is decided with `--parent p5n2hv`.
- **Then** it is an error that says `--parent` needs `nesting`.

### **AC-4** A path must be one that a Work could have

`--path` is accepted only when the file would be a Work and does not exist.

#### Paths

- **Given** `hierarchy = "nesting"`, a Work at `p/README.md` and the paths
  `.agents/wio/works/q/spec.md`, `/tmp/x.md`, `.agents/wio/works/../x.md`,
  `docs/x.md`, `.agents/wio/works/.hidden/x.md`, `.agents/wio/works/q/spec.txt`,
  `.agents/wio/works/q/spec.MD`, `.agents/wio/works/p/README.md`,
  `.agents/wio/works/top.md`, `.agents/wio/works/p/other.md`, and a path through
  a symbolic link.
- **When** each is checked as the path of a new Work.
- **Then** the first is accepted and its directory is created by the writer, and
  each of the others is an error that names the path and says why.

#### Flat

- **Given** `hierarchy = "flat"`, the same Work, and the paths
  `.agents/wio/works/top.md` and
  `.agents/wio/works/p/other.md`.
- **When** each is checked.
- **Then** both are accepted.

### **AC-5** An id is six characters of the alphabet and is not in the tree

The id is drawn from `Entropy` until it is free, and the draw gives up after 100
tries.

#### Fixed bytes

- **Given** an `Entropy` that gives the bytes 0 to 5 and then 6 to 11, an empty
  tree, and a tree with a Work whose id is `012345`.
- **When** an id is drawn for each.
- **Then** the first is `012345`, the second is `6789ab`, and both consist of
  the characters of the alphabet only.

#### A shared id and no free id

- **Given** a tree where two Works share the id `012345` and an `Entropy` that
  gives the bytes 0 to 5 and then 6 to 11, and a tree that holds `012345` with
  an `Entropy` that gives the bytes 0 to 5 every time.
- **When** an id is drawn for each.
- **Then** the first is `6789ab`, drawn after the shared id, and the second ends
  after 100 draws with an error.

### **AC-6** Deciding writes nothing, and the guard never overwrites

Deciding the place changes no file, and the guard writes a new file and refuses
one that exists.

#### The guard

- **Given** a recording file system, a path that is free, and a path that
  exists.
- **When** the place is decided for each, and the guard is asked to write a
  contract to each.
- **Then** deciding wrote nothing, the guard wrote the free path with its
  directories, and for the existing path it raised an error that names it and
  changed nothing.

## Additional context

- [Identity and location](../../../../../docs/concepts.md#identity-and-location)
  states the rules for ids, the default place and `--path`.
- The new leaf calls this leaf's decision and writes the contract through the
  guard, with the skeleton of the template.
- The alphabet has no `i`, `l`, `o` or `u`, so an id cannot be mistaken for a
  digit and cannot spell `none`.
