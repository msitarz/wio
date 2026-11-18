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
- A `--json` option. The command prints a plain record to append to a commit
  message and sends the findings of a check to standard error, so it deviates
  on purpose from the convention of `wio.cli` that every command declares
  `--json`; the driver confirms this at the gate.

## Assumptions

### A-1

A first argument that is `check` or `fold` selects that subcommand, and any
other value is a Work id, so a Work cannot be named `check` or `fold`, though
`wio contracts` does not forbid such an id. The form is chosen by the first
argument, so an option before it is a usage error.

### A-2

The rules component does not exist yet, so until it does the port for the rules
of a stage is wired to one that selects no rule, and a cited rule code is
refused as not selected.

### A-3

`wio trailers` with no argument is a usage error, because the write form needs a
Work, an action and a stage, and so it exits 2 as the other usage mistakes do,
unlike `wio` and `wio contracts`, which print their help and exit 0.

## Mechanisms

- **The `wio trailers` group** — in `wio.cli`, which dispatches on the first
  argument and gives every form the exit codes 0, 1 and 2. It reaches 2 by
  raising a `WioError` or by argparse, because `wio.cli` turns any other code
  than 0 or 1 that a command returns into 70.
- **The wiring** — of the adapters of the `History` port (the git adapter) and
  the `Contracts` port (the adapter of the contracts component), the no-op
  `EventSink` and the port for the rules of a stage, which `wio.trailers` owns
  and whose null adapter, selecting no rule, is built in `wio.cli`. They are
  built in `wio.cli` and never imported by `wio.trailers`.
- **The help** — `wio trailers --help` lists the three forms and exits 0.

## Acceptance criteria

The examples use a temporary repository whose config declares the gate
`architecture-review`, with `judge = "human"`, and a Work `k3m9xq` that has an
item `AC-1` and a `deliver` that lists `architecture` and `architecture-review`.
`HEAD` carries a record for `k3m9xq`.

### **AC-1** The arguments select the form

#### The write form, check and fold

- **Given** the repository, a commit message file with the subject `feat: add x`
  and no record, and a pull request body. Standard input holds the message for
  the fourth run and the body for the sixth.
- **When** `wio trailers k3m9xq deliver architecture`,
  `wio trailers check <file>`, `wio trailers check --require <file>`,
  `wio trailers check --require -` with the message on standard input,
  `wio trailers fold block HEAD~1..HEAD` and
  `wio trailers fold body HEAD~1..HEAD` run.
- **Then** the first, the fifth and the sixth exit 0 and print the record of
  `k3m9xq`, the folded record of `HEAD` and the body with that record at its end
  in turn, the second exits 0 because a message without a record passes, and
  the third and the fourth exit 1 because it has none.

### **AC-2** A usage mistake exits 2

#### Calls that no form accepts

- **Given** the repository.
- **When** `wio trailers`, `wio trailers fold nosuch`,
  `wio trailers check --nosuch` and the call that starts with the option
  `--items AC-1`, before `k3m9xq deliver architecture`, run.
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

- **Given** the repository, with a work commit under a pure gate commit of
  `architecture-review`, and an empty Wio home.
- **When** `wio trailers k3m9xq deliver architecture-review --result pass
  --judge human` runs.
- **Then** it prints the record, exits 0 and leaves the Wio home empty.

#### A cited rule code with the null rules port

- **Given** the repository, with no injected adapter.
- **When** `wio trailers k3m9xq deliver architecture-review --result pass
  --judge human --cite docs.DOC001=fail` runs.
- **Then** it exits 1, prints an `error:` line that names `docs.DOC001` on
  standard error and prints nothing on standard output.

### **AC-4** The help lists the forms

#### The help text

- **Given** the repository.
- **When** `wio trailers --help` runs.
- **Then** it exits 0 and lists the write form, `check` and `fold`.
