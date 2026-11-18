<!-- wio
id = "d3kanf"
template = "feature.leaf"
roots = ["wio"]
depends_on = []
-->

# Print a record for no Work

## Purpose

A commit that belongs to no Work still needs a record, and an agent that types
`Wio-Work: none` by hand can get it wrong, so the engine prints it as it prints
every other record.

## Goals

- `wio trailers none` prints the record of a commit that belongs to no Work.
- A call that gives `none` anything else, or that lists Works, is refused and
  says what is wrong.

## Non-Goals

- Writing one record for a list of Works.
- Writing a record for no Work with an action, a stage, items, a result or a
  judge, which the shape of a `Wio-Work: none` record forbids.

## Assumptions

None.

## Mechanisms

- **`wio trailers none`** — the form of the write command with no other
  argument, which prints `Wio-Work: none` and a newline on standard output, and
  exits 0.
- **The record** — rendered by the shared renderer of `wio.formats` from the one
  field `Wio-Work`, and never built as a line of text by the form.
- **Refusals** — a usage error, which exits 2 and prints nothing on standard
  output, for a `none` that is given an action, a stage or an option, and for a
  value that lists Works with a comma, `none` among them. The message for a list
  says that a list of Works is not written and asks for one Work.

## Constraints

### C-1

The form is wired as the other forms of `wio trailers` are, so a config that
cannot be read, or a working directory outside a git repository, exits 2 before
it prints anything. A reviewer judges it from the wiring in `wio.cli`.

## Acceptance criteria

The examples use a git repository with a config that declares the action
`deliver` and the stage `architecture`.

### **AC-1** A record for no Work is printed and accepted by the check

#### The printed record round-trips

- **Given** the repository.
- **When** `wio trailers none` runs, and its output is the paragraph of a commit
  message that `wio trailers check --require` reads.
- **Then** the first prints exactly `Wio-Work: none` and a newline and exits 0,
  and the second exits 0.

### **AC-2** A `none` with anything more is refused

#### An action, a stage and an option

- **Given** the repository.
- **When** `wio trailers none deliver architecture`, `wio trailers none --items
  AC-1` and `wio trailers none --result pass` run.
- **Then** each exits 2, prints nothing on standard output and says on standard
  error what is wrong.

### **AC-3** A list of Works is refused

#### A comma list, with and without `none`

- **Given** the repository and a Work `k3m9xq`.
- **When** `wio trailers k3m9xq,a7b2c4 deliver architecture` and `wio trailers
  none,k3m9xq deliver architecture` run.
- **Then** each exits 2, prints nothing on standard output and says on standard
  error that a list of Works is not written.

### **AC-4** A config that cannot be read exits 2

#### An invalid config

- **Given** a repository whose config is not valid TOML.
- **When** `wio trailers none` runs.
- **Then** the command exits 2 and prints nothing on standard output.

## Additional context

The refusal of a list and of `none` is `_one_work` in
`src/wio/trailers/write.py`, and its message today names `none` as a list of
Works. The command's own `--help` lists the forms and is not part of this
contract. The documents that say the write form refuses `none` are
`src/wio/trailers/README.md` and the v0.1 note in `docs/concepts.md`.
