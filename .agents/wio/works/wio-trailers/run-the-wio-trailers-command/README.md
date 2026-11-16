<!-- wio
id = "37vw05"
template = "feature.leaf"
roots = ["wio"]
depends_on = ["eh62g6", "jyhy64", "vy01kg", "sk5wwq", "x4vs3k"]
-->

# Run the wio trailers command

## Purpose

The write form, the two checks and the fold are separate pieces, and a person or
an agent can use them only as one `wio trailers` command that tells them apart,
reaches the repository and follows one contract for its failures.

## Goals

- `wio trailers` runs the write form, `check` and `fold` from its arguments.
- The adapters behind the ports are wired into the command, so that it works on
  a real repository.
- A usage mistake is reported the same way for every form.

## Non-Goals

- What each form does; its own leaf specifies that.
- A real event sink; constraint C-4 of the top parent keeps it a no-op until
  `wio log` exists.

## Assumptions

### A-1

A first argument that is `check` or `fold` selects that subcommand, and any
other value is a Work id, so a Work cannot be named `check` or `fold`.

### A-2

The rules component does not exist yet, so until it does the port for the rules
of a stage is wired to one that selects no rule, and a cited rule code is
refused as not selected.

## Mechanisms

- **The `wio trailers` group** — in `wio.cli`, which dispatches on the first
  argument and gives every form the exit codes 0, 1 and 2.
- **The wiring** — of the adapters of the `History` and `Contracts` ports, the
  no-op `EventSink` and the port for the rules of a stage, built in `wio.cli`
  and never imported by `wio.trailers`.
- **The help** — `wio trailers --help` lists the three forms and exits 0.

## Acceptance criteria

The examples use a temporary repository with a Work `k3m9xq` that has an item
`AC-1` and a `deliver` that lists `architecture`.

### **AC-1** The arguments select the form

#### The write form, check and fold

- **Given** the repository, and a commit message file and a pull request body.
- **When** `wio trailers k3m9xq deliver architecture`,
  `wio trailers check <file>` and `wio trailers fold block HEAD~1..HEAD` run.
- **Then** the first prints a record, the second checks the file and the third
  prints the folded records of the range, each exiting 0.

### **AC-2** A usage mistake exits 2

#### Calls that no form accepts

- **Given** the repository.
- **When** `wio trailers`, `wio trailers check --nosuch`, `wio trailers fold`,
  `wio trailers fold body` and `wio trailers k3m9xq deliver` run.
- **Then** each exits 2, prints nothing on standard output and says on standard
  error what is wrong.

### **AC-3** The command works on a real repository

#### A round trip with the real adapters

- **Given** the repository, and no injected adapter.
- **When** `wio trailers k3m9xq deliver architecture` prints a record, a commit
  carries it in its message, and `wio trailers check --ref-range HEAD~1..HEAD`
  and `wio trailers fold block HEAD~1..HEAD` run.
- **Then** each exits 0 and the fold prints that record.

#### A gate result with the no-op sink

- **Given** the repository with a gate stage and a work commit under a pure gate
  commit.
- **When** `wio trailers k3m9xq deliver <gate> --result pass --judge human`
  runs.
- **Then** it prints the record, exits 0 and writes no event anywhere.

### **AC-4** The help lists the forms

#### The help text

- **Given** the repository.
- **When** `wio trailers --help` runs.
- **Then** it exits 0 and lists the write form, `check` and `fold`.
