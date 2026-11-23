<!-- wio
id = "9pfyfe"
template = "feature.leaf"
roots = ["wio"]
depends_on = ["5yb4tz", "ndwemw", "w3k7vd"]
-->

# Rule selector for context and trailers

## Purpose

`wio context` and `wio trailers` each wait for a provider of the rules that a
stage selects for a Work, and nothing gives them one, so a bundle has no rules
and every cited rule is refused.

## Goals

- One class gives `wio context` the selection of a Work at a stage and gives
  `wio trailers` the rules that the stage selects for the Work, through the
  ports that they already declare.
- `wio trailers` receives with each selected rule the hash of its file, computed
  by one function that `wio context` will use as well.
- A fault in the rules and an unknown name are refused in the form that each
  consumer expects, and a Work without roots gets a selection with no included
  rule.

## Non-Goals

- Choosing the rules, which `select` of `5yb4tz` does, and finding the roots,
  which `ndwemw` does.
- Writing the `context` and `review` events, which `wio context` and
  `wio trailers` do with what this gives them.

## Assumptions

### A-1

The hash of a rule is the SHA-256 of its file's bytes as stored, written as 64
lower-case hexadecimal digits, because the event models carry the hash as an
opaque string, the log already hashes with SHA-256, and a hash of the bytes
changes when any part of the file does.

### A-2

The action does not change which rules a stage selects, so `selected` takes it
because its port does and does not read it.

### A-3

The config, the rule files and the Work's roots are read from the working tree,
so the hash is that of the file on disk when `wio trailers` runs, which can
differ from the staged or committed file; the reviewed commit is recorded
separately by `wio trailers`.

### A-4

A Work with no roots gets no included rule from a stage that selects the Work's
roots, because `wio trailers` calls `selected` for every gate record, with no
cited rule too, and it received an empty mapping for every Work from `NoRules`.

## Mechanisms

The names of the types and the functions below are provisional.

- **`RuleSelector`** — a frozen dataclass in `wio.rules` whose collaborators are
  injected: `settings: Settings`, `repository: Repository` for the repository
  root, `files: FileSystem` and `work_roots: WorkRoots`; it builds the
  `Mapping[str, LoadedRuleset]` with `ruleset_map` of `w3k7vd` and reads a
  rule's file at `root / rule.path`.
- **`RuleSelector.selection(work_id: str, stage: str) -> Selection`** — runs the
  discovery of `8zn10d`, refuses on an error of it with `refuse_on_errors`,
  takes the roots from `stage_roots` of `ndwemw`, and calls `select` of
  `5yb4tz`.
- **The Work without roots** — `selection` catches the `ValueError` of
  `stage_roots` for a Work that has no roots and returns a `Selection` in which
  every rule is out with the reason `not-selected`, so that `select` gives it to
  `wio context` and `selected` gives no rule to `wio trailers`.
- **`RuleSelector.select(contract: ResolvedContract, stage: str) -> Selection`**
  — the method of the `RuleSelection` port of `wio.context`, which calls
  `selection` with the id of the contract's Work.
- **`RuleSelector.selected(work_id, action, stage)`** — the method of the
  `StageRules` port of `wio.trailers`, which returns a `Mapping[str, str]` of
  the qualified code of each included rule to `rule_hash` of the bytes of its
  file.
- **`rule_hash(data: bytes) -> str`** — in `wio.formats`, the hash of A-1.
- **The refusal** — the `DiagnosticsError` of `refuse_on_errors` of `8zn10d`, or
  a `WioError` that names a cause that `wio trailers` cannot receive as an
  exception, such as an unknown name or a rule file that cannot be read, which
  `wio.cli` turns into exit 2.

## Constraints

### C-1

`selection` and `select` read only the rule files and manifests that the
discovery reads, and `selected` reads in addition the bytes of the files of the
rules it returns and of no others, all through the `FileSystem` port. AC-2
verifies it.

### C-2

`wio.cli` wires one `RuleSelector`, whose `work_roots` is the `WorkLookup` of
`wio.contracts`, to the `RuleSelection` port of `wio.context`
and the `StageRules` port of `wio.trailers`, in place of the `NoRules` that it
wires today, and removes the `NoRules` class of `wio.cli.null` that nothing then
uses. AC-10 of [wio rules](../../README.md) verifies the wiring and AC-9 the
removal.

### C-3

The docstring of `RuleSelection.select` in `src/wio/context/ports.pyi` says that
a Work without roots gets a selection with no included rule, in place of the
`ValueError` it documents today, and AC-7 verifies the behaviour it states.

## Acceptance criteria

### **AC-1** The selector gives `wio context` the selection

`select` and `selection` give the selection of `select` of `5yb4tz` for the
roots that the stage selects for the Work.

#### The same selection

- **Given** the repository of AC-1 of [selection](../README.md) with its Work
  whose roots list `api`, a root `web` of the config, a stage with no `roots`,
  and a stage with `roots = ["web"]`.
- **When** `selection` runs for the Work and each stage, and `select` runs for
  the Work's resolved contract and each stage.
