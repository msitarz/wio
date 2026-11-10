<!-- wio
id = "4tc534"
template = "feature.draft"
roots = []
depends_on = ["zfx8h2"]
-->

# Reporting a broken template at once

## Purpose

An agent that edits a template, and a commit that changes one, must be told of
a problem in the project's templates without anyone running the check.

## Intent

Run `wio templates check` from a `PostToolUse` entry of `.claude/settings.json`
when an agent edits a file in the templates directory, and from a
`wio-templates` hook of `prek.toml` when a commit changes one, as the config's
hooks do, and extend `docs/workflow.md` section 7 to cover both.
