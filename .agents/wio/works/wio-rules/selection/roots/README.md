<!-- wio
id = "ndwemw"
template = "feature.leaf"
roots = ["wio"]
depends_on = []
-->

# Roots of a Work or a path

## Purpose

The roots that count for a stage of a Work, and the roots that contain a file,
are computed nowhere that `wio.rules` may read, so no view of a listing can say
which roots apply.

## Goals

- A Work's expanded roots reach `wio.rules` by the Work's id, through a port
  that `wio.contracts` satisfies, and no `wio contracts` command changes.
- The roots that a stage selects for a Work are found from the stage's `roots`,
  the Work's roots and `@work`, and fail loudly for a Work that has none when
  the stage needs them.
- The roots that contain a file are found from the paths of the roots of the
  config.

## Non-Goals

- Applying the roots to rules, which `5yb4tz` does.
- Turning the argument of `--path` into a path relative to the repository root,
  which `wio rules list` does.
- Expanding `@descendants`, which `wio.contracts` does already and this Work
  only exposes.

## Assumptions

### A-1

The path that is given for a file is already relative to the repository root,
normalized and written with `/`, because the command turns the argument into
one, and the file need not exist.

### A-2

The roots that a Work lists are roots of the config, which `wio contracts check`
already enforces, so a name that is not is a mistake that is refused, not a root
to skip.

## Mechanisms

The names of the types and the functions below are provisional.

- **`WorkRoots`** — a port declared by `wio.rules` in its `ports.pyi`, with
  `roots_of(work_id: str) -> tuple[str, ...] | None`, the roots of the Work with
  `@descendants` expanded, each name once and sorted, and `None` for an id that
  no Work has, as the ports of `wio.trailers` answer; `wio.cli` wires
  `WorkLookup` to it.
- **`WorkLookup.roots_of`** — a method of the `WorkLookup` of `wio.contracts`,
  which satisfies the port structurally as it does those of `wio.trailers`: it
  finds the Work in its views with the discovery of that component and reads the
  roots from the `Hierarchy` that `wio contracts show` already reads, built from
  the same discovery.
- **`stage_roots(config, stage, work_id, work_roots) -> tuple[str, ...]`** — in
  `wio.rules`, with the `Config`, a stage's name, a Work's id and a `WorkRoots`;
  the names it returns are sorted and each is once.
- **`roots_of_path(config, path) -> tuple[str, ...]`** — in `wio.rules`, with
  the `Config` and a `PurePosixPath`.

## Constraints

### C-1

`stage_roots` and `roots_of_path` do no input or output, and `roots_of` only
reads. AC-7 verifies the two functions, and AC-1 and AC-3 the method.

## Acceptance criteria

### **AC-1** A Work's expanded roots are given by its id

`WorkLookup.roots_of` returns the roots of a Work with `@descendants` expanded
through its descendants, each name once and sorted.

#### A tree of Works

- **Given** a Work `p` whose roots are `["e2e", "@descendants"]` with children
  `a` with `["api"]` and `b` with `["@descendants"]`, and a child `c` of `b`
  with `["web", "web"]`.
- **When** `roots_of` is asked for `p`, `b`, `a` and `c`.
- **Then** they are `("api", "e2e", "web")`, `("web",)`, `("api",)` and
  `("web",)`.

### **AC-2** An unknown Work is `None` and an empty one is empty

`roots_of` gives `None` for an id that no Work has, and an empty tuple for a
Work with no roots and for a leaf that lists `@descendants`.

#### Unknown and empty

- **Given** a Work `x` with no roots, a leaf `y` with `["@descendants"]`.
- **When** `roots_of` is asked for `x`, `y` and an id `none`.
- **Then** the first two are `()` and the third is `None`.

### **AC-3** No `wio contracts` command changes

Adding `roots_of` changes nothing that a `wio contracts` command or the other
methods of `WorkLookup` print or return.

#### The commands as they were

- **Given** the scenarios of the acceptance tests of `wio contracts` and of the
  `wio.trailers` commands that use `WorkLookup`.
- **When** they run after `roots_of` is added.
- **Then** every output and exit code is what it was before.

### **AC-4** The stage decides which roots count

A stage with no `roots` selects the Work's roots, a stage with `roots` selects
exactly those with `@work` standing for the Work's roots, and `[]` selects none.

#### Each form

- **Given** a Work whose roots are `["api"]`, a root `contract` in the config,
  and stages with no `roots`, with `roots = ["contract"]`, with
  `roots = ["contract", "@work"]` and with `roots = []`.
- **When** `stage_roots` runs for each stage.
- **Then** the results are `("api",)`, `("contract",)`, `("api", "contract")`
  and `()`.

#### A Work without roots

- **Given** a Work with no roots and the same four stages.
- **When** `stage_roots` runs for each.
- **Then** the stage with no `roots` and the stage with `["contract", "@work"]`
  each raise `ValueError` that says the Work has no roots, whatever other roots
  the list names, and the stage with `["contract"]` gives `("contract",)` and
  the stage with `[]` gives `()`.

### **AC-5** A name that does not exist is refused

An unknown stage, an unknown Work, a root of a Work that the config does not
have and a root of a stage that it does not have each raise `KeyError` that
names it.

#### Unknown names

- **Given** a config with the root `api`, a Work whose roots are `["nope"]`, and
  a stage with `roots = ["missing"]`.
- **When** `stage_roots` runs for a stage `none`, for an id `none`, for the Work
  with the stage that has no `roots`, and for the stage with `["missing"]`.
- **Then** each raises `KeyError` naming `none`, `none`, `nope` and `missing`.

### **AC-6** The roots that contain a file

A file is in a root when its path is the root's path or lies under it, by whole
path components, and every root that contains it is returned, sorted by name.

#### Overlapping roots

- **Given** roots `api` with `src/api`, `api2` with `src/api2`, `web` with
  `src/web` and `repo` with `.`.
- **When** `roots_of_path` runs for `src/api/app.py`, `src/api2/x.py`,
  `docs/readme.md` and `src/api`.
- **Then** the results are `("api", "repo")`, `("api2", "repo")`, `("repo",)`
  and `("api", "repo")`.

#### A file in no root

- **Given** the roots `api` and `web` only.
- **When** `roots_of_path` runs for `docs/readme.md`.
- **Then** it gives `()`.

### **AC-7** The functions are pure and do not depend on order

`stage_roots` and `roots_of_path` give the same result whatever the order of the
roots of the config, of a root's paths and of a stage's `roots`.

#### Two orders

- **Given** the config of AC-4 and AC-6 declared in two orders and the `roots`
  of a stage listed in two orders.
- **When** the functions run on each, with fakes for the port and no file
  system.
- **Then** the results are equal.

## Additional context

- `Hierarchy.roots` in `src/wio/contracts/hierarchy.py` already resolves a
  Work's roots with `@descendants` and sorts them, so the new method adds a
  lookup by id and nothing else; `WorkLookup` in `src/wio/contracts/lookup.py`
  already finds a Work by id for the ports of `wio.trailers`, and one class may
  satisfy the ports of several consumers, so no second adapter is added.
- `wio.context` declares a provisional `RuleSelection.select(contract, stage)`
  whose contract holds the roots as written; the adapter of `5yb4tz` calls this
  port with the Work's id, so that signature need not carry the roots.