- **Then** each equals `select` of `5yb4tz` for the roots `("api",)` and
  `("web",)`.

### **AC-2** `selected` gives the hash of each selected rule

`selected` gives the qualified code of every rule that the selection includes
and the hash of its file, reads the bytes of those files only, and gives a
different hash when a file changes.

#### Included rules only

- **Given** a Work and a stage whose selection includes `demo.ARC001`, whose
  file has CRLF line endings, excludes `demo.ARC002` by the stage and cuts
  `web.WEB001` because the roots do not reach its ruleset, and a file system
  that records every read of bytes.
- **When** `selected` runs for the Work, two different actions and the stage,
  then the file of `ARC001` is edited and it runs again.
- **Then** the mapping holds `demo.ARC001` with `rule_hash` of its bytes and no
  other rule, it is the same for both actions, the bytes of the file of
  `ARC001` were read and those of the files of `ARC002` and `WEB001` were not,
  and the second run has a different hash.

### **AC-3** `rule_hash` is the SHA-256 of the bytes

`rule_hash` gives the SHA-256 of its input as 64 lower-case hexadecimal digits.

#### Known inputs

- **Given** the bytes of the empty input and of `abc`.
- **When** `rule_hash` runs on each.
- **Then** the results are
  `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` and
  `ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad`.

### **AC-4** A fault in the rules is a refusal, not a partial answer

When the discovery reports an error, none of the three methods returns a
selection or a mapping.

#### Two rules with one code

- **Given** a ruleset `demo` that holds two rules with the code `ARC001`.
- **When** `selection`, `select` and `selected` run.
- **Then** each raises the `DiagnosticsError` that carries the error naming both
  files, and none returns a selection or a mapping.

### **AC-5** Unknown names are refused

Each consumer receives a refusal in the form its port expects: the exceptions of
`select` for `wio context`, and a `WioError` for `wio trailers`, whose port
declares none.

#### Each cause

- **Given** an unknown stage and an unknown Work id.
- **When** `selection`, `select` and `selected` run for each.
- **Then** `selection` and `select` raise `KeyError` for each, as the
  `RuleSelection` port declares for the stage and as an addition to it for the
  Work, and `selected` raises a `WioError` that names the cause, so that
  `wio trailers` exits 2 and not 70.

### **AC-6** The result does not depend on the order of the inputs

The same config, files and arguments give the same selection and the same
mapping, whatever the order of the inputs.

#### Two orders

- **Given** the repository of AC-2 with its config tables and the listing of its
  files in two orders.
- **When** `selection` and `selected` run on each.
- **Then** the selections are equal and the mappings are equal.

### **AC-7** A Work without roots gets a selection with no included rule

For a Work with no roots and a stage that selects the Work's roots, none of the
three methods raises, and no rule is included, so that a gate record of such a
Work needs no rule.

#### For `wio trailers`

- **Given** the repository of AC-1 of [selection](../README.md) with a Work that
  lists no roots and a stage with no `roots`.
- **When** `selected` runs for the Work, an action and the stage.
- **Then** it returns an empty mapping and raises nothing.

#### For `wio context`

- **Given** the same Work and stage.
- **When** `selection` and `select` run.
- **Then** each returns a selection with an entry for every rule, none included
  and each out with the reason `not-selected`, and raises nothing.

### **AC-8** A rule file that cannot be read for its hash is a refusal

A rule file whose bytes cannot be read when `selected` hashes it is a `WioError`
that names the file, and not an unhandled `OSError`.

#### An unreadable file

- **Given** a selection that includes `demo.ARC001`, and a file system whose
  read of the bytes of that file raises `OSError` although the discovery read
  its text.
- **When** `selected` runs.
- **Then** it raises a `WioError` that names the file of `ARC001`, so that
  `wio trailers` exits 2 and not 70.

### **AC-9** The selector replaces `NoRules`

The `NoRules` class of `wio.cli.null` is gone, and `wio.cli` wires the selector
where it wired it.

#### No `NoRules`

- **Given** the package `wio.cli` after the delivery.
- **When** `wio.cli.null` is imported and the wiring of `wio trailers` is built.
- **Then** `wio.cli.null` has no `NoRules`, and the `StageRules` that `wio.cli`
  gives `wio trailers` is a `RuleSelector`.

## Additional context

- The `RuleSelection` and `StageRules` ports are declared by their consumers in
  `src/wio/context/ports.pyi` and `src/wio/trailers/ports.pyi`; the class
  satisfies them structurally, as `WorkLookup` satisfies the ports of
  `wio.trailers`, and `wio.cli` replaces the `NoRules` that it wires to
  `wio.trailers` today with this class, which C-2 states.
- `wio rules list` does not call `selection`: it runs the discovery once itself
  and calls `select` of `5yb4tz` with the roots that `stage_roots` gives, as
  `fjvj3x` states, so it still refuses a Work with no roots.
- `wio.context` will write a hash for every rule in its `context` event and will
  use `rule_hash` for it, which is why the function lives in `wio.formats`.
