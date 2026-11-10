<!-- wio
id = "4tc534"
template = "feature.leaf"
roots = ["repo"]
depends_on = ["zfx8h2"]
-->

# Reporting a broken template at once

## Purpose

An agent that edits a template, and a commit that changes one, must be told of a
problem in the project's templates without anyone running the check.

## Goals

- An agent that edits a template gets the check's diagnostics back in the same
  turn.
- A commit that changes a template is refused while the templates have an error.
- A hook says nothing when the templates pass or when the edit is not to a
  template.
- The workflow's document says how both hooks run the check, for the config and
  for the templates.

## Non-Goals

- Reporting warnings to the agent.
- A hook for a harness other than Claude Code, which a project writes with its
  own hook.
- Following a `[templates] dir` other than this repository's.

## Assumptions

- **A-1**: The check leaf is delivered, so `wio templates check` exits 1 on an
  error and prints the diagnostics.
- **A-2**: Claude Code returns a hook's standard error to the model when the
  hook exits 2, as the config's hook already relies on; the payload is as the
  parent's A-5 says.

## Mechanisms

- The `PostToolUse` entries of `.claude/settings.json`, which already hold the
  formatter and the config check, and gain a command that runs
  `uv run wio templates check`; the command's shape is provisional, and its exit
  codes and its silence are required.
- `jq`, which reads the edited path from the hook's input.
- A hook of `prek.toml`, `wio-templates`, set beside `wio-config`, which runs
  `uv run wio templates check` when a file of the templates directory is in the
  commit and passes it no file names.
- Section 7 of `docs/workflow.md`, which describes the hooks.

## Constraints

- **The hook reports only a failed check.** It exits 2 with the diagnostics on
  standard error when the check exits 1, and exits 0 with no output otherwise,
  including when the check is refused or cannot run.
- **The hook runs only for a template.** The path is a `.md` file under
  `.agents/wio/templates/`, in any subdirectory.
- **wio knows nothing of the harness.** The hook is the project's, and it calls
  the command the way the config's hook does.
- **Verification.** The agent's hook is verified by AC-1, AC-2 and AC-3, the
  commit hook by AC-4 and the document by AC-5.

## Acceptance criteria

### **AC-1** An edit of a template with an error is reported to the agent

The hook of `.claude/settings.json` exits 2 and prints the check's diagnostics
on standard error when the edited file is a template and the templates have an
error.

#### A broken template

- **Given** the hook's command and a repository whose template
  `.agents/wio/templates/feature.leaf.md` has an unknown key and which also has
  the file `.agents/wio/templates/sub/other.md`.
- **When** the command receives the `PostToolUse` input for an edit of that
  file, and again for an edit of `.agents/wio/templates/sub/other.md`.
- **Then** each exits 2 with the diagnostics on standard error and nothing on
  standard output.

### **AC-2** Anything else is silent

The hook exits 0 with no output when the templates pass, when a warning is all
the check finds, and when the edited file is not a template.

#### Quiet cases

- **Given** the hook's command and a repository whose templates have an error.
- **When** the command receives the input for an edit of `src/wio/cli/x.py`, of
  `.agents/wio/config.toml` and of `.agents/wio/templates/notes.txt`; and then,
  once with templates that have no problem and once with templates whose only
  finding is the repeated-heading warning of the check leaf's AC-7, for an edit
  of a template.
- **Then** each exits 0 with no output, so a passing check's message is not
  printed.

### **AC-3** A check that cannot run does not block the edit

When `wio templates check` exits with anything but 1, the hook exits 0 with no
output.

#### A refused check

- **Given** the hook's command and a repository whose config has an error, so
  that the check exits 2.
- **When** the command receives the input for an edit of a template.
- **Then** it exits 0 with no output.

### **AC-4** A commit that changes a template is refused on an error

The `wio-templates` hook of `prek.toml` runs `uv run wio templates check` when a
file of the templates directory is in the commit, takes no file names, fails and
prints the diagnostics on an error, and does not run for a commit with no
template.

#### The commit hook

- **Given** `prek.toml` and a staged template with an unknown key, and then a
  staged change to `src/wio/cli/x.py` alone.
- **When** `prek` runs the hook on each.
- **Then** the first fails and prints the diagnostics, and the second does not
  run it.

### **AC-5** The workflow's document describes both hooks

Section 7 of `docs/workflow.md` says that the config and the templates are
checked after every edit and before every commit that changes them, shows the
`.claude/settings.json` entry for each, names the `prek` hook for each, and says
that each project decides how its harness runs the checks.

## Additional context

- Section 7 of [the workflow](../../../../../docs/workflow.md), on checking the
  config after every edit, is the section this Work extends to the templates.
- The [check](../check/README.md) leaf is the command the hooks run.
