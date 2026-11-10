<!-- wio
id = "zfx8h2"
template = "feature.draft"
roots = []
depends_on = ["1n1p8j", "776g94", "vyjmpc"]
-->

# Checking the templates

## Purpose

A broken template must be caught before a contract follows it.

## Intent

`wio templates check` judges keys (`kind` required; `shape`, `description`
optional; unknown top-level keys are errors), kinds, duplicate names,
directives, `[actions]` references and the `[templates.kinds]` entries.
