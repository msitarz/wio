<!-- wio
id = "zggta5"
template = "feature.leaf"
roots = ["repo"]
depends_on = ["mb4q2g", "d2ytdf"]
-->

# Hooks that run the contracts check

## Purpose

An agent that edits a contract, and a commit that changes one, must be told of a
problem in the project's contracts without anyone running the check. The checks
of the config and of the templates already run this way, and the contracts are
the last of the three.

## Goals

- An agent that edits a contract gets the errors of the check back in the same
  turn.
- A commit that changes a contract is refused while the contracts have an error.
- A hook says nothing when the contracts pass, when only a warning is found, or
  when the edit is not to a contract.

## Non-Goals

- Reporting warnings and notes to the agent. They are one `wio contracts check`
  away, which the define stage's goal tells the agent to run.
- A hook for a harness other than Claude Code, which a project writes with its
  own hook.
- Following a `[works] dir` other than this repository's: the hooks are fixed to
  `.agents/wio/works/`, and a project with another directory gets no hook.
- Folding the checks into one. When `wio check` exists, the three commit hooks
  become one that calls it, and the agent hooks stay.
- Catching a commit that only deletes a Work, because `prek` passes only files
  that exist. The abandon procedure also edits the dependents, which does run
  it.

## Assumptions

- **A-1**: The check-works and check-body leaves are delivered, so
  `wio contracts check` exits 1 on an error and prints the diagnostics.
- **A-2**: Claude Code returns a hook's standard error to the model when the
  hook exits 2, as the config's and the templates' hooks already rely on, and
  the payload carries the edited file as an absolute `tool_input.file_path`, as
  the parent's A-6 says.
- **A-3**: Claude Code runs the hooks of one matcher side by side, so the
  formatter can rewrite a contract while the check reads it, and a line in a
  diagnostic may be stale for that one edit. The next edit corrects it.

## Mechanisms

- The `PostToolUse` entries of `.claude/settings.json`, which hold the
  formatter, the config check and the templates check, and gain a command that
  runs `uv run wio contracts check`. The shape of the command is provisional,
  and its exit codes and its silence are required.
- `jq`, which reads the edited path from the hook's input.
- A hook of `prek.toml`, `wio-contracts`, set beside `wio-templates`, which runs
  `uv run wio contracts check` when a Markdown file of the Works directory is in
  the commit and passes it no file names.
- The helpers of `tests/tooling` that run a hook's command with a fake `uv` and
  tell whether the check was called.

## Constraints

- **The hook reports only a failed check.** It exits 2 with the diagnostics on
  standard error when the check exits 1, and exits 0 with no output when the
  check exits with anything else, including a refusal or a failure to run, and
  when it finds only warnings or notes.
- **The hook runs only for a contract.** The edited path is absolute, ends in
  `.md` and contains `/.agents/wio/works/`, at any depth.
- **The whole tree is checked.** The hook passes no file name to the check,
  because duplicate ids, cycles and dependencies span files.
- **wio knows nothing of the harness.** The hook is the project's, and it calls
  the command the way the other two hooks do.

## Acceptance criteria

### **AC-1** An edit of a contract with an error is reported to the agent

The hook of `.claude/settings.json` exits 2 and prints the check's diagnostics
on standard error when the edited file is a contract and the check fails.

#### A broken contract

- **Given** the hook's command and a fake `uv` that prints the diagnostic
  ``error: .agents/wio/works/a/README.md: The dependency `zzzzzz` is not a Work``
  and exits 1.
- **When** the command receives the `PostToolUse` input for an edit of
  `/repo/.agents/wio/works/a/README.md` and of
  `/repo/.agents/wio/works/a/b/README.md`.
- **Then** each exits 2 with that diagnostic on standard error and nothing on
  standard output, and the fake `uv` was called with `run wio contracts check`.

### **AC-2** Anything else is silent

The hook exits 0 with no output when the contracts pass, when a warning is all
the check finds, and when the edited file is not a contract, and it calls the
check only for a contract.

#### Quiet cases

- **Given** the hook's command and a fake `uv` that prints a diagnostic and
  exits 1.
- **When** the command receives the input for an edit of
  `/repo/src/wio/cli/x.py`, of `/repo/.agents/wio/config.toml`, of
  `/repo/.agents/wio/templates/feature.leaf.md` and of
  `/repo/.agents/wio/works/a/notes.txt`; and then, with a fake `uv` that prints
  `The contracts pass.` and exits 0, and one that prints a warning and exits 0,
  for an edit of `/repo/.agents/wio/works/a/README.md`.
- **Then** each exits 0 with no output, the check was not called for the first
  four, and it was called for the last two.

### **AC-3** A check that cannot run does not block the edit

When `wio contracts check` exits with anything but 1, the hook exits 0 with no
output.

#### A refused check

- **Given** the hook's command and a fake `uv` that exits 2 with a message, and
  one that exits 127.
- **When** the command receives the input for an edit of
  `/repo/.agents/wio/works/a/README.md`.
- **Then** each exits 0 with no output.

### **AC-4** A commit that changes a contract is refused on an error

The `wio-contracts` hook of `prek.toml` runs `uv run wio contracts check` when a
Markdown file of the Works directory is in the commit, takes no file names,
fails and prints the diagnostics on an error, and does not run for a commit with
no contract.

#### The commit hook

- **Given** a temporary git repository with this repository's `prek.toml`, a
  minimal config and the entry template of its kind, and a staged contract at
  `.agents/wio/works/a/README.md` whose `depends_on` names an id that no Work
  has; and then a repository in which only `src/wio/cli/x.py` is staged.
- **When** `prek` runs the hooks on the staged files of each.
- **Then** in the first the `wio-contracts` hook fails and prints the diagnostic
  that names the unknown dependency, and in the second prek's output marks it
  `(no files to check)Skipped`.

## Additional context

- The config's and the templates' hooks are the pattern, and the contracts'
  hooks sit beside them in `.claude/settings.json` and `prek.toml`.
